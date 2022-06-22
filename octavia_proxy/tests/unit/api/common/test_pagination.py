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
import datetime
from unittest import mock

from dateutil.tz import tzlocal

from octavia_proxy.api.common import pagination
from octavia_proxy.common import exceptions
from octavia_proxy.tests.unit import base

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
        "created_at": datetime.datetime(2021, 10, 13, 8, 10, 36),
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": datetime.datetime(2021, 10, 13, 8, 11, 36),
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a9"
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
        "created_at": datetime.datetime(2021, 10, 13, 8, 13, 36),
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": datetime.datetime(2021, 10, 13, 8, 14, 36),
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
        "created_at": datetime.datetime(2021, 10, 13, 8, 14, 36),
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": datetime.datetime(2021, 10, 13, 8, 15, 36),
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a6"
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
        "created_at": datetime.datetime(2021, 10, 13, 8, 11, 36),
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": datetime.datetime(2021, 10, 13, 8, 12, 36),
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a8"
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
        "created_at": datetime.datetime(2021, 10, 13, 8, 16, 36),
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": datetime.datetime(2021, 10, 13, 8, 17, 36),
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a4"
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
        "created_at": datetime.datetime(2021, 10, 13, 8, 15, 36),
        "tags": [],
        "pools": [],
        "tenant_id": "959db9b6017d4a1fa1c6fd17b682fake",
        "updated_at": datetime.datetime(2021, 10, 13, 8, 16, 36),
        "vip_subnet_id": "6543210a-847b-4cb5-a1b8-282c4a1fake5",
        "admin_state_up": True,
        "vip_port_id": "15c5fca3-f02a-485e-920f-fake987317a5"
    }
]

SORTED_EXAMPLE = [
    {
        'admin_state_up': True,
        'created_at': datetime.datetime(2021, 10, 13, 8, 10, 36,
                                        tzinfo=tzlocal()),
        'description': 'Best App lb test',
        'id': '147f018a-f401-48d1-b58a-50fe6600fake',
        'listeners': [],
        'name': 'lb_test1',
        'operating_status': 'ONLINE',
        'pools': [],
        'project_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'provider': 'vlb',
        'provisioning_status': 'ACTIVE',
        'tags': [],
        'tenant_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'updated_at': datetime.datetime(2021, 10, 13, 8, 11, 36,
                                        tzinfo=tzlocal()),
        'vip_address': '192.168.241.33',
        'vip_port_id': '15c5fca3-f02a-485e-920f-fake987317a9',
        'vip_subnet_id': '6543210a-847b-4cb5-a1b8-282c4a1fake5'
    },
    {
        'admin_state_up': True,
        'created_at': datetime.datetime(2021, 10, 13, 8, 11, 36,
                                        tzinfo=tzlocal()),
        'description': 'Best App lb test 2',
        'id': '123f018a-f401-48d1-b58a-50fe6600fake',
        'listeners': [],
        'name': 'lb_test2',
        'operating_status': 'ONLINE',
        'pools': [],
        'project_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'provider': 'vlb',
        'provisioning_status': 'ACTIVE',
        'tags': [],
        'tenant_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'updated_at': datetime.datetime(2021, 10, 13, 8, 12, 36,
                                        tzinfo=tzlocal()),
        'vip_address': '192.168.241.32',
        'vip_port_id': '15c5fca3-f02a-485e-920f-fake987317a8',
        'vip_subnet_id': '6543210a-847b-4cb5-a1b8-282c4a1fake5'
    },
    {
        'admin_state_up': True,
        'created_at': datetime.datetime(2021, 10, 13, 8, 13, 36,
                                        tzinfo=tzlocal()),
        'description': 'Best App lb test 3',
        'id': '345f018a-f401-48d1-b58a-50fe6600fake',
        'listeners': [],
        'name': 'lb_test3',
        'operating_status': 'ONLINE',
        'pools': [],
        'project_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'provider': 'vlb',
        'provisioning_status': 'ACTIVE',
        'tags': [],
        'tenant_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'updated_at': datetime.datetime(2021, 10, 13, 8, 14, 36,
                                        tzinfo=tzlocal()),
        'vip_address': '192.168.241.31',
        'vip_port_id': '15c5fca3-f02a-485e-920f-fake987317a7',
        'vip_subnet_id': '6543210a-847b-4cb5-a1b8-282c4a1fake5'
    },
    {
        'admin_state_up': True,
        'created_at': datetime.datetime(2021, 10, 13, 8, 14, 36,
                                        tzinfo=tzlocal()),
        'description': 'Best App lb test 4',
        'id': '456f018a-f401-48d1-b58a-50fe6600fake',
        'listeners': [],
        'name': 'lb_test4',
        'operating_status': 'ONLINE',
        'pools': [],
        'project_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'provider': 'vlb',
        'provisioning_status': 'ACTIVE',
        'tags': [],
        'tenant_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'updated_at': datetime.datetime(2021, 10, 13, 8, 15, 36,
                                        tzinfo=tzlocal()),
        'vip_address': '192.168.241.31',
        'vip_port_id': '15c5fca3-f02a-485e-920f-fake987317a6',
        'vip_subnet_id': '6543210a-847b-4cb5-a1b8-282c4a1fake5'
    },
    {
        'admin_state_up': True,
        'created_at': datetime.datetime(2021, 10, 13, 8, 15, 36,
                                        tzinfo=tzlocal()),
        'description': 'Best App lb test 5',
        'id': '567f018a-f401-48d1-b58a-50fe6600fake',
        'listeners': [],
        'name': 'lb_test5',
        'operating_status': 'ONLINE',
        'pools': [],
        'project_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'provider': 'vlb',
        'provisioning_status': 'ACTIVE',
        'tags': [],
        'tenant_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'updated_at': datetime.datetime(2021, 10, 13, 8, 16, 36,
                                        tzinfo=tzlocal()),
        'vip_address': '192.168.241.30',
        'vip_port_id': '15c5fca3-f02a-485e-920f-fake987317a5',
        'vip_subnet_id': '6543210a-847b-4cb5-a1b8-282c4a1fake5'
    },
    {
        'admin_state_up': True,
        'created_at': datetime.datetime(2021, 10, 13, 8, 16, 36,
                                        tzinfo=tzlocal()),
        'description': 'Best App lb test 6',
        'id': '678f018a-f401-48d1-b58a-50fe6600fake',
        'listeners': [],
        'name': 'lb_test6',
        'operating_status': 'ONLINE',
        'pools': [],
        'project_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'provider': 'vlb',
        'provisioning_status': 'ACTIVE',
        'tags': [],
        'tenant_id': '959db9b6017d4a1fa1c6fd17b682fake',
        'updated_at': datetime.datetime(2021, 10, 13, 8, 17, 36,
                                        tzinfo=tzlocal()),
        'vip_address': '192.168.241.29',
        'vip_port_id': '15c5fca3-f02a-485e-920f-fake987317a4',
        'vip_subnet_id': '6543210a-847b-4cb5-a1b8-282c4a1fake5'
    }
]
PATH_URL = 'http://localhost:9876/v2/lbaas/loadbalancers.json'


class TestPaginationHelper(base.TestCase):

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_no_param(self, request_mock):
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
        limit = 4
        params = {'limit': limit}
        helper = pagination.PaginationHelper(params)
        self.assertEqual(limit, helper.limit)

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_sorting_and_links_generation(self, request_mock):
        request_mock.path_url = PATH_URL
        params = {
            'marker': '147f018a-f401-48d1-b58a-50fe6600fake',
            'limit': 4,
            'page_reverse': False
        }
        expected_result = SORTED_EXAMPLE[1:5]
        expected_links = [
            {'href': 'http://localhost:9876/v2/lbaas/loadbalancers.json'
                     '?limit=4&marker=147f018a-f401-48d1-b58a-50fe6600fake',
             'rel': 'previous'},
            {'href': 'http://localhost:9876/v2/lbaas/loadbalancers.json'
                     '?limit=4&marker=678f018a-f401-48d1-b58a-50fe6600fake',
             'rel': 'next'}
        ]
        helper = pagination.PaginationHelper(params)
        result, links = helper.apply(EXAMPLE)
        self.assertEqual(expected_result, result)
        self.assertEqual(expected_links, links)

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_sorting_and_links_generation_reversed(self, request_mock):
        request_mock.path_url = PATH_URL
        params = {
            'marker': '147f018a-f401-48d1-b58a-50fe6600fake',
            'limit': 4,
            'page_reverse': True
        }
        expected_result = SORTED_EXAMPLE[0:1]
        expected_links = [
            {'href': 'http://localhost:9876/v2/lbaas/loadbalancers.json'
                     '?limit=4&marker=147f018a-f401-48d1-b58a-50fe6600fake'
                     '&page_reverse=True',
             'rel': 'previous'}
        ]
        helper = pagination.PaginationHelper(params)
        result, links = helper.apply(EXAMPLE)
        self.assertEqual(expected_result, result)
        self.assertEqual(expected_links, links)

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_links_generation_reversed(self, request_mock):
        request_mock.path_url = PATH_URL
        params = {
            'marker': None,
            'limit': 4,
            'page_reverse': True
        }
        expected_result = SORTED_EXAMPLE[5:1:-1]
        expected_links = [
            {'href': 'http://localhost:9876/v2/lbaas/loadbalancers.json'
                     '?limit=4&marker=123f018a-f401-48d1-b58a-50fe6600fake'
                     '&page_reverse=True',
             'rel': 'next'}
        ]
        helper = pagination.PaginationHelper(params)
        result, links = helper.apply(EXAMPLE)
        self.assertEqual(expected_result, result)
        self.assertEqual(expected_links, links)

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_marker_is_last_element_in_list(self, request_mock):
        request_mock.path_url = PATH_URL
        params = {
            'marker': "678f018a-f401-48d1-b58a-50fe6600fake",
            'limit': None,
            'page_reverse': False
        }
        expected_result = SORTED_EXAMPLE[5:4:-1]
        expected_links = [
            {'href': 'http://localhost:9876/v2/lbaas/loadbalancers.json'
                     '?marker=678f018a-f401-48d1-b58a-50fe6600fake',
             'rel': 'previous'}
        ]
        helper = pagination.PaginationHelper(params)
        result, links = helper.apply(EXAMPLE)
        self.assertEqual(expected_result, result)
        self.assertEqual(expected_links, links)

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_marker_is_last_element_in_list_reversed(self, request_mock):
        request_mock.path_url = PATH_URL
        params = {
            'marker': "147f018a-f401-48d1-b58a-50fe6600fake",
            'limit': None,
            'page_reverse': True
        }
        expected_result = SORTED_EXAMPLE[0:1]
        expected_links = [
            {'href': 'http://localhost:9876/v2/lbaas/loadbalancers.json'
                     '?marker=147f018a-f401-48d1-b58a-50fe6600fake'
                     '&page_reverse=True',
             'rel': 'previous'}
        ]
        helper = pagination.PaginationHelper(params)
        result, links = helper.apply(EXAMPLE)
        self.assertEqual(expected_result, result)
        self.assertEqual(expected_links, links)

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_empty_links(self, request_mock):
        request_mock.path_url = PATH_URL
        params = {
            'marker': None,
            'limit': None,
            'page_reverse': False
        }
        expected_result = SORTED_EXAMPLE
        expected_links = []
        helper = pagination.PaginationHelper(params)
        result, links = helper.apply(EXAMPLE)
        self.assertEqual(expected_result, result)
        self.assertEqual(expected_links, links)

    @mock.patch('octavia_proxy.api.common.pagination.request')
    def test_empty_links_reversed(self, request_mock):
        request_mock.path_url = PATH_URL
        params = {
            'marker': None,
            'limit': None,
            'page_reverse': True
        }
        expected_result = SORTED_EXAMPLE[::-1]
        expected_links = []
        helper = pagination.PaginationHelper(params)
        result, links = helper.apply(EXAMPLE)
        self.assertEqual(expected_result, result)
        self.assertEqual(expected_links, links)
