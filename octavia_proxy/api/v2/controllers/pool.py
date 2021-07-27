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
from pecan import abort as pecan_abort
from pecan import expose as pecan_expose
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.v2.types import pool as pool_types
from octavia_proxy.common import constants
from octavia_proxy.common import exceptions


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PoolsController(base.BaseController):
    RBAC_TYPE = constants.RBAC_POOL

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(pool_types.PoolRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get(self, id, fields=None):
        """Gets a pool's details."""
        context = pecan_request.context.get('octavia_context')

        result = self.find_pool(context, id)

        self._auth_validate_action(context, result.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            result = self._filter_fields([result], fields)[0]
        return pool_types.PoolRootResponse(
            listener=result)

    @wsme_pecan.wsexpose(pool_types.PoolsRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all pools."""
        pcontext = pecan_request.context
        context = pcontext.get('octavia_context')

        query_filter = self._auth_get_all(context, project_id)
        query_params = pcontext.get(constants.PAGINATION_HELPER).params

        # TODO: fix filtering and sorting, especially for multiple providers
        # TODO: if provider is present in query => ...
        # TODO: parallelize drivers querying
        query_filter.update(query_params)

        enabled_providers = CONF.api_settings.enabled_provider_drivers
        result = []
        links = []

        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                pools = driver_utils.call_provider(
                    driver.name, driver.pools,
                    context.session,
                    context.project_id,
                    query_filter)
                if pools:
                    LOG.debug('Received %s from %s' % (pools, driver.name))
                    result.extend(pools)
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

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

        if not pool.project_id and context.project_id:
            pool.project_id = context.project_id

        self._auth_validate_action(
            context, pool.project_id, constants.RBAC_POST)

        driver = driver_factory.get_driver(pool.provider)

        if pool.loadbalancer_id:
            loadbalancer = self.find_load_balancer(
                context, pool.loadbalancer_id)
        elif pool.listener_id:
            listener = self.find_listener(context, pool.listener_id)
            pool.loadbalancer_id = listener.loadbalancer_id
        else:
            msg = _("Must provide at least one of: "
                    "loadbalancer_id, listener_id")
            raise exceptions.ValidationException(detail=msg)


        # check quota


        driver = driver_factory.get_driver(pool.provider)

        obj_dict = pool.to_dict(render_unsets=False)
        obj_dict['id'] = None

        result = driver_utils.call_provider(
            driver.name, driver.pool_create,
            context.session,
            pool)

        orig_listener = self.find_listener(context, result.listeners[0]['id'])
        self._auth_validate_action(
            context, orig_listener.project_id,
            constants.RBAC_PUT)
        lsnr_dict = orig_listener.to_dict(render_unsets=False)
        lsnr_dict['default_pool_id'] = result.id
        listener = driver_utils.call_provider(
            driver.name, driver.listener_update, context.session,
            orig_listener, lsnr_dict)
        # For some API requests the listener_id will be passed in the
        # pool_dict:

    @wsme_pecan.wsexpose(pool_types.PoolRootResponse, wtypes.text,
                         body=pool_types.PoolRootPut, status_code=200)
    def put(self, id, pool_):
        """Updates a pool on a load balancer."""
        pool = pool_.pool
        context = pecan_request.context.get('octavia_context')

        orig_pool = self.find_pool(context, id)

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

        pool = self.find_pool(context, id)

        self._auth_validate_action(
            context, pool.project_id,
            constants.RBAC_DELETE)

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
        pecan_abort(501)
