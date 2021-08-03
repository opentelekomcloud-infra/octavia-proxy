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
from octavia_proxy.common import constants


class RuleConditionResponse(types.BaseType):
    """Defines which attributes are to be shown on any response."""
    key = wtypes.wsattr(wtypes.StringType)
    value = wtypes.wsattr(wtypes.StringType)


class RuleConditionPOST(types.BaseType):
    """Defines mandatory and optional attributes of a POST request."""
    key = wtypes.wsattr(wtypes.StringType(max_length=128))
    value = wtypes.wsattr(
        wtypes.StringType(max_length=128),
        mandatory=True)


class RuleConditionPUT(types.BaseType):
    """Defines attributes that are acceptable of a PUT request."""
    key = wtypes.wsattr(wtypes.StringType(max_length=128))
    value = wtypes.wsattr(wtypes.StringType(max_length=128))


class BaseL7Type(types.BaseType):
    _type_to_model_map = {'admin_state_up': 'enabled'}
    _child_map = {}


class L7RuleResponse(BaseL7Type):
    """Defines which attributes are to be shown on any response."""
    admin_state_up = wtypes.wsattr(bool)
    compare_type = wtypes.wsattr(wtypes.StringType())
    id = wtypes.wsattr(wtypes.UuidType())
    invert = wtypes.wsattr(bool)
    key = wtypes.wsattr(wtypes.StringType())
    project_id = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    type = wtypes.wsattr(wtypes.StringType())
    value = wtypes.wsattr(wtypes.StringType())
    conditions = wtypes.wsattr(RuleConditionResponse)

    @classmethod
    def from_data_model(cls, data_model, children=False):
        rule = super(L7RuleResponse, cls).from_data_model(
            data_model, children=children)
        return rule


class L7RuleFullResponse(L7RuleResponse):
    @classmethod
    def _full_response(cls):
        return True


class L7RuleRootResponse(types.BaseType):
    rule = wtypes.wsattr(L7RuleResponse)


class L7RulesRootResponse(types.BaseType):
    rules = wtypes.wsattr([L7RuleResponse])
    rules_links = wtypes.wsattr([types.PageType])


class L7RulePOST(BaseL7Type):
    """Defines mandatory and optional attributes of a POST request."""
    admin_state_up = wtypes.wsattr(bool, default=True)
    compare_type = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_L7RULE_COMPARE_TYPES_V3),
        mandatory=True)
    key = wtypes.wsattr(wtypes.StringType(max_length=255))
    value = wtypes.wsattr(wtypes.StringType(max_length=255), mandatory=True)
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    type = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_L7RULE_TYPES_V3),
        mandatory=True)
    invert = wtypes.wsattr(bool, default=False)
    conditions = wtypes.wsattr(wtypes.ArrayType(RuleConditionPOST))


class L7RuleRootPOST(types.BaseType):
    rule = wtypes.wsattr(L7RulePOST)


class L7RulePUT(BaseL7Type):
    """Defines attributes that are acceptable of a PUT request."""
    type = wtypes.wsattr(
        wtypes.Enum(str,
                    *constants.SUPPORTED_L7RULE_TYPES_V3))
    compare_type = wtypes.wsattr(
        wtypes.Enum(str,
                    *constants.SUPPORTED_L7RULE_COMPARE_TYPES_V3))
    key = wtypes.wsattr(wtypes.StringType(max_length=255))
    value = wtypes.wsattr(wtypes.StringType(max_length=255))
    invert = wtypes.wsattr(bool)
    admin_state_up = wtypes.wsattr(bool)
    conditions = wtypes.wsattr(wtypes.ArrayType(RuleConditionPUT))


class L7RuleRootPUT(types.BaseType):
    rule = wtypes.wsattr(L7RulePUT)


class L7RuleSingleCreate(BaseL7Type):
    """Defines mandatory and optional attributes of a POST request."""
    type = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_L7RULE_TYPES),
        mandatory=True)
    compare_type = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_L7RULE_COMPARE_TYPES),
        mandatory=True)
    key = wtypes.wsattr(wtypes.StringType(max_length=255))
    value = wtypes.wsattr(wtypes.StringType(max_length=255), mandatory=True)
    invert = wtypes.wsattr(bool, default=False)
    admin_state_up = wtypes.wsattr(bool, default=True)
