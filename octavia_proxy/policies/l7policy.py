# Copyright 2017 Rackspace, US Inc.
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

from oslo_policy import policy

from octavia_proxy.common import constants

rules = [
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_L7POLICY,
                                    action=constants.RBAC_GET_ALL),
        constants.RULE_API_READ,
        "List L7 Policys",
        [{'method': 'GET', 'path': '/v2/lbaas/l7policies'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_L7POLICY,
                                    action=constants.RBAC_GET_ALL_GLOBAL),
        constants.RULE_API_READ_GLOBAL,
        "List L7 Policys including resources owned by others",
        [{'method': 'GET', 'path': '/v2/lbaas/l7policies'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_L7POLICY,
                                    action=constants.RBAC_POST),
        constants.RULE_API_WRITE,
        "Create a L7 Policy",
        [{'method': 'POST', 'path': '/v2/lbaas/l7policies'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_L7POLICY,
                                    action=constants.RBAC_GET_ONE),
        constants.RULE_API_READ,
        "Show L7 Policy details",
        [{'method': 'GET',
          'path': '/v2/lbaas/l7policies/{l7policy_id}'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_L7POLICY,
                                    action=constants.RBAC_PUT),
        constants.RULE_API_WRITE,
        "Update a L7 Policy",
        [{'method': 'PUT',
          'path': '/v2/lbaas/l7policies/{l7policy_id}'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_L7POLICY,
                                    action=constants.RBAC_DELETE),
        constants.RULE_API_WRITE,
        "Remove a L7 Policy",
        [{'method': 'DELETE',
          'path': '/v2/lbaas/l7policies/{l7policy_id}'}]
    ),
]


def list_rules():
    return rules
