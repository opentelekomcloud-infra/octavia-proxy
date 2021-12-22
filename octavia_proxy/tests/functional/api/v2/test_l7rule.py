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

from octavia_proxy.common import constants
from octavia_proxy.tests.functional.api.v2 import base


class TestL7Rule(base.BaseAPITest):

    root_tag = 'rule'
    root_tag_list = 'rules'
    root_tag_links = 'rules_links'

    def setUp(self):
        super().setUp()
        self.lb_id = self.get_lb_id()
        self.listener = self.create_listener(
            constants.PROTOCOL_HTTP, 80, lb_id=self.lb_id)
        self.listener_id = self.listener.get('listener').get('id')
        self.pool = self.create_pool(
            self.lb_id,
            constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN)
        self.pool_id = self.pool.get('pool').get('id')
        self.l7policy = self.create_l7policy(
            self.listener_id, constants.L7POLICY_ACTION_REDIRECT_TO_POOL,
            redirect_pool_id=self.pool_id)
        self.l7policy_id = self.l7policy.get('l7policy').get('id')
        self.l7rules_path = self.L7RULES_PATH.format(
            l7policy_id=self.l7policy_id)
        self.l7rule_path = self.l7rules_path + '/{l7rule_id}'

    @classmethod
    def tearDownClass(cls):
        pass

    def test_create_get_delete(self):
        l7rule = self.create_l7rule(
            self.l7policy_id, constants.L7RULE_TYPE_PATH,
            constants.L7RULE_COMPARE_TYPE_STARTS_WITH,
            '/api').get(self.root_tag)
        response = self.get(self.l7rule_path.format(
            l7rule_id=l7rule.get('id'))).json.get(self.root_tag)
        self.assertEqual(l7rule, response)
        self.delete(self.l7rule_path.format(l7rule_id=l7rule.get('id')))
        self.delete(self.L7POLICY_PATH.format(
           l7policy_id=self.l7policy_id))
        self.delete(self.POOL_PATH.format(pool_id=self.pool_id))
        self.delete(self.LISTENER_PATH.format(listener_id=self.listener_id))

    def test_create_get_all_delete(self):
        l7rule1 = self.create_l7rule(
            self.l7policy_id, constants.L7RULE_TYPE_PATH,
            constants.L7RULE_COMPARE_TYPE_STARTS_WITH, '/api'
        ).get(self.root_tag)
        l7rule2 = self.create_l7rule(
            self.l7policy_id, constants.L7RULE_TYPE_HOST_NAME,
            constants.L7RULE_COMPARE_TYPE_EQUAL_TO, 'test'
        ).get(self.root_tag)
        rules = self.get(self.L7RULES_PATH.format(
            l7policy_id=self.l7policy_id)).json.get(self.root_tag_list)
        self.assertIsInstance(rules, list)
        self.assertEqual(2, len(rules))
        rule_id_type = [(r.get('id'), r.get('type')) for r in rules]
        self.assertIn((l7rule1.get('id'), l7rule1.get('type')), rule_id_type)
        self.assertIn((l7rule2.get('id'), l7rule2.get('type')), rule_id_type)
        self.delete(self.l7rule_path.format(l7rule_id=l7rule1.get('id')))
        self.delete(self.l7rule_path.format(l7rule_id=l7rule2.get('id')))
        self.delete(self.L7POLICY_PATH.format(l7policy_id=self.l7policy_id))
        self.delete(self.POOL_PATH.format(pool_id=self.pool_id))
        self.delete(self.LISTENER_PATH.format(listener_id=self.listener_id))
