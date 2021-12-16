#    Copyright 2014 Rackspace
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
from dateutil import parser
from wsme import types as wtypes

from octavia_proxy.api.common import types
from octavia_proxy.common import constants


class BaseHealthMonitorType(types.BaseType):
    _type_to_model_map = {}
    _child_map = {}


class HealthMonitorResponse(BaseHealthMonitorType):
    """Defines which attributes are to be shown on any response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    type = wtypes.wsattr(wtypes.text)
    delay = wtypes.wsattr(wtypes.IntegerType())
    timeout = wtypes.wsattr(wtypes.IntegerType())
    max_retries = wtypes.wsattr(wtypes.IntegerType())
    max_retries_down = wtypes.wsattr(wtypes.IntegerType())
    http_method = wtypes.wsattr(wtypes.text)
    url_path = wtypes.wsattr(wtypes.text)
    expected_codes = wtypes.wsattr(wtypes.text)
    admin_state_up = wtypes.wsattr(bool)
    project_id = wtypes.wsattr(wtypes.StringType())
    pools = wtypes.wsattr([types.IdOnlyType])
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    created_at = wtypes.wsattr(wtypes.datetime.datetime)
    updated_at = wtypes.wsattr(wtypes.datetime.datetime)
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType()))
    http_version = wtypes.wsattr(float)
    domain_name = wtypes.wsattr(wtypes.StringType())

    @classmethod
    def from_sdk_object(cls, sdk_entity):
        monitor = cls()
        for key in [
            'id', 'name',
            'type', 'delay', 'timeout', 'max_retries', 'max_retries_down',
            'http_method', 'url_path', 'expected_codes', 'project_id',
            'provisioning_status', 'operating_status',
            'tags',
            'http_version', 'domain_name',
        ]:
            v = sdk_entity.get(key)
            if v:
                setattr(monitor, key, v)

        monitor.admin_state_up = sdk_entity.is_admin_state_up
        for attr in ['created_at', 'updated_at']:
            v = sdk_entity.get(attr)
            if v:
                setattr(monitor, attr, parser.parse(v) or None)
        if sdk_entity.pools:
            monitor.pools = [
                types.IdOnlyType(id=i['id']) for i in sdk_entity.pools
            ]
        return monitor

    @classmethod
    def from_data_model(cls, data_model, children=False):
        pools = data_model.get('pools', [])
        data_model['pools'] = []
        healthmonitor = super(HealthMonitorResponse, cls).from_data_model(
            data_model, children=children)

        if cls._full_response():
            del healthmonitor.pools
        else:
            healthmonitor.pools = [
                types.IdOnlyType.from_data_model(i) for i in pools]
        return healthmonitor

    def to_full_response(self):
        full_response = HealthMonitorFullResponse()

        for key in [
            'id', 'name',
            'type', 'delay', 'timeout', 'max_retries', 'max_retries_down',
            'http_method', 'url_path', 'expected_codes', 'project_id',
            'provisioning_status', 'operating_status',
            'tags',
            'http_version', 'domain_name',
        ]:
            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(full_response, key, v)

        full_response.admin_state_up = self.admin_state_up
        full_response.url_path = self.url_path
        full_response.pools = self.pools
        full_response.created_at = self.created_at
        full_response.updated_at = self.updated_at

        return full_response


class HealthMonitorFullResponse(HealthMonitorResponse):
    @classmethod
    def _full_response(cls):
        return True


class HealthMonitorRootResponse(types.BaseType):
    healthmonitor = wtypes.wsattr(HealthMonitorResponse)


class HealthMonitorsRootResponse(types.BaseType):
    healthmonitors = wtypes.wsattr([HealthMonitorResponse])
    healthmonitors_links = wtypes.wsattr([types.PageType])


class HealthMonitorPOST(BaseHealthMonitorType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    type = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_HEALTH_MONITOR_TYPES),
        mandatory=True)
    delay = wtypes.wsattr(wtypes.IntegerType(minimum=0), mandatory=True)
    timeout = wtypes.wsattr(wtypes.IntegerType(minimum=0), mandatory=True)
    max_retries_down = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_HM_RETRIES,
                           maximum=constants.MAX_HM_RETRIES),
        default=constants.DEFAULT_MAX_RETRIES_DOWN)
    max_retries = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_HM_RETRIES,
                           maximum=constants.MAX_HM_RETRIES),
        mandatory=True)
    http_method = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_HEALTH_MONITOR_HTTP_METHODS))
    url_path = wtypes.wsattr(
        types.URLPathType())
    expected_codes = wtypes.wsattr(
        wtypes.StringType(pattern=r'^(\d{3}(\s*,\s*\d{3})*)$|^(\d{3}-\d{3})$'))
    admin_state_up = wtypes.wsattr(bool, default=True)
    # TODO(johnsom) Remove after deprecation (R series)
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    pool_id = wtypes.wsattr(wtypes.UuidType(), mandatory=True)
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    http_version = wtypes.wsattr(
        wtypes.Enum(float, *constants.SUPPORTED_HTTP_VERSIONS))
    domain_name = wtypes.wsattr(
        wtypes.StringType(min_length=1, max_length=255,
                          pattern=constants.DOMAIN_NAME_REGEX))


class HealthMonitorRootPOST(types.BaseType):
    healthmonitor = wtypes.wsattr(HealthMonitorPOST)


class HealthMonitorPUT(BaseHealthMonitorType):
    """Defines attributes that are acceptable of a PUT request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    delay = wtypes.wsattr(wtypes.IntegerType(minimum=0))
    timeout = wtypes.wsattr(wtypes.IntegerType(minimum=0))
    max_retries_down = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_HM_RETRIES,
                           maximum=constants.MAX_HM_RETRIES))
    max_retries = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_HM_RETRIES,
                           maximum=constants.MAX_HM_RETRIES))
    http_method = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_HEALTH_MONITOR_HTTP_METHODS))
    url_path = wtypes.wsattr(types.URLPathType())
    expected_codes = wtypes.wsattr(
        wtypes.StringType(pattern=r'^(\d{3}(\s*,\s*\d{3})*)$|^(\d{3}-\d{3})$'))
    admin_state_up = wtypes.wsattr(bool)
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    http_version = wtypes.wsattr(
        wtypes.Enum(float, *constants.SUPPORTED_HTTP_VERSIONS))
    domain_name = wtypes.wsattr(
        wtypes.StringType(min_length=1, max_length=255,
                          pattern=constants.DOMAIN_NAME_REGEX))


class HealthMonitorRootPUT(types.BaseType):
    healthmonitor = wtypes.wsattr(HealthMonitorPUT)


class HealthMonitorSingleCreate(BaseHealthMonitorType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    type = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_HEALTH_MONITOR_TYPES),
        mandatory=True)
    delay = wtypes.wsattr(wtypes.IntegerType(minimum=0), mandatory=True)
    timeout = wtypes.wsattr(wtypes.IntegerType(minimum=0), mandatory=True)
    max_retries_down = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_HM_RETRIES,
                           maximum=constants.MAX_HM_RETRIES),
        default=constants.DEFAULT_MAX_RETRIES_DOWN)
    max_retries = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_HM_RETRIES,
                           maximum=constants.MAX_HM_RETRIES),
        mandatory=True)
    http_method = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_HEALTH_MONITOR_HTTP_METHODS))
    url_path = wtypes.wsattr(types.URLPathType())
    expected_codes = wtypes.wsattr(
        wtypes.StringType(pattern=r'^(\d{3}(\s*,\s*\d{3})*)$|^(\d{3}-\d{3})$'))
    admin_state_up = wtypes.wsattr(bool, default=True)
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    http_version = wtypes.wsattr(
        wtypes.Enum(float, *constants.SUPPORTED_HTTP_VERSIONS))
    domain_name = wtypes.wsattr(
        wtypes.StringType(min_length=1, max_length=255,
                          pattern=constants.DOMAIN_NAME_REGEX))

    def to_hm_post(self, pool_id=None, project_id=None):
        hm_post = HealthMonitorPOST()

        for key in [
            'name',
            'type', 'delay', 'timeout', 'max_retries', 'max_retries_down',
            'http_method', 'expected_codes',
            'tags', 'http_version', 'domain_name',
        ]:
            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(hm_post, key, v)

        if self.admin_state_up:
            hm_post.admin_state_up = self.admin_state_up
        if self.url_path:
            hm_post.admin_state_up = self.admin_state_up
        if project_id:
            hm_post.project_id = project_id
        if pool_id:
            setattr(hm_post, 'pool_id', pool_id)
        return hm_post


class HealthMonitorStatusResponse(BaseHealthMonitorType):
    """Defines which attributes are to be shown on status response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    type = wtypes.wsattr(wtypes.text)
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
