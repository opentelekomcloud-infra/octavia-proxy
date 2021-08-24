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
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import health_monitor as hm_types
from octavia_proxy.common import constants
from octavia_proxy.common import exceptions
from octavia_proxy.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class HealthMonitorController(base.BaseController):
    RBAC_TYPE = constants.RBAC_HEALTHMONITOR

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a single healthmonitor's details."""
        context = pecan_request.context.get('octavia_context')
        hm = self.find_healthmonitor(context, id)
        self._auth_validate_action(context, hm.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            hm = self._filter_fields([hm], fields)[0]
        return hm_types.HealthMonitorRootResponse(healthmonitor=hm)

    @wsme_pecan.wsexpose(hm_types.HealthMonitorsRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Gets all health monitors."""
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
                hms = driver_utils.call_provider(
                    driver.name, driver.healthmonitors,
                    context.session,
                    context.project_id,
                    query_filter)
                if hms:
                    LOG.debug('Received %s from %s' % (hms, driver.name))
                    result.extend(hms)
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

        if fields is not None:
            result = self._filter_fields(result, fields)
        return hm_types.HealthMonitorsRootResponse(
            healthmonitors=result, pools_links=links)

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse,
                         body=hm_types.HealthMonitorRootPOST, status_code=201)
    def post(self, health_monitor_):
        """Creates a health monitor on a pool."""
        hm = health_monitor_.healthmonitor
        context = pecan_request.context.get('octavia_context')
        loadbalancer = None

        if not hm.project_id and context.project_id:
            hm.project_id = context.project_id

        self._auth_validate_action(
            context, hm.project_id, constants.RBAC_POST)

        pool = self.find_pool(context, id=hm.pool_id)

        if pool.loadbalancers:
            loadbalancer = self.find_load_balancer(
                context, pool.loadbalancers[0].id)
        elif pool.listeners:
            loadbalancer = self.find_load_balancer(
                context, pool.listeners[0].id)

        if (not CONF.api_settings.allow_ping_health_monitors and
                hm.type == constants.HEALTH_MONITOR_PING):
            raise exceptions.DisabledOption(
                option='type', value=constants.HEALTH_MONITOR_PING)

        if pool.protocol is constants.PROTOCOL_UDP:
            self._validate_healthmonitor_request_for_udp(hm, pool.protocol)
        else:
            if hm.type is constants.HEALTH_MONITOR_UDP_CONNECT:
                raise exceptions.ValidationException(detail=_(
                    "The %(type)s type is only supported for pools of type "
                    "%(protocols)s.") % {
                        'type': hm.type,
                        'protocols': '/'.join(constants.PROTOCOL_UDP)})

        driver = driver_factory.get_driver(loadbalancer.provider)
        result = driver_utils.call_provider(
            driver.name, driver.healthmonitor_create,
            context.session,
            hm)

        return hm_types.HealthMonitorRootResponse(healthmonitor=result)

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse, wtypes.text,
                         body=hm_types.HealthMonitorRootPUT, status_code=200)
    def put(self, id, health_monitor_):
        """Updates a health monitor."""
        healthmonitor = health_monitor_.healthmonitor
        context = pecan_request.context.get('octavia_context')

        orig_hm = self.find_healthmonitor(context, id)

        self._auth_validate_action(
            context, orig_hm.project_id,
            constants.RBAC_PUT)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(orig_hm.provider)

        # Prepare the data for the driver data model
        hm_dict = healthmonitor.to_dict(render_unsets=False)

        result = driver_utils.call_provider(
            driver.name, driver.healthmonitor_update,
            context.session,
            orig_hm, hm_dict)

        return hm_types.HealthMonitorRootResponse(healthmonitor=result)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a health monitor."""
        pecan_abort(501)
