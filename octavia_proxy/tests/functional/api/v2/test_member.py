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


class TestMember(base.BaseAPITest):

    root_tag = 'member'
    root_tag_list = 'members'
    root_tag_links = 'members_links'

    def setUp(self):
        super().setUp()
        self.lb_id = self.get_lb_id()
        self.pool = self.create_pool(self.lb_id, constants.PROTOCOL_HTTP,
                                     constants.LB_ALGORITHM_ROUND_ROBIN)
        self.pool_id = self.pool.get('pool').get('id')
        self.members_path = self.MEMBERS_PATH.format(
            pool_id=self.pool_id)
        self.member_path = self.members_path + '/{member_id}'

    @classmethod
    def tearDownClass(cls):
        pass

    def test_create_get_delete(self):
        api_member = self.create_member(
            self.pool_id, '192.168.2.1', 80).get(self.root_tag)
        response = self.get(self.member_path.format(
            member_id=api_member.get('id'))).json.get(self.root_tag)
        self.assertEqual(api_member, response)
        self.assertEqual(api_member.get('name'), None)
        self.delete(self.MEMBER_PATH.format(
            member_id=api_member.get('id'), pool_id=self.pool_id))
        self.delete(self.POOL_PATH.format(pool_id=self.pool_id))

    def test_create_get_all_delete(self):
        api_member = self.create_member(
            self.pool_id, '192.168.2.1', 80).get(self.root_tag)
        members = self.get(self.MEMBERS_PATH.format(
            pool_id=self.pool_id)).json.get(self.root_tag_list)
        self.assertIsInstance(members, list)
        self.assertEqual(1, len(members))
        self.delete(self.MEMBER_PATH.format(
            member_id=api_member.get('id'), pool_id=self.pool_id))
        self.delete(self.POOL_PATH.format(pool_id=self.pool_id))
