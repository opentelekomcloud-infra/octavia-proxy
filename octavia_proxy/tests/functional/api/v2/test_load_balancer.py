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

from octavia_proxy.tests.functional.api.v2 import base


class TestLoadBalancer(base.BaseAPITest):
    root_tag = 'loadbalancer'
    root_tag_list = 'loadbalancers'
    root_tag_links = 'loadbalancers_links'

    def test_empty_list(self):
        response = self.get(self.LBS_PATH)
        api_list = response.json.get(self.root_tag_list)
        self.assertEqual([], api_list)
