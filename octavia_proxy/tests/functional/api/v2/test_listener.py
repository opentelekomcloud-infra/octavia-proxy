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

from octavia_proxy.common import constants
from octavia_proxy.tests.functional.api.v2 import base


class TestListener(base.BaseAPITest):

    root_tag = 'listener'
    root_tag_list = 'listeners'
    root_tag_links = 'listeners_links'

    def setUp(self):
        super().setUp()
        self.lb_id = self.get_lb_id()
        self.listener_path = self.LISTENERS_PATH+'/{listener_id}'
        # self.pool = self.create_pool(
        #     self.lb_id, constants.PROTOCOL_HTTP,
        #     constants.LB_ALGORITHM_ROUND_ROBIN)
        # self.pool_id = self.pool.get('pool').get('id')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_get_all_admin(self):
        listener1 = self.create_listener(
            constants.PROTOCOL_HTTP, 80, self.lb_id
            ).get(self.root_tag)
        listener2 = self.create_listener(
            constants.PROTOCOL_HTTP, 81, self.lb_id
            ).get(self.root_tag)
        listener3 = self.create_listener(
            constants.PROTOCOL_HTTP, 82, self.lb_id
            ).get(self.root_tag)
        listeners = self.get(self.LISTENERS_PATH).json.get(self.root_tag_list)
        self.assertEqual(3, len(listeners))
        listener_id_ports = [(li.get('id'), li.get('protocol_port'))
                             for li in listeners]
        self.assertIn((listener1.get('id'), listener1.get('protocol_port')),
                      listener_id_ports)
        self.assertIn((listener2.get('id'), listener2.get('protocol_port')),
                      listener_id_ports)
        self.assertIn((listener3.get('id'), listener3.get('protocol_port')),
                      listener_id_ports)
        self.delete(self.LISTENER_PATH.format(
            listener_id=listener1.get('id')))
        self.delete(self.LISTENER_PATH.format(
            listener_id=listener2.get('id')))
        self.delete(self.LISTENER_PATH.format(
            listener_id=listener3.get('id')))
