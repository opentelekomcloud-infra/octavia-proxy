#  Copyright 2021 Open Telekom Cloud, T-Systems International
#  Copyright 2014 Rackspace
#  Copyright 2016 Blue Box, an IBM Company
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import strutils
from pecan import abort as pecan_abort
from pecan import expose as pecan_expose
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from openstack import exceptions as openstack_exceptions
from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import (base, pool as pool_controller,
                                              listener as li_controller)
from octavia_proxy.api.v2.types import load_balancer as lb_types
from octavia_proxy.api.common import types
from octavia_proxy.common import constants, validate
from octavia_proxy.common import exceptions
from octavia_proxy.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class LoadBalancersController(base.BaseController):
    RBAC_TYPE = constants.RBAC_LOADBALANCER

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(lb_types.LoadBalancerRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a single load balancer's details."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)

        result = self.find_load_balancer(context, id, is_parallel)[0]

        self._auth_validate_action(context, result.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            result = self._filter_fields([result], fields)[0]
        return lb_types.LoadBalancerRootResponse(loadbalancer=result)

    @wsme_pecan.wsexpose(lb_types.LoadBalancersRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all load balancers."""
        pcontext = pecan_request.context
        context = pcontext.get('octavia_context')

        query_filter = self._auth_get_all(context, project_id)
        # Get pagination helper
        pagination_helper = pcontext.get(constants.PAGINATION_HELPER)
        query_params = pagination_helper.params

        # TODO: fix filtering and sorting, especially for multiple providers
        if 'vip_port_id' in query_params:
            query_filter['vip_port_id'] = query_params['vip_port_id']

        query_filter.update(query_params)

        is_parallel = query_filter.pop('is_parallel', True)
        allow_pagination = CONF.api_settings.allow_pagination

        links = []
        result = driver_invocation(
            context, 'loadbalancers', is_parallel, query_filter
        )

        if allow_pagination:
            result_to_dict = [lb_obj.to_dict() for lb_obj in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, lb_types.LoadBalancerFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)
        return lb_types.LoadBalancersRootResponse(
            loadbalancers=result, loadbalancers_links=links)

    def _get_provider(self, session, load_balancer):
        """Decide on the provider for this load balancer."""

        provider = None

        # No provider specified and no flavor specified, use conf default
        if (isinstance(load_balancer.provider, wtypes.UnsetType) and
                not provider):
            provider = CONF.api_settings.default_provider_driver
        # Both provider and flavor specified, they must match
        elif (not isinstance(load_balancer.provider, wtypes.UnsetType) and
              provider):
            if provider != load_balancer.provider:
                raise exceptions.ProviderFlavorMismatchError(
                    flav=load_balancer.flavor_id, prov=load_balancer.provider)
        # No flavor, but provider, use the provider specified
        elif not provider:
            provider = load_balancer.provider
        # Otherwise, use the flavor provider we found above

        return provider

    @staticmethod
    def _validate_network_and_fill_or_validate_subnet(load_balancer,
                                                      context=None):
        network = validate.network_exists_optionally_contains_subnet(
            network_id=load_balancer.vip_network_id,
            subnet_id=load_balancer.vip_subnet_id,
            context=context)
        if not load_balancer.vip_subnet_id:
            if load_balancer.vip_address:
                for subnet_id in network.subnet_ids:
                    subnet = context.session.get_subnet(subnet_id)
                    if validate.is_ip_member_of_cidr(load_balancer.vip_address,
                                                     subnet.cidr):
                        load_balancer.vip_subnet_id = subnet_id
                        break
                if not load_balancer.vip_subnet_id:
                    raise exceptions.ValidationException(detail=_(
                        "Supplied network does not contain a subnet for "
                        "VIP address specified."
                    ))
            else:
                # If subnet and IP are not provided, pick the first subnet with
                # enough available IPs, preferring ipv4
                if not network.subnet_ids:
                    raise exceptions.ValidationException(detail=_(
                        "Supplied network does not contain a subnet."
                    ))
                for subnet_id in network.subnet_ids:
                    # Use the first subnet, in case there are no ipv4 subnets
                    if not load_balancer.vip_subnet_id:
                        load_balancer.vip_subnet_id = subnet_id
                    subnet = context.session.get_subnet(subnet_id)
                    if subnet.ip_version == 4:
                        load_balancer.vip_subnet_id = subnet_id
                        break

    def _validate_vip_request_object(self, load_balancer, context=None):
        allowed_network_objects = []
        if CONF.networking.allow_vip_network_id:
            allowed_network_objects.append('vip_network_id')
        if CONF.networking.allow_vip_subnet_id:
            allowed_network_objects.append('vip_subnet_id')

        msg = _("use of %(object)s is disallowed by this deployment's "
                "configuration.")
        if (load_balancer.vip_network_id and
                not CONF.networking.allow_vip_network_id):
            raise exceptions.ValidationException(
                detail=msg % {'object': 'vip_network_id'})
        if (load_balancer.vip_subnet_id and
                not CONF.networking.allow_vip_subnet_id):
            raise exceptions.ValidationException(
                detail=msg % {'object': 'vip_subnet_id'})
        if not (load_balancer.vip_network_id or
                load_balancer.vip_subnet_id):
            raise exceptions.VIPValidationException(
                objects=', '.join(allowed_network_objects))
        # Validate the network id (and subnet if provided)
        elif load_balancer.vip_network_id:
            self._validate_network_and_fill_or_validate_subnet(
                load_balancer,
                context=context)
        # Validate just the subnet id
        elif load_balancer.vip_subnet_id:
            subnet = validate.subnet_exists(
                subnet_id=load_balancer.vip_subnet_id, context=context)
            load_balancer.vip_network_id = subnet.network_id

    @wsme_pecan.wsexpose(lb_types.LoadBalancerFullRootResponse,
                         body=lb_types.LoadBalancerRootPOST, status_code=201)
    def post(self, load_balancer):
        """Creates a load balancer."""
        load_balancer = load_balancer.loadbalancer
        context = pecan_request.context.get('octavia_context')

        if not load_balancer.project_id and context.project_id:
            load_balancer.project_id = context.project_id
        elif not context.project_id:
            load_balancer.project_id = context.session.current_project.id
        if not load_balancer.project_id:
            raise exceptions.ValidationException(detail=(
                "Missing project ID in request where one is required. "
                "An administrator should check the keystone settings "
                "in the Octavia configuration."))

        self._auth_validate_action(context, load_balancer.project_id,
                                   constants.RBAC_POST)

        provider = self._get_provider(context.session, load_balancer)
        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(provider)

        self._validate_vip_request_object(load_balancer, context=context)
        self._validate_flavor(driver, load_balancer, context=context)
        self._validate_availability_zone(context.session, load_balancer)
        lb_response = None
        # Dispatch to the driver
        try:
            lb_response = driver_utils.call_provider(
                driver.name, driver.loadbalancer_create,
                context.session,
                load_balancer)
        except openstack_exceptions.ConflictException:
            raise exceptions.IPAddressInUse(
                network_id=load_balancer.vip_network_id,
                vip_address=load_balancer.vip_address)
        except Exception as e:
            raise e

        pools = None
        listeners = None
        if load_balancer.pools or load_balancer.listeners:
            pools = load_balancer.pools
            listeners = load_balancer.listeners
            pools, listeners = self._graph_create(
                context.session, lb_response, pools, listeners)
        lb_full_response = lb_response.to_full_response(pools=pools,
                                                        listeners=listeners)

        return lb_types.LoadBalancerRootResponse(loadbalancer=lb_full_response)

    @wsme_pecan.wsexpose(lb_types.LoadBalancerRootResponse,
                         wtypes.text, status_code=200,
                         body=lb_types.LoadBalancerRootPUT)
    def put(self, id, load_balancer):
        """Updates a load balancer."""
        load_balancer = load_balancer.loadbalancer
        context = pecan_request.context.get('octavia_context')
        orig_balancer = self.find_load_balancer(context, id)[0]
        self._auth_validate_action(
            context, orig_balancer.project_id,
            constants.RBAC_PUT)
        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(orig_balancer.provider)

        # Prepare the data for the driver data model
        lb_dict = load_balancer.to_dict(render_unsets=False)

        result = driver_utils.call_provider(
            driver.name, driver.loadbalancer_update,
            context.session,
            orig_balancer, lb_dict)

        return lb_types.LoadBalancerRootResponse(loadbalancer=result)

    @wsme_pecan.wsexpose(None, wtypes.text, wtypes.text, status_code=204)
    def delete(self, id, cascade=False):
        """Deletes a load balancer."""
        context = pecan_request.context.get('octavia_context')
        cascade = strutils.bool_from_string(cascade)
        load_balancer = self.find_load_balancer(context, id)[0]

        self._auth_validate_action(
            context, load_balancer.project_id,
            constants.RBAC_DELETE)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(load_balancer.provider)

        driver_utils.call_provider(
            driver.name, driver.loadbalancer_delete,
            context.session,
            load_balancer, cascade)

    @pecan_expose()
    def _lookup(self, id, *remainder):
        """Overridden pecan _lookup method for custom routing.

        Currently it checks if this was a status request and routes
        the request to the StatusController.

        'statuses' is aliased here for backward compatibility with
        neutron-lbaas LBaaS v2 API.
        """
        is_children = (
            id and remainder and (
                remainder[0] == 'status' or remainder[0] == 'statuses' or (
                    remainder[0] == 'stats' or remainder[0] == 'failover'
                )
            )
        )
        # NOTE(gtema): currently not exposing any sub stuff
        if is_children:
            controller = remainder[0]
            remainder = remainder[1:]
            if controller in ('status', 'statuses'):
                pecan_abort(501)
            if controller == 'stats':
                pecan_abort(501)
            if controller == 'failover':
                pecan_abort(501)
        return None

    def _validate_flavor(self, driver, load_balancer, context):
        pass

    def _validate_availability_zone(self, session, load_balancer):
        pass

    def _graph_create(self, session, lb, pools, listeners):
        result_pools = []
        result_listeners = []
        pool_name_ids = {}
        if pools is None:
            pools = []
        if listeners is None:
            listeners = []

        if listeners:
            for li in listeners:
                default_pool = li.default_pool
                if not isinstance(default_pool, wtypes.UnsetType):
                    if not default_pool.name:
                        raise exceptions.ValidationException(
                            detail='Pools must be named when creating a fully '
                                   'populated loadbalancer.')
                    pools.append(default_pool)

        pool_names = []
        for pool in pools:
            if not pool.protocol or not pool.lb_algorithm:
                raise exceptions.ValidationException(
                    detail="'protocol' or 'lb_algorithm' is missing for pool")
            pool_names.append(pool.name)
        if len(pool_names) != len(set(pool_names)):
            raise exceptions.ValidationException(
                detail="Pool names must be unique when creating a fully "
                       "populated loadbalancer.")

        for p in pools:
            members = p.members
            pool_post = p.to_pool_post(loadbalancer_id=lb.id,
                                       project_id=lb.project_id)

            new_pool = (pool_controller.PoolsController()._graph_create(
                session, lb, pool_post, members=members,
                provider=lb.provider))
            result_pools.append(new_pool)
            pool_name_ids[new_pool.name] = new_pool.id

        if listeners:
            for li in listeners:
                if li.default_pool:
                    name = li.default_pool.name
                    listener_post = li.to_listener_post(
                        project_id=lb.project_id, loadbalancer_id=lb.id,
                        default_pool_id=pool_name_ids[name])
                else:
                    listener_post = li.to_listener_post(
                        project_id=lb.project_id, loadbalancer_id=lb.id)

                result_listener = li_controller.ListenersController()\
                    ._graph_create(session, lb, listener_post,
                                   pool_name_ids=pool_name_ids,
                                   provider=lb.provider)
                result_listeners.append(result_listener)
        return result_pools, result_listeners
