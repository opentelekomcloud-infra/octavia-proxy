# Copyright 2017 Walmart Stores Inc..
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
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_FLAVOR,
                                    action=constants.RBAC_GET_ALL),
        constants.RULE_API_READ,
        "List Flavors",
        [{'method': 'GET', 'path': '/v2.0/lbaas/flavors'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_FLAVOR,
                                    action=constants.RBAC_GET_ALL_GLOBAL),
        constants.RULE_API_READ_GLOBAL,
        "List Flavors including resources owned by others",
        [{'method': 'GET', 'path': '/v2/lbaas/flavors'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_FLAVOR,
                                    action=constants.RBAC_POST),
        constants.RULE_API_ADMIN,
        "Create a Flavor",
        [{'method': 'POST', 'path': '/v2.0/lbaas/flavors'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_FLAVOR,
                                    action=constants.RBAC_PUT),
        constants.RULE_API_ADMIN,
        "Update a Flavor",
        [{'method': 'PUT', 'path': '/v2.0/lbaas/flavors/{flavor_id}'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_FLAVOR,
                                    action=constants.RBAC_GET_ONE),
        constants.RULE_API_READ,
        "Show Flavor details",
        [{'method': 'GET',
          'path': '/v2.0/lbaas/flavors/{flavor_id}'}]
    ),
    policy.DocumentedRuleDefault(
        '{rbac_obj}{action}'.format(rbac_obj=constants.RBAC_FLAVOR,
                                    action=constants.RBAC_DELETE),
        constants.RULE_API_ADMIN,
        "Remove a Flavor",
        [{'method': 'DELETE',
          'path': '/v2.0/lbaas/flavors/{flavor_id}'}]
    ),
]


def list_rules():
    return rules
