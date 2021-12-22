
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

from octavia_proxy.common import constants
from octavia_proxy.tests.functional.api.v2 import base


class TestHealthMonitor(base.BaseAPITest):

    root_tag = 'healthmonitor'
    root_tag_list = 'healthmonitors'
    root_tag_links = 'healthmonitors_links'

    def setUp(self):
        super().setUp()
        self.lb_id = self.get_lb_id()
        self.listener = self.create_listener(
            constants.PROTOCOL_HTTP, 80,
            self.lb_id).get('listener')
        self.listener_id = self.listener.get('id')
        self.pool_with_listener = self.create_pool(
            self.lb_id, constants.PROTOCOL_HTTP,
            constants.LB_ALGORITHM_ROUND_ROBIN, listener_id=self.listener_id)
        self.pool_with_listener_id = (
            self.pool_with_listener.get('pool').get('id'))

    @classmethod
    def tearDownClass(cls):
        pass

    def test_create_get_delete(self):
        api_hm = self.create_health_monitor(
            self.pool_with_listener_id, constants.HEALTH_MONITOR_HTTP,
            1, 1, 1, 1).get(self.root_tag)
        response = self.get(self.HM_PATH.format(
            healthmonitor_id=api_hm.get('id'))).json.get(self.root_tag)
        self.assertEqual(api_hm, response)
        self.delete(self.HM_PATH.format(healthmonitor_id=api_hm.get('id')))
        self.delete(self.POOL_PATH.format(pool_id=self.pool_with_listener_id))
        self.delete(self.LISTENER_PATH.format(listener_id=self.listener_id))

    def test_create_get_all_delete(self):
        api_hm = self.create_health_monitor(
            self.pool_with_listener_id, constants.HEALTH_MONITOR_HTTP,
            1, 1, 1, 1).get(self.root_tag)
        hms = self.get(self.HMS_PATH).json.get(self.root_tag_list)
        self.assertIsInstance(hms, list)
        self.assertEqual(1, len(hms))
        self.assertEqual(api_hm.get('id'), hms[0].get('id'))
        self.delete(self.HM_PATH.format(healthmonitor_id=api_hm.get('id')))
        self.delete(self.POOL_PATH.format(pool_id=self.pool_with_listener_id))
        self.delete(self.LISTENER_PATH.format(listener_id=self.listener_id))
