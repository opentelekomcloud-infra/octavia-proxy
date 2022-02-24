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
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import health_monitor as hm_types
from octavia_proxy.api.common import types
from octavia_proxy.common import constants as const
from octavia_proxy.common import exceptions
from octavia_proxy.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class HealthMonitorController(base.BaseController):
    RBAC_TYPE = const.RBAC_HEALTHMONITOR

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a single healthmonitor's details."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(const.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)

        hm = self.find_health_monitor(context, id, is_parallel)[0]

        self._auth_validate_action(context, hm.project_id,
                                   const.RBAC_GET_ONE)

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
        pagination_helper = pcontext.get(const.PAGINATION_HELPER)

        query_params = pagination_helper.params
        query_filter.update(query_params)

        is_parallel = query_filter.pop('is_parallel', True)
        allow_pagination = CONF.api_settings.allow_pagination

        links = []
        result = driver_invocation(
            context, 'health_monitors', is_parallel, query_filter
        )

        if allow_pagination:
            result_to_dict = [hlth_mntr.to_dict() for hlth_mntr in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, hm_types.HealthMonitorFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)
        return hm_types.HealthMonitorsRootResponse(
            healthmonitors=result, healthmonitors_links=links)

    def _validate_create_hm(self, hm):
        """Validate creating health monitor on pool."""
        mandatory_fields = (const.TYPE, const.DELAY, const.TIMEOUT,
                            const.POOL_ID, const.MAX_RETRIES)
        for field in mandatory_fields:
            if hm.get(field, None) is None:
                raise exceptions.InvalidOption(value='None', option=field)
        http_s_types = (const.HEALTH_MONITOR_HTTP, const.HEALTH_MONITOR_HTTPS)
        if hm[const.TYPE] not in http_s_types:
            if hm.get(const.HTTP_METHOD, None):
                raise exceptions.InvalidOption(
                    value=const.HTTP_METHOD,
                    option='health monitors of '
                           'type {}'.format(hm[const.TYPE]))
            if hm.get(const.URL_PATH, None):
                raise exceptions.InvalidOption(
                    value=const.URL_PATH,
                    option='health monitors of '
                           'type {}'.format(hm[const.TYPE]))
            if hm.get(const.EXPECTED_CODES, None):
                raise exceptions.InvalidOption(
                    value=const.EXPECTED_CODES,
                    option='health monitors of '
                           'type {}'.format(hm[const.TYPE]))
        else:
            if not hm.get(const.HTTP_METHOD, None):
                hm[const.HTTP_METHOD] = (
                    const.HEALTH_MONITOR_HTTP_DEFAULT_METHOD)
            if not hm.get(const.URL_PATH, None):
                hm[const.URL_PATH] = (
                    const.HEALTH_MONITOR_DEFAULT_URL_PATH)
            if not hm.get(const.EXPECTED_CODES, None):
                hm[const.EXPECTED_CODES] = (
                    const.HEALTH_MONITOR_DEFAULT_EXPECTED_CODES)

        if hm.get('domain_name') and not hm.get('http_version'):
            raise exceptions.ValidationException(
                detail=_("'http_version' must be specified when 'domain_name' "
                         "is provided."))

        if hm.get('http_version') and hm.get('domain_name'):
            if hm['http_version'] < 1.1:
                raise exceptions.InvalidOption(
                    value='http_version %s' % hm['http_version'],
                    option='health monitors HTTP 1.1 domain name health check')

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse,
                         body=hm_types.HealthMonitorRootPOST, status_code=201)
    def post(self, health_monitor_):
        """Creates a health monitor on a pool."""
        hm = health_monitor_.healthmonitor
        context = pecan_request.context.get('octavia_context')

        if not hm.project_id and context.project_id:
            hm.project_id = context.project_id

        self._auth_validate_action(
            context, hm.project_id, const.RBAC_POST)

        pool = self.find_pool(context, id=hm.pool_id)[0]

        provider = pool.provider

        if (not CONF.api_settings.allow_ping_health_monitors and
                hm.type == const.HEALTH_MONITOR_PING):
            raise exceptions.DisabledOption(
                option='type', value=const.HEALTH_MONITOR_PING)

        if pool.protocol is const.PROTOCOL_UDP:
            self._validate_healthmonitor_request_for_udp(hm, pool.protocol)
        else:
            if hm.type is const.HEALTH_MONITOR_UDP_CONNECT:
                raise exceptions.ValidationException(
                    detail=_(
                        "The %(type)s type is only supported for pools of type"
                        " %(protocols)s.") % {
                        'type': hm.type,
                        'protocols': '/'.join(const.PROTOCOL_UDP)})

        self._validate_create_hm(hm.to_dict(render_unsets=True))

        driver = driver_factory.get_driver(provider)
        result = driver_utils.call_provider(
            driver.name, driver.health_monitor_create,
            context.session,
            hm)

        return hm_types.HealthMonitorRootResponse(healthmonitor=result)

    def _validate_update_hm(self, hm, health_monitor):
        if hm.type not in (const.HEALTH_MONITOR_HTTP,
                           const.HEALTH_MONITOR_HTTPS):
            if health_monitor.http_method != wtypes.Unset:
                raise exceptions.InvalidOption(
                    value=const.HTTP_METHOD,
                    option='health monitors of '
                           'type {}'.format(hm.type))
            if health_monitor.url_path != wtypes.Unset:
                raise exceptions.InvalidOption(
                    value=const.URL_PATH,
                    option='health monitors of '
                           'type {}'.format(hm.type))
            if health_monitor.expected_codes != wtypes.Unset:
                raise exceptions.InvalidOption(
                    value=const.EXPECTED_CODES,
                    option='health monitors of '
                           'type {}'.format(hm.type))
        if health_monitor.delay is None:
            raise exceptions.InvalidOption(value=None, option=const.DELAY)
        if health_monitor.max_retries is None:
            raise exceptions.InvalidOption(
                value=None, option=const.MAX_RETRIES)
        if health_monitor.timeout is None:
            raise exceptions.InvalidOption(value=None, option=const.TIMEOUT)

        if health_monitor.domain_name and not (
                hm.http_version or health_monitor.http_version):
            raise exceptions.ValidationException(
                detail=_("'http_version' must be specified when 'domain_name' "
                         "is provided."))

        if ((hm.http_version or health_monitor.http_version) and
                (hm.domain_name or health_monitor.domain_name)):
            http_version = health_monitor.http_version or hm.http_version
            if http_version < 1.1:
                raise exceptions.InvalidOption(
                    value='http_version %s' % http_version,
                    option='health monitors HTTP 1.1 domain name health check')

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse, wtypes.text,
                         body=hm_types.HealthMonitorRootPUT, status_code=200)
    def put(self, id, health_monitor_):
        """Updates a health monitor."""
        healthmonitor = health_monitor_.healthmonitor
        context = pecan_request.context.get('octavia_context')

        orig_hm = self.find_health_monitor(context, id)[0]

        self._auth_validate_action(
            context, orig_hm.project_id,
            const.RBAC_PUT)

        self._validate_update_hm(orig_hm, healthmonitor)
        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(orig_hm.provider)

        # Prepare the data for the driver data model
        hm_dict = healthmonitor.to_dict(render_unsets=False)

        result = driver_utils.call_provider(
            driver.name, driver.health_monitor_update,
            context.session,
            orig_hm, hm_dict)

        return hm_types.HealthMonitorRootResponse(healthmonitor=result)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a health monitor."""
        context = pecan_request.context.get('octavia_context')

        hm = self.find_health_monitor(context, id)[0]

        self._auth_validate_action(
            context, hm.project_id,
            const.RBAC_DELETE)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(hm.provider)

        driver_utils.call_provider(
            driver.name, driver.health_monitor_delete,
            context.session, hm)

    def _graph_create(self, session, lb, hm_dict, provider=None):
        driver = driver_factory.get_driver(provider)
        hm_response = driver_utils.call_provider(
            driver.name, driver.health_monitor_create,
            session, hm_dict)
        if not hm_response:
            context = pecan_request.context.get('octavia_context')
            driver_utils.call_provider(
                driver.name, driver.loadbalancer_delete,
                context.session,
                lb, cascade=True)
            raise Exception("Healthmonitor creation failed")
        hm_full_response = hm_response.to_full_response()
        return hm_full_response
