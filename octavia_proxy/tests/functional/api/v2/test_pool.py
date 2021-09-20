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

from oslo_utils import uuidutils

from octavia_proxy.common import constants
from octavia_proxy.tests.functional.api.v2 import base
from octavia_proxy.api.v2.controllers.pool import PoolsController

class TestPool(base.BaseAPITest):
    root_tag = 'listener'
    root_tag_list = 'listeners'
    root_tag_links = 'listeners_links'
    api_lb = None
    lb_id = None

    def setUp(self):
        super().setUp()

    def tearDownUp(self):
        super().tearDown()

    # def test_create(self, **optionals):
    #     pool_json = {'name': 'test1-lstnr',
    #                'protocol': 'TCP',
    #                'listener_id': '51a11fb7-0b38-4080-be8b-8bfc90ffdb3b',
    #                'lb-algorithm': 'ROUND_ROBIN'
    #                }
    #     body = self._build_body(pool_json)
    #     response = self.post(self.POOLS_PATH, body)
    #     self.api_listener = response.json.get(self.root_tag)


    def test_delete(self, **optionals):
        pool_json = {}
        body = self._build_body(pool_json)
        cnt = PoolsController()
        response = cnt.delete(id='fcfcb5b7-4bbd-4eba-9209-30f4a8b24310')
        a = 5
