#    Copyright 2018 Rackspace, US Inc.
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

from unittest import mock

from octavia_proxy.tests.unit import base
from octavia_proxy.api.common import pagination
from octavia_proxy.common import exceptions

DEFAULT_SORTS = [('created_at', 'asc'), ('id', 'asc')]
EXAMPLE = [
    {
        "name": "lb_test1",
        "id": "147f018a-f401-48d1-b58a-50fe6600fake",
        "description": "Best App lb test",
        "provisioning_status": "ACTIVE",
        "provider": "vlb",
        "operating_status": "ONLINE",
        "vip_address": "192.168.241.33",
        "listeners": [],
        "project_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "created_at": "2021-10-13T11:01:08",
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": "2021-10-13T11:01:09",
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a9"
    },
    {
        "name": "lb_test2",
        "id": "123f018a-f401-48d1-b58a-50fe6600fake",
        "description": "Best App lb test 2",
        "provisioning_status": "ACTIVE",
        "provider": "vlb",
        "operating_status": "ONLINE",
        "vip_address": "192.168.241.32",
        "listeners": [],
        "project_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "created_at": "2021-10-13T11:02:08",
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": "2021-10-13T11:02:09",
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a8"
    },
    {
        "name": "lb_test3",
        "id": "345f018a-f401-48d1-b58a-50fe6600fake",
        "description": "Best App lb test 3",
        "provisioning_status": "ACTIVE",
        "provider": "vlb",
        "operating_status": "ONLINE",
        "vip_address": "192.168.241.31",
        "listeners": [],
        "project_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "created_at": "2021-10-13T11:03:08",
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": "2021-10-13T11:03:09",
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a7"
    },
    {
        "name": "lb_test4",
        "id": "456f018a-f401-48d1-b58a-50fe6600fake",
        "description": "Best App lb test 4",
        "provisioning_status": "ACTIVE",
        "provider": "vlb",
        "operating_status": "ONLINE",
        "vip_address": "192.168.241.31",
        "listeners": [],
        "project_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "created_at": "2021-10-13T11:04:08",
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": "2021-10-13T11:05:09",
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a6"
    },
    {
        "name": "lb_test5",
        "id": "567f018a-f401-48d1-b58a-50fe6600fake",
        "description": "Best App lb test 5",
        "provisioning_status": "ACTIVE",
        "provider": "vlb",
        "operating_status": "ONLINE",
        "vip_address": "192.168.241.30",
        "listeners": [],
        "project_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "created_at": "2021-10-13T11:05:08",
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": "2021-10-13T11:05:09",
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a5"
    },
    {
        "name": "lb_test6",
        "id": "678f018a-f401-48d1-b58a-50fe6600fake",
        "description": "Best App lb test 6",
        "provisioning_status": "ACTIVE",
        "provider": "vlb",
        "operating_status": "ONLINE",
        "vip_address": "192.168.241.29",
        "listeners": [],
        "project_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "created_at": "2021-10-13T11:06:08",
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": "2021-10-13T11:06:09",
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a4"
    },
]


class TestPaginationHelper(base.TestCase):

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_no_param(self, request_mock):
        params = {}
        helper = pagination.PaginationHelper(params)
        helper.apply(EXAMPLE)
        self.assertEqual(DEFAULT_SORTS, helper.sort_keys_dirs)
        self.assertIsNone(helper.marker)
        self.assertEqual(4, helper.limit)

    def test_sort_empty(self):
        sort_params = ""
        params = {'sort': sort_params}
        act_params = pagination.PaginationHelper(params).sort_keys_dirs
        self.assertEqual([], act_params)

    def test_sort_none(self):
        sort_params = None
        params = {'sort': sort_params}
        act_params = pagination.PaginationHelper(params).sort_keys_dirs
        self.assertEqual([], act_params)

    def test_sort_key_dir(self):
        sort_keys = "key1,key2,key3"
        sort_dirs = "asc,desc"
        ref_sort_keys_dirs = [
            ('key1', 'asc'), ('key2', 'desc'), ('key3', 'asc')
        ]
        params = {'sort_key': sort_keys, 'sort_dir': sort_dirs}
        helper = pagination.PaginationHelper(params)
        self.assertEqual(ref_sort_keys_dirs, helper.sort_keys_dirs)

    def test_invalid_sorts(self):
        sort_params = "should_fail_exception:cause:of:this"
        params = {'sort': sort_params}
        self.assertRaises(exceptions.InvalidSortKey,
                          pagination.PaginationHelper,
                          params)
        sort_params = "key1:asc, key2:InvalidDir, key3"
        params = {'sort': sort_params}
        self.assertRaises(exceptions.InvalidSortDirection,
                          pagination.PaginationHelper,
                          params)

    def test_marker(self):
        marker = 'random_uuid'
        params = {'marker': marker}
        helper = pagination.PaginationHelper(params)
        self.assertEqual(marker, helper.marker)

    def test_limit(self):
        limit = 4
        params = {'limit': limit}
        helper = pagination.PaginationHelper(params)
        self.assertEqual(limit, helper.limit)

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_sorting_and_links_generation(self, request_mock):
        params = {
            'marker': '147f018a-f401-48d1-b58a-50fe6600fake',
            'limit': 4,
            'page_reverse': False
        }
        expected_link_list = [
            {'href': 'http://localhost:9876/v2/lbaas/loadbalancers.json'
                     '?limit=4&marker=147f018a-f401-48d1-b58a-50fe6600fake',
             'rel': 'previous'},
            {'href': 'http://localhost:9876/v2/lbaas/loadbalancers.json'
                     '?limit=4&marker=678f018a-f401-48d1-b58a-50fe6600fake',
             'rel': 'next'}
        ]
        helper = pagination.PaginationHelper(params)
        entities_list, links = helper.apply(EXAMPLE)
        self.assertEqual(expected_link_list, links)
