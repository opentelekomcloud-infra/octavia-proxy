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

from octavia_proxy.tests.unit import base
from octavia_proxy.api.common import pagination
from octavia_proxy.common import exceptions

DEFAULT_SORTS = [('id', 'asc')]
EXAMPLE = [
    {
        "admin_state_up": True,
        "listeners": [],
        "vip_subnet_id": "08dce793-daef-411d-a896-d389cd45b1ea",
        "pools": [],
        "provider": "octavia",
        "description": "Best App load balancer 1",
        "name": "aabestapp1",
        "operating_status": "ONLINE",
        "id": "34d5f4a5-cbbc-43a0-878f-b8a26370e6e7",
        "provisioning_status": "ACTIVE",
        "vip_port_id": "1e20d91d-8df9-4c15-9778-28bc89226c19",
        "vip_address": "203.0.113.10",
        "project_id": "bf325b04-e7b1-4002-9b10-f4984630367f"
    },
    {
        "admin_state_up": True,
        "listeners": [],
        "vip_subnet_id": "08dce793-daef-411d-a896-d389cd45b1ea",
        "pools": [],
        "provider": "octavia",
        "description": "Second Best App load balancer 1",
        "name": "bbbestapp2",
        "operating_status": "ONLINE",
        "id": "0fdb0ca7-0a38-4aea-891c-daaed40bcafe",
        "provisioning_status": "ACTIVE",
        "vip_port_id": "21f7ac04-6824-4222-93cf-46e0d70607f9",
        "vip_address": "203.0.113.20",
        "project_id": "bf325b04-e7b1-4002-9b10-f4984630367f"
    },
    {
        "admin_state_up": True,
        "listeners": [],
        "vip_subnet_id": "08dce793-daef-411d-a896-d389cd45b1ea",
        "pools": [],
        "provider": "octavia",
        "description": "Third best App load balancer 1",
        "name": "acbestapp3",
        "operating_status": "ONLINE",
        "id": "1fdb0ca7-0a38-4aea-891c-daaed40bcawe",
        "provisioning_status": "ACTIVE",
        "vip_port_id": "21f7ac04-6824-4222-93cf-46e0d70607f9",
        "vip_address": "203.0.113.20",
        "project_id": "bf325b04-e7b1-4002-9b10-f4984630367f"
    },
    {
        "admin_state_up": True,
        "listeners": [],
        "vip_subnet_id": "08dce793-daef-411d-a896-d389cd45b1ea",
        "pools": [],
        "provider": "octavia",
        "description": "Another Best App load balancer 1",
        "name": "ddbestapp4",
        "operating_status": "ONLINE",
        "id": "2fdb0ca7-0a38-4aea-891c-daaed40bcadc",
        "provisioning_status": "ACTIVE",
        "vip_port_id": "21f7ac04-6824-4222-93cf-46e0d70607f9",
        "vip_address": "203.0.113.20",
        "project_id": "bf325b04-e7b1-4002-9b10-f4984630367f"
    }
]


class TestPaginationHelper(base.TestCase):

    def test_no_param(self):
        params = {}
        helper = pagination.PaginationHelper(params)

        helper.apply(EXAMPLE)
        self.assertEqual(DEFAULT_SORTS, helper.sort_keys_dirs)
        self.assertIsNone(helper.marker)
        self.assertEqual(1000, helper.limit)

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
        limit = 100
        params = {'limit': limit}
        helper = pagination.PaginationHelper(params)
        self.assertEqual(limit, helper.limit)
