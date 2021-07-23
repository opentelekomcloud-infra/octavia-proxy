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
from octavia_lib.api.drivers import data_models as driver_dm
from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import strutils
from pecan import expose as pecan_expose
from pecan import request as pecan_request
from pecan import abort as pecan_abort
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.common import constants
from octavia_proxy.common import exceptions

from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.drivers import driver_factory

from octavia_proxy.api.v2.types import load_balancer as lb_types
from octavia_proxy.api.v2.controllers import base


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
        context = pecan_request.context.get('octavia_context')

        result = self.find_load_balancer(context, id)

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
        query_params = pcontext.get(constants.PAGINATION_HELPER).params

        # TODO: fix filtering and sorting, especially for multiple providers
        # TODO: if provider is present in query => ...
        # TODO: parallelize drivers querying
        if 'vip_port_id' in query_params:
            query_filter['vip_port_id'] = query_params['vip_port_id']

        enabled_providers = CONF.api_settings.enabled_provider_drivers
        result = []
        links = []
        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                lbs = driver_utils.call_provider(
                    driver.name, driver.loadbalancers,
                    context.session,
                    context.project_id,
                    query_filter)
                if lbs:
                    LOG.debug('Received %s from %s' % (lbs, driver.name))
                    result.extend(lbs)
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

        # TODO: pagination
        if fields is not None:
            result = self._filter_fields(result, fields)
        return lb_types.LoadBalancersRootResponse(
            loadbalancers=result, loadbalancers_links=links)

    def _get_provider(self, session, load_balancer):
        """Decide on the provider for this load balancer."""

        provider = None
        if not isinstance(load_balancer.flavor_id, wtypes.UnsetType):
            try:
                provider = self.repositories.flavor.get_flavor_provider(
                    session, load_balancer.flavor_id)
            except Exception as e:
                raise exceptions.ValidationException(
                    detail=("Invalid flavor_id.")) from e

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

    @wsme_pecan.wsexpose(lb_types.LoadBalancerFullRootResponse,
                         body=lb_types.LoadBalancerRootPOST, status_code=201)
    def post(self, load_balancer):
        """Creates a load balancer."""
        load_balancer = load_balancer.loadbalancer
        context = pecan_request.context.get('octavia_context')

        if not load_balancer.project_id and context.project_id:
            load_balancer.project_id = context.project_id

        if not load_balancer.project_id:
            raise exceptions.ValidationException(detail=(
                "Missing project ID in request where one is required. "
                "An administrator should check the keystone settings "
                "in the Octavia configuration."))

        self._auth_validate_action(context, load_balancer.project_id,
                                   constants.RBAC_POST)

        provider = self._get_provider(context.session, load_balancer)

        # TODO(gtema): implement complex create

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(provider)

        lb_dict = load_balancer.to_dict(render_unsets=False)
        lb_dict['id'] = None
        driver_lb_dict = driver_utils.lb_dict_to_provider_dict(
            lb_dict, None, None, None)

        # Dispatch to the driver
        result = driver_utils.call_provider(
            driver.name, driver.loadbalancer_create,
            context.session,
            driver_dm.LoadBalancer.from_dict(driver_lb_dict))

        return lb_types.LoadBalancerRootResponse(loadbalancer=result)

    @wsme_pecan.wsexpose(lb_types.LoadBalancerRootResponse,
                         wtypes.text, status_code=200,
                         body=lb_types.LoadBalancerRootPUT)
    def put(self, id, load_balancer):
        """Updates a load balancer."""
        load_balancer = load_balancer.loadbalancer
        context = pecan_request.context.get('octavia_context')

        orig_balancer = self.find_load_balancer(context, id)

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

        load_balancer = self.find_load_balancer(context, id)

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
