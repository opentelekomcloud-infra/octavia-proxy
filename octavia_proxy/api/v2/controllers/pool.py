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

from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base
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
    def get_one(self, id, fields=None):
        """Gets a pool's details."""
        context = pecan_request.context.get('octavia_context')
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        pool = None
        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                pool = driver_utils.call_provider(
                    driver.name, driver.pool_get,
                    context.session,
                    context.project_id,
                    id)
                if pool:
                    setattr(pool, 'provider', provider)
                    break
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

        if not pool:
            raise exceptions.NotFound(
                resource='Pool',
                id=id)

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
        query_params = pcontext.get(constants.PAGINATION_HELPER).params

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
        pecan_abort(501)
        # For some API requests the listener_id will be passed in the
        # pool_dict:

    @wsme_pecan.wsexpose(pool_types.PoolRootResponse, wtypes.text,
                         body=pool_types.PoolRootPut, status_code=200)
    def put(self, id, pool_):
        """Updates a pool on a load balancer."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a pool from a load balancer."""
        context = pecan_request.context.get('octavia_context')
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        pool = None

        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                pool = driver_utils.call_provider(
                    driver.name, driver.pool_get,
                    context.session,
                    context.project_id,
                    id)
                if pool:
                    setattr(pool, 'provider', provider)
                    if pool.healthmonitor_id:
                        hm = driver_utils.call_provider(
                            driver.name, driver.health_monitor_get,
                            context.session,
                            context.project_id,
                            pool.healthmonitor_id)
                        driver_utils.call_provider(
                            driver.name, driver.health_monitor_delete,
                            context.session,
                            hm)
                    break
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')
        if not pool:
            raise exceptions.NotFound(
                resource='pool',
                id=id)
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
        return None
