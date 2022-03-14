#    Copyright 2014 Rackspace
#    Copyright 2016 Blue Box, an IBM Company
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg
from oslo_log import log as logging
from pecan import expose as pecan_expose
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base, member, health_monitor
from octavia_proxy.api.v2.types import pool as pool_types
from octavia_proxy.api.common import types
from octavia_proxy.common import constants, validate, exceptions
from octavia_proxy.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PoolsController(base.BaseController):
    RBAC_TYPE = constants.RBAC_POOL

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(pool_types.PoolRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a pool's details."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)

        pool = self.find_pool(context, id, is_parallel)[0]
        self._auth_validate_action(context, pool.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            pool = self._filter_fields([pool], fields)[0]
        return pool_types.PoolRootResponse(pool=pool)

    @wsme_pecan.wsexpose(pool_types.PoolsRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all pools."""
        pcontext = pecan_request.context
        context = pcontext.get('octavia_context')

        query_filter = self._auth_get_all(context, project_id)
        pagination_helper = pcontext.get(constants.PAGINATION_HELPER)

        query_params = pagination_helper.params
        query_filter.update(query_params)

        is_parallel = query_filter.pop('is_parallel', True)
        allow_pagination = CONF.api_settings.allow_pagination

        links = []
        result = driver_invocation(
            context, 'pools', is_parallel, query_filter
        )

        if allow_pagination:
            result_to_dict = [pl_obj.to_dict() for pl_obj in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, pool_types.PoolFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)
        return pool_types.PoolsRootResponse(
            pools=result, pools_links=links)

    @wsme_pecan.wsexpose(pool_types.PoolRootResponse,
                         body=pool_types.PoolRootPOST, status_code=201)
    def post(self, pool_):
        """Creates a pool on a load balancer or listener.

        Note that this can optionally take a listener_id with which the pool
        should be associated as the listener's default_pool. If specified,
        the pool creation will fail if the listener specified already has
        a default_pool.
        """

        pool = pool_.pool
        context = pecan_request.context.get('octavia_context')
        listener = None
        loadbalancer = None

        if not pool.project_id and context.project_id:
            pool.project_id = context.project_id

        self._auth_validate_action(
            context, pool.project_id, constants.RBAC_POST)
        if pool.loadbalancer_id:
            loadbalancer = self.find_load_balancer(
                context, pool.loadbalancer_id)[0]
            pool.loadbalancer_id = loadbalancer.id
        elif pool.listener_id:
            listener = self.find_listener(context, pool.listener_id)[0]
            loadbalancer = self.find_load_balancer(
                context, listener.loadbalancers[0].id)[0]
            pool.loadbalancer_id = listener.loadbalancers[0].id
        else:
            msg = _("Must provide at least one of: "
                    "loadbalancer_id, listener_id")
            raise exceptions.ValidationException(detail=msg)

        if pool.listener_id and listener:
            self._validate_protocol(listener.protocol, pool.protocol)

        if pool.protocol in constants.PROTOCOL_UDP:
            self._validate_pool_request_for_tcp_udp(pool)

        if pool.session_persistence:
            sp_dict = pool.session_persistence.to_dict(render_unsets=False)
            validate.check_session_persistence(sp_dict)

        driver = driver_factory.get_driver(loadbalancer.provider)

        pool_dict = pool.to_dict(render_unsets=False)
        pool_dict['id'] = None

        if listener and listener.default_pool_id:
            raise exceptions.DuplicatePoolEntry()

        result = driver_utils.call_provider(
            driver.name, driver.pool_create,
            context.session,
            pool)

        return pool_types.PoolRootResponse(pool=result)

    @wsme_pecan.wsexpose(pool_types.PoolRootResponse, wtypes.text,
                         body=pool_types.PoolRootPut, status_code=200)
    def put(self, id, pool_):
        """Updates a pool on a load balancer."""
        pool = pool_.pool
        context = pecan_request.context.get('octavia_context')

        orig_pool = self.find_pool(context, id)[0]

        self._auth_validate_action(
            context, orig_pool.project_id,
            constants.RBAC_PUT)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(orig_pool.provider)

        # Prepare the data for the driver data model
        pool_dict = pool.to_dict(render_unsets=False)

        result = driver_utils.call_provider(
            driver.name, driver.pool_update,
            context.session,
            orig_pool, pool_dict)

        return pool_types.PoolRootResponse(pool=result)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a pool from a load balancer."""
        context = pecan_request.context.get('octavia_context')

        pool = self.find_pool(context, id)[0]

        self._auth_validate_action(
            context, pool.project_id,
            constants.RBAC_DELETE)

        if pool.healthmonitor_id:
            raise exceptions.PoolInUseByHealthCheck(
                id=pool.id, healthmonitor_id=pool.healthmonitor_id)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(pool.provider)

        driver_utils.call_provider(
            driver.name, driver.pool_delete,
            context.session,
            pool)

    @pecan_expose()
    def _lookup(self, pool_id, *remainder):
        """Overridden pecan _lookup method for custom routing.

        Verifies that the pool passed in the url exists, and if so decides
        which controller, if any, should control be passed.
        """
        context = pecan_request.context.get('octavia_context')
        if pool_id and remainder and remainder[0] == 'members':
            remainder = remainder[1:]
            pool = self.find_pool(context, pool_id)[0]
            if not pool:
                LOG.info("Pool %s not found.", pool_id)
                raise exceptions.NotFound(
                    resource='pool',
                    id=pool_id)
            if remainder:
                return member.MemberController(pool_id=pool.id), remainder
            return member.MembersController(pool_id=pool.id), remainder
        return None

    def _graph_create(self, session, lb, pool, hm=None, members=None,
                      provider=None):
        if not hm:
            hm = pool.healthmonitor
        if not members:
            members = pool.members

        driver = driver_factory.get_driver(provider)

        if pool.protocol in constants.PROTOCOL_UDP:
            self._validate_pool_request_for_tcp_udp(pool)

        if pool.session_persistence:
            sp_dict = pool.session_persistence.to_dict(render_unsets=False)
            validate.check_session_persistence(sp_dict)

        result_pool = driver_utils.call_provider(
            driver.name, driver.pool_create,
            session, pool)
        if not result_pool:
            context = pecan_request.context.get('octavia_context')
            driver_utils.call_provider(
                driver.name, driver.loadbalancer_delete,
                context.session,
                lb, cascade=True)
            raise Exception('Pool {pool} creation failed'.format(
                pool=pool.name))

        new_hm = None
        if hm:
            if not hm.delay or not hm.type:
                raise exceptions.ValidationException(
                    detail="Mandatory parameter is missing for healthmonitor.")

            if result_pool.protocol in (constants.PROTOCOL_UDP):
                health_monitor.HealthMonitorController(
                )._validate_healthmonitor_request_for_udp(
                    hm, result_pool.protocol)
            else:
                if hm.type in (constants.HEALTH_MONITOR_UDP_CONNECT):
                    raise exceptions.ValidationException(detail=_(
                        "The %(type)s type is only supported for pools of "
                        "type %(protocol)s.") % {
                            'type': hm.type,
                            'protocol': '/'.join((constants.PROTOCOL_UDP))})

            hm_post = hm.to_hm_post(pool_id=result_pool.id,
                                    project_id=result_pool.project_id)
            new_hm = health_monitor.HealthMonitorController()._graph_create(
                session, lb=lb, hm_dict=hm_post, provider=result_pool.provider)

        # Now create members
        new_members = []
        if members:
            for m in members:
                member_post = m.to_member_post(
                    project_id=result_pool.project_id)
                new_member = member.MembersController(result_pool.id)\
                    ._graph_create(session, lb, member_post,
                                   provider=result_pool.provider)
                new_members.append(new_member)
        full_response_pool = result_pool.to_full_response(members=new_members,
                                                          healthmonitor=new_hm)
        return full_response_pool
