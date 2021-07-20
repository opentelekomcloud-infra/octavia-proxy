# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from octavia_proxy.tests.functional.api.v2 import base


class TestProvider(base.BaseAPITest):

    root_tag_list = 'providers'

    def setUp(self):
        super().setUp()

    def test_get_all_providers(self):
        elbv2_dict = {u'description': u'The ELBv2 driver.',
                      u'name': u'elbv2'}
        elbv3_dict = {u'description': u'The ELBv3 driver.',
                      u'name': u'elbv3'}
        providers = self.get(self.PROVIDERS_PATH).json.get(self.root_tag_list)
        self.assertEqual(2, len(providers))
        self.assertIn(elbv2_dict, providers)
        self.assertIn(elbv3_dict, providers)

    def test_get_all_providers_fields(self):
        elbv2_dict = {u'name': u'elbv2'}
        elbv3_dict = {u'name': u'elbv3'}
        providers = self.get(self.PROVIDERS_PATH, params={'fields': ['name']})
        providers_list = providers.json.get(self.root_tag_list)
        self.assertEqual(2, len(providers_list))
        self.assertIn(elbv2_dict, providers_list)
        self.assertIn(elbv3_dict, providers_list)
