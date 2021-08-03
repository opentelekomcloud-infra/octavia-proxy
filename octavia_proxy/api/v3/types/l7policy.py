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

from wsme import types as wtypes

from octavia_proxy.api.common import types
from octavia_proxy.api.v3.types import l7rule
from octavia_proxy.api.v3.types import listener
from octavia_proxy.api.v3.types import pool
from octavia_proxy.common import constants


class UrlConfigResponse(types.BaseType):
    """Defines which attributes are to be shown on any response."""
    protocol = wtypes.wsattr(wtypes.StringType())
    host = wtypes.wsattr(wtypes.StringType())
    port = wtypes.wsattr(wtypes.StringType())
    path = wtypes.wsattr(wtypes.StringType())
    query = wtypes.wsattr(wtypes.StringType())
    status_code = wtypes.wsattr(wtypes.StringType())


class UrlConfigPOST(types.BaseType):
    """Defines mandatory and optional attributes of a POST request."""
    protocol = wtypes.wsattr(wtypes.Enum(
        str, *constants.SUPPORTED_L7POLICY_PROTOCOLS),
        default=constants.L7POLICY_PROTOCOL_REQUEST)
    host = wtypes.wsattr(
        wtypes.StringType(max_length=128),
        default='${host}')
    port = wtypes.wsattr(
        wtypes.StringType(max_length=16),
        default='${port}')
    path = wtypes.wsattr(
        wtypes.StringType(max_length=128),
        default='${path}')
    query = wtypes.wsattr(
        wtypes.StringType(max_length=128),
        default='${query}')
    status_code = wtypes.wsattr(
        wtypes.StringType(max_length=16),
        mandatory=True)


class UrlConfigPUT(types.BaseType):
    """Defines attributes that are acceptable of a PUT request."""
    protocol = wtypes.wsattr(wtypes.Enum(
        str, *constants.SUPPORTED_L7POLICY_PROTOCOLS),
        default=constants.L7POLICY_PROTOCOL_REQUEST)
    host = wtypes.wsattr(
        wtypes.StringType(max_length=128),
        default='${host}')
    port = wtypes.wsattr(
        wtypes.StringType(max_length=16),
        default='${port}')
    path = wtypes.wsattr(
        wtypes.StringType(max_length=128),
        default='${path}')
    query = wtypes.wsattr(
        wtypes.StringType(max_length=128),
        default='${query}')
    status_code = wtypes.wsattr(
        wtypes.StringType(max_length=16))


class FixedConfigResponse(types.BaseType):
    """Defines which attributes are to be shown on any response."""
    status_code = wtypes.wsattr(wtypes.StringType)
    content_type = wtypes.wsattr(wtypes.StringType)
    message_body = wtypes.wsattr(wtypes.StringType())


class FixedConfigPOST(types.BaseType):
    """Defines mandatory and optional attributes of a POST request."""
    status_code = wtypes.wsattr(wtypes.StringType(max_length=16),
                                mandatory=True)
    content_type = wtypes.wsattr(wtypes.StringType(max_length=32),
                                 default=None)
    message_body = wtypes.wsattr(wtypes.StringType(max_length=1024),
                                 default=None)


class FixedConfigPUT(types.BaseType):
    """Defines attributes that are acceptable of a PUT request."""
    status_code = wtypes.wsattr(wtypes.StringType(max_length=16))
    content_type = wtypes.wsattr(wtypes.StringType(max_length=32),
                                 default=None)
    message_body = wtypes.wsattr(wtypes.StringType(max_length=1024),
                                 default=None)


class BaseL7PolicyType(types.BaseType):
    _type_to_model_map = {'admin_state_up': 'enabled'}
    _child_map = {}


class L7PolicyResponse(BaseL7PolicyType):
    """Defines which attributes are to be shown on any response."""
    action = wtypes.wsattr(wtypes.StringType())
    admin_state_up = wtypes.wsattr(bool)
    description = wtypes.wsattr(wtypes.StringType())
    id = wtypes.wsattr(wtypes.UuidType())
    listener_id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    position = wtypes.wsattr(wtypes.IntegerType())
    project_id = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    redirect_listener_id = wtypes.wsattr(wtypes.UuidType())
    redirect_pool_id = wtypes.wsattr(wtypes.UuidType())
    redirect_url = wtypes.wsattr(wtypes.StringType())
    rules = wtypes.wsattr([types.IdOnlyType])
    redirect_url_config = wtypes.wsattr(UrlConfigResponse)
    fixed_response_config = wtypes.wsattr(FixedConfigResponse)
    priority = wtypes.wsattr(wtypes.IntegerType())

    @classmethod
    def from_data_model(cls, data_model, children=False):
        policy = super(L7PolicyResponse, cls).from_data_model(
            data_model, children=children)

        if cls._full_response():
            rule_model = l7rule.L7RuleFullResponse
        else:
            rule_model = types.IdOnlyType
        policy.rules = [
            rule_model.from_data_model(i) for i in data_model.l7rules]
        return policy


class L7PolicyFullResponse(L7PolicyResponse):
    @classmethod
    def _full_response(cls):
        return True

    rules = wtypes.wsattr([l7rule.L7RuleFullResponse])


class L7PolicyRootResponse(types.BaseType):
    l7policy = wtypes.wsattr(L7PolicyResponse)


class L7PoliciesRootResponse(types.BaseType):
    l7policies = wtypes.wsattr([L7PolicyResponse])
    l7policies_links = wtypes.wsattr([types.PageType])


class L7PolicyPOST(BaseL7PolicyType):
    """Defines mandatory and optional attributes of a POST request."""
    action = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_L7POLICY_ACTIONS_V3),
        mandatory=True)
    admin_state_up = wtypes.wsattr(bool, default=True)
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    listener_id = wtypes.wsattr(wtypes.UuidType(), mandatory=True)
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    position = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_POLICY_POSITION,
        maximum=constants.MAX_POLICY_POSITION_V3),
        default=constants.MAX_POLICY_POSITION_V3)
    priority = wtypes.wsattr(wtypes.IntegerType(
        minimum=0,
        maximum=10000))
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    redirect_listener_id = wtypes.wsattr(wtypes.UuidType())
    redirect_pool_id = wtypes.wsattr(wtypes.UuidType())
    redirect_url = wtypes.wsattr(types.URLType())
    redirect_url_config = wtypes.wsattr(UrlConfigPOST)
    fixed_response_config = wtypes.wsattr(FixedConfigPOST)
    rules = wtypes.wsattr([l7rule.L7RuleSingleCreate])


class L7PolicyRootPOST(types.BaseType):
    l7policy = wtypes.wsattr(L7PolicyPOST)


class L7PolicyPUT(BaseL7PolicyType):
    """Defines attributes that are acceptable of a PUT request."""
    admin_state_up = wtypes.wsattr(bool, default=True)
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    priority = wtypes.wsattr(wtypes.IntegerType(
        minimum=0,
        maximum=10000))
    redirect_listener_id = wtypes.wsattr(wtypes.UuidType())
    redirect_pool_id = wtypes.wsattr(wtypes.UuidType())
    redirect_url_config = wtypes.wsattr(UrlConfigPUT)
    fixed_response_config = wtypes.wsattr(FixedConfigPUT)
    rules = wtypes.wsattr([l7rule.L7RuleSingleCreate])


class L7PolicyRootPUT(types.BaseType):
    l7policy = wtypes.wsattr(L7PolicyPUT)


class L7PolicySingleCreate(BaseL7PolicyType):
    """Defines mandatory and optional attributes of a POST request."""
    action = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_L7POLICY_ACTIONS_V3),
        mandatory=True)
    admin_state_up = wtypes.wsattr(bool, default=True)
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    position = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_POLICY_POSITION,
        maximum=constants.MAX_POLICY_POSITION_V3),
        default=constants.MAX_POLICY_POSITION_V3)
    priority = wtypes.wsattr(wtypes.IntegerType(
        minimum=0,
        maximum=10000))
    redirect_listener = wtypes.wsattr(listener.ListenerSingleCreate())
    redirect_pool = wtypes.wsattr(pool.PoolSingleCreate)
    redirect_url = wtypes.wsattr(types.URLType())
    redirect_url_config = wtypes.wsattr(UrlConfigPUT)
    fixed_response_config = wtypes.wsattr(FixedConfigPUT)
    rules = wtypes.wsattr([l7rule.L7RuleSingleCreate])
