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

import requests
from keystoneauth1 import adapter
from otcextensions.sdk.vlb.v3 import (
    load_balancer, listener, pool, member, health_monitor,
    l7_policy, l7_rule, flavor, availability_zone, quota
)

from octavia_proxy.api.drivers.elbv3 import driver
from octavia_proxy.api.v2.types import (
    load_balancer as oct_lb,
    listener as oct_lis
)
from octavia_proxy.tests.unit import base
from octavia_proxy.tests.unit.api.drivers.common import Statuses, statuses

EXAMPLE_LB = {
    "name": "lb-unit-test",
    "description": "LB for unit tests",
    "vip_subnet_cidr_id": "29bb7aa5-44d2-4aaf-8e49-993091c7fa42",
    "provider": "vlb",
}


class FakeResponse:
    def __init__(self, response, status_code=200, headers=None, reason=None):
        self.body = response
        self.content = response
        self.text = response
        self.status_code = status_code
        headers = headers if headers else {'content-type': 'application/json'}
        self.headers = requests.structures.CaseInsensitiveDict(headers)
        if reason:
            self.reason = reason
        # for the sake of "list" response faking
        self.links = []

    def json(self):
        return self.body


class TestElbv3Driver(base.TestCase):
    attrs = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'name': 'test',
        'availability_zone': 'eu-nl-01',
        'admin_state_up': True,
        'tags': [
            {'key': 'tag1', 'value': 'val'},
            {'key': 'tag2', 'value': ''},
            {'key': 'tag3', 'value': ''}],
        'subnet_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'network_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'created_at': '2021-08-10T09:39:24+00:00',
        'updated_at': '2021-08-10T09:39:24+00:00',
        'description': 'Test',
        'guaranteed': True,
        'l7policies': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'listeners': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'pools': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'location': None,
        'project_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'provider': 'elbv3',
        'vpc_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'network_ids': ['07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'],
    }
    octavia_attrs = {
        'name': 'test',
        'description': 'Test',
        'provider': 'elbv3',
        'vip_subnet_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'vip_network_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'tags': ["tag1=val", 'tag2=', 'tag3'],
    }
    fake_call_create = {
        'enabled': True,
        'availability_zone_list': ['eu-de-01'],
        'description': 'Test',
        'elb_virsubnet_ids': ['07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'],
        'name': 'test',
        'tags': [
            {'key': 'tag1', 'value': 'val'},
            {'key': 'tag2', 'value': ''},
            {'key': 'tag3', 'value': ''}],
        'vip_subnet_cidr_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'vip_subnet_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.lb = load_balancer.LoadBalancer(**self.attrs)
        self.sess = mock.MagicMock()
        self.sess.vlb = mock.MagicMock()
        self.sess.vlb.create_load_balancer = mock.MagicMock(
            return_value=self.lb)
        self.sess.vlb.find_load_balancer = mock.MagicMock(
            return_value=self.lb)
        self.sess.vlb.update_load_balancer = mock.MagicMock(
            return_value=self.lb)
        self.sess.vlb.get_load_balancer_statuses = mock.MagicMock(
            return_value=Statuses(**statuses)
        )
        self.sess.vlb.get_flavor = mock.MagicMock(
            return_value=flavor.Flavor(**{
                'id': '9d3ed668-b0ab-4abc-af4a-81458851ef34',
                'name': 'L7_flavor.elb.s2.medium'
            })
        )
        self.sess.vlb.find_flavor = mock.MagicMock(
            return_value=flavor.Flavor(**{
                'id': '232e88a6-e373-49bb-ae8c-830423a37895',
                'name': 'L4_flavor.elb.s2.medium'
            })
        )

    def test_get_supported_flavor_metadata(self):
        resp = self.driver.get_supported_flavor_metadata()
        self.assertDictEqual(
            resp,
            {"elbv3": "Plain ELBv3 (New one)"}
        )

    def test_get_supported_availability_zone_metadata(self):
        resp = self.driver.get_supported_availability_zone_metadata()
        self.assertDictEqual(
            resp,
            {"eu-nl-01": "The compute availability zone to use for "
                         "this loadbalancer."}
        )

    def test_loadbalancers_no_qp(self):
        self.driver.loadbalancers(self.sess, 'p1')
        self.sess.vlb.load_balancers.assert_called_with()

    def test_loadbalancers_qp(self):
        self.driver.loadbalancers(
            self.sess, 'p1',
            query_filter={'a': 'b'})
        self.sess.vlb.load_balancers.assert_called_with(
            a='b'
        )

    def test_loadbalancer_get(self):
        self.driver.loadbalancer_get(self.sess, 'test', self.lb)
        self.sess.vlb.find_load_balancer.assert_called_with(
            name_or_id=self.lb, ignore_missing=True)

    def test_loadbalancer_create(self):
        lb = oct_lb.LoadBalancerPOST(**self.octavia_attrs)
        self.driver.loadbalancer_create(self.sess, lb)
        self.sess.vlb.create_load_balancer.assert_called_with(
            **self.fake_call_create
        )

    def test_loadbalancer_create_multiple_azs(self):
        azs = 'az1,az2'
        self.fake_call_create['availability_zone_list'] = azs.split(',')
        lb = oct_lb.LoadBalancerPOST(
            **self.octavia_attrs,
            availability_zone=azs
        )
        self.driver.loadbalancer_create(self.sess, lb)
        self.sess.vlb.create_load_balancer.assert_called_with(
            **self.fake_call_create
        )

    def test_loadbalancer_create_flavors(self):
        lb = oct_lb.LoadBalancerPOST(
            **self.octavia_attrs,
            flavor_id='9d3ed668-b0ab-4abc-af4a-81458851ef34'
        )
        self.driver.loadbalancer_create(self.sess, lb)
        self.sess.vlb.create_load_balancer.assert_called_with(
            **self.fake_call_create,
            l4_flavor_id='232e88a6-e373-49bb-ae8c-830423a37895',
            l7_flavor_id='9d3ed668-b0ab-4abc-af4a-81458851ef34'
        )

    def test_loadbalancer_update(self):
        attrs = {
            'description': 'New Description',
            'operating_status': 'ACTIVE',
        }
        self.driver.loadbalancer_update(self.sess, self.lb, attrs)
        self.sess.vlb.update_load_balancer.assert_called_with(
            self.lb.id, **attrs)

    def test_loadbalancer_delete(self):
        self.driver.loadbalancer_delete(self.sess, self.lb)
        self.sess.vlb.delete_load_balancer.assert_called_with(self.lb.id)

    def test_loadbalancer_delete_cascade(self):
        self.driver.loadbalancer_delete(self.sess, self.lb, cascade=True)
        self.sess.vlb.get_load_balancer_statuses.assert_called_with(self.lb.id)
        res = statuses['loadbalancer']
        self.sess.vlb.delete_l7_rule.assert_called_with(
            l7_policy=res['listeners'][0]['l7policies'][0]['id'],
            l7rule=res['listeners'][0]['l7policies'][0]['rules'][0]['id'])
        self.sess.vlb.delete_l7_policy.assert_called_with(
            res['listeners'][0]['l7policies'][0]['id']
        )
        self.sess.vlb.delete_health_monitor.assert_called_with(
            res['pools'][0]['healthmonitor']['id']
        )
        self.sess.vlb.delete_member.assert_called_with(
            member=res['pools'][0]['members'][0]['id'],
            pool=res['pools'][0]['id']
        )
        self.sess.vlb.delete_pool.assert_called_with(
            res['pools'][0]['id']
        )
        self.sess.vlb.delete_listener.assert_called_with(
            res['listeners'][0]['id']
        )
        self.sess.vlb.delete_load_balancer.assert_called_with(self.lb.id)


class TestElbv3FlavorDriver(base.TestCase):
    output = [
        {
            'id': '5e512bae-950a-4bb3-8e30-3e8d6a9e030e',
            'name': 'L4_flavor.elb.s2.small'
        },
        {
            'id': '7628a037-c229-4c0c-820b-4ea862743aef',
            'name': 'L7_flavor.elb.s2.small'
        },
        {
            'id': '95b6c7e0-f0d8-495b-9b14-53df1a8dbd81',
            'name': 'L4_flavor.elb.s2.medium'
        },
        {
            'id': '9d3ed668-b0ab-4abc-af4a-81458851ef34',
            'name': 'L7_flavor.elb.s2.medium'
        }
    ]

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.flavors = [flavor.Flavor(**f) for f in self.output]
        self.sess = mock.MagicMock()
        self.sess.vlb.flavors = mock.MagicMock(
            return_value=self.flavors
        )
        self.sess.vlb.get_flavor = mock.MagicMock(
            return_value=flavor.Flavor(**{
                'id': '7628a037-c229-4c0c-820b-4ea862743aef',
                'name': 'L7_flavor.elb.s2.small'
            })
        )

    def test_flavors_no_qp(self):
        result = self.driver.flavors(self.sess, 'p1')
        self.assertEquals(2, len(result))
        self.assertEquals('7628a037-c229-4c0c-820b-4ea862743aef', result[0].id)
        self.assertEquals('9d3ed668-b0ab-4abc-af4a-81458851ef34', result[1].id)
        self.sess.vlb.flavors.assert_called_with()

    def test_flavors_qp(self):
        qp = {'id': '7628a037-c229-4c0c-820b-4ea862743aef'}
        result = self.driver.flavors(
            self.sess, 'p1',
            query_filter=qp)
        self.assertEquals('7628a037-c229-4c0c-820b-4ea862743aef', result[0].id)
        self.assertEquals('L7_flavor.elb.s2.small'[14:], result[0].name)
        self.sess.vlb.get_flavor.assert_called_with(
            qp['id']
        )

    def test_flavors_short_name(self):
        qp = {'name': 's2.medium'}
        self.driver.flavors(
            self.sess, 'p1',
            query_filter=qp)
        self.sess.vlb.flavors.assert_called_with(
            name='L7_flavor.elb.s2.medium'
        )

    def test_flavors_full_name(self):
        qp = {'name': 'L7_flavor.elb.s2.medium'}
        self.driver.flavors(
            self.sess, 'p1',
            query_filter=qp)
        self.sess.vlb.flavors.assert_called_with(
            name='L7_flavor.elb.L7_flavor.elb.s2.medium'
        )

    def test_flavor_get(self):
        self.driver.flavor_get(self.sess, 'p1', self.flavors[0].id)
        self.sess.vlb.get_flavor.assert_called_with(self.flavors[0].id)


class TestElbv3ListenerDriver(base.TestCase):
    attrs = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'loadbalancer_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'protocol_port': 80,
        'protocol': "TCP",
        'insert_headers': {'X-Forwarded-ELB-IP': True},
        'name': 'test',
        'admin_state_up': True,
        'timeout_client_data': 10,
        'timeout_member_data': 10,
        'timeout_member_connect': 10,
        'timeout_tcp_inspect': 10,
        'created_at': '2021-08-10T09:39:24+00:00',
        'updated_at': '2021-08-10T09:39:24+00:00',
        'load_balancers': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'tags': [
            {'key': 'tag1', 'value': 'val'},
            {'key': 'tag2', 'value': ''},
            {'key': 'tag3', 'value': ''}],
    }
    octavia_attrs = {
        'name': 'test',
        'description': 'Test',
        'provider': 'elbv3',
        'loadbalancer_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'protocol': 'TCP',
        'protocol_port': 80,
        'tags': ["tag1=val", 'tag2=', 'tag3'],
    }
    fake_call_create = {
        'client_authentication': 'NONE',
        'description': 'Test',
        'enabled': True,
        'loadbalancer_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'name': 'test',
        'protocol': 'TCP',
        'protocol_port': 80,
        'tags': [
            {'key': 'tag1', 'value': 'val'},
            {'key': 'tag2', 'value': ''},
            {'key': 'tag3', 'value': ''}],
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.lsnr = listener.Listener(**self.attrs)
        self.sess.vlb.create_listener = mock.MagicMock(return_value=self.lsnr)
        self.sess.vlb.find_listener = mock.MagicMock(return_value=self.lsnr)
        self.sess.vlb.update_listener = mock.MagicMock(return_value=self.lsnr)

    def test_listeners_no_qp(self):
        self.driver.listeners(self.sess, 'l1')
        self.sess.vlb.listeners.assert_called_with()

    def test_listeners_qp(self):
        self.driver.listeners(
            self.sess, 'l1',
            query_filter={'a': 'b'})
        self.sess.vlb.listeners.assert_called_with(
            a='b'
        )

    def test_listener_get(self):
        self.driver.listener_get(self.sess, 'test', self.lsnr)
        self.sess.vlb.find_listener.assert_called_with(
            name_or_id=self.lsnr, ignore_missing=True)

    def test_listener_create(self):
        lsnr = oct_lis.ListenerPOST(**self.octavia_attrs)
        self.driver.listener_create(self.sess, lsnr)
        self.sess.vlb.create_listener.assert_called_with(
            **self.fake_call_create
        )

    def test_listener_update(self):
        attrs = {
            'description': 'New Description',
            'operating_status': 'ACTIVE',
        }
        self.driver.listener_update(self.sess, self.lsnr, attrs)
        self.sess.vlb.update_listener.assert_called_with(self.lsnr.id, **attrs)

    def test_listener_delete(self):
        self.driver.listener_delete(self.sess, self.lsnr)
        self.sess.vlb.delete_listener.assert_called_with(self.lsnr.id)


class TestElbv3PoolDriver(base.TestCase):
    attrs = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'description': 'desc',
        'healthmonitor_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'ip_version': 4,
        'lb_algorithm': 'ROUND_ROBIN',
        'listener_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'loadbalancer_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'listeners': [],
        'loadbalancers': [],
        'members': [],
        'name': 'pool',
        'protocol': 'TCP',
        'session_persistence': None,
        'slow_start': None,
        'admin_state_up': True,
    }
    fake_call_create = {
        'description': 'desc',
        'healthmonitor_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'ip_version': 4,
        'is_admin_state_up': True,
        'lb_algorithm': 'ROUND_ROBIN',
        'listener_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'listeners': [],
        'loadbalancer_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'loadbalancers': [],
        'location': None,
        'members': [],
        'name': 'pool',
        'project_id': None,
        'protocol': 'TCP',
        'session_persistence': None,
        'slow_start': None,
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.pool = pool.Pool(**self.attrs)
        self.sess.vlb.create_pool = mock.MagicMock(return_value=self.pool)
        self.sess.vlb.find_pool = mock.MagicMock(return_value=self.pool)
        self.sess.vlb.update_pool = mock.MagicMock(return_value=self.pool)

    def test_pools_no_qp(self):
        self.driver.pools(self.sess, 'l1')
        self.sess.vlb.pools.assert_called_with()

    def test_pools_qp(self):
        self.driver.pools(
            self.sess, 'l1',
            query_filter={'a': 'b'})
        self.sess.vlb.pools.assert_called_with(
            a='b'
        )

    def test_pool_get(self):
        self.driver.pool_get(self.sess, 'test', self.pool)
        self.sess.vlb.find_pool.assert_called_with(
            name_or_id=self.pool, ignore_missing=True)

    def test_pool_create(self):
        self.driver.pool_create(self.sess, self.pool)
        self.sess.vlb.create_pool.assert_called_with(**self.fake_call_create)

    def test_pool_update(self):
        attrs = {
            'description': 'New Description',
            'operating_status': 'ACTIVE',
        }
        self.driver.pool_update(self.sess, self.pool, attrs)
        self.sess.vlb.update_pool.assert_called_with(self.pool.id, **attrs)

    def test_pool_delete(self):
        self.driver.pool_delete(self.sess, self.pool)
        self.sess.vlb.delete_pool.assert_called_with(self.pool.id)


class TestElbv3MemberDriver(base.TestCase):
    attrs = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'address': '192.168.1.10',
        'ip_address': '192.168.1.10',
        'admin_state_up': True,
        'ip_version': 4,
        'name': 'fake',
        'project_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'protocol_port': 4321,
        'subnet_cidr_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'subnet_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'weight': 10,

    }
    fake_call_create = {
        'address': None,
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'ip_version': 4,
        'is_admin_state_up': True,
        'location': None,
        'name': 'fake',
        'operating_status': None,
        'project_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'protocol_port': 4321,
        'subnet_cidr_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'weight': 10,
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.member = member.Member(**self.attrs)
        self.sess.vlb.create_member = mock.MagicMock(return_value=self.member)
        self.sess.vlb.find_member = mock.MagicMock(return_value=self.member)
        self.sess.vlb.update_member = mock.MagicMock(return_value=self.member)
        self.sess.vlb.get_pool = mock.MagicMock(return_value={
                'loadbalancers': [
                    {'id': '12f0a424-cdb9-4584-b9c0-6a38fbacdc5t'}
                ]
            })
        self.sess.vlb.get_load_balancer = mock.MagicMock(
            return_value={
                'vip_subnet_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'
            }
        )

    def test_members_no_qp(self):
        self.driver.members(self.sess, 'l1', 'pid')
        self.sess.vlb.members.assert_called_with('pid')

    def test_members_qp(self):
        self.driver.members(
            self.sess, 'l1', 'pid',
            query_filter={'a': 'b'})
        self.sess.vlb.members.assert_called_with(
            'pid',
            a='b'
        )

    def test_member_get(self):
        self.driver.member_get(self.sess, 'test', 'pid', 'mid')
        self.sess.vlb.find_member.assert_called_with(
            name_or_id='mid', pool='pid', ignore_missing=True)

    def test_member_create(self):
        self.driver.member_create(self.sess, 'pid', self.member)
        self.sess.vlb.create_member.assert_called_with(
            'pid',
            **self.fake_call_create
        )

    def test_member_update(self):
        attrs = {
            'name': 'New Fake',
            'weight': 5,
        }
        self.driver.member_update(self.sess, 'pid', self.member, attrs)
        self.sess.vlb.update_member.assert_called_with(
            self.member.id, 'pid', **attrs)

    def test_member_delete(self):
        self.driver.member_delete(self.sess, 'pid', self.member)
        self.sess.vlb.delete_member.assert_called_with(self.member.id, 'pid')


class TestElbv3HealthMonitorDriver(base.TestCase):
    attrs = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'pool_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'type': 'TCP',
        'timeout': 3,
        'delay': 3,
        'max_retries': 3,
        'admin_state_up': True,
        'monitor_port': 3333,
    }
    fake_call_create = {
        'delay': 3,
        'domain_name': None,
        'expected_codes': None,
        'http_method': None,
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'is_admin_state_up': True,
        'location': None,
        'max_retries': 3,
        'max_retries_down': None,
        'monitor_port': 3333,
        'name': None,
        'pool_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'pools': None,
        'project_id': None,
        'timeout': 3,
        'type': 'TCP',
        'url_path': None,
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.hm = health_monitor.HealthMonitor(**self.attrs)
        self.sess.vlb.create_health_monitor = mock.MagicMock(
            return_value=self.hm)
        self.sess.vlb.find_health_monitor = mock.MagicMock(
            return_value=self.hm)
        self.sess.vlb.update_health_monitor = mock.MagicMock(
            return_value=self.hm)

    def test_health_monitor_no_qp(self):
        self.driver.health_monitors(self.sess, 'l1')
        self.sess.vlb.health_monitors.assert_called_with()

    def test_health_monitor_qp(self):
        self.driver.health_monitors(
            self.sess, 'l1',
            query_filter={'a': 'b'})
        self.sess.vlb.health_monitors.assert_called_with(
            a='b'
        )

    def test_health_monitor_get(self):
        self.driver.health_monitor_get(self.sess, 'test', self.hm.id)
        self.sess.vlb.find_health_monitor.assert_called_with(
            name_or_id=self.hm.id, ignore_missing=True)

    def test_health_monitor_create(self):
        self.driver.health_monitor_create(self.sess, self.hm)
        self.sess.vlb.create_health_monitor.assert_called_with(
            **self.fake_call_create
        )

    def test_health_monitor_update(self):
        attrs = {
            'delay': 5,
            'name': 'hm',
        }
        self.driver.health_monitor_update(self.sess, self.hm, attrs)
        self.sess.vlb.update_health_monitor.assert_called_with(
            self.hm.id,
            **attrs
        )

    def test_health_monitor_delete(self):
        self.driver.health_monitor_delete(self.sess, self.hm)
        self.sess.vlb.delete_health_monitor.assert_called_with(self.hm.id)


class TestElbv3L7Policy(base.TestCase):
    attrs = {
        "action": "REDIRECT_TO_POOL",
        "admin_state_up": True,
        "created_at": "2021-08-20T12:14:57",
        "description": "test_description",
        "id": "8a1412f0-4c32-4257-8b07-af4770b604fd",
        "listener_id": "07f0a424-cdb9-4584-b9c0-6a38fbacdc3a",
        "name": "test_l7_policy",
        "operating_status": "ONLINE",
        "position": 1,
        "project_id": "e3cd678b11784734bc366148aa37580e",
        "provisioning_status": "ACTIVE",
        "redirect_pool_id": "6460f13a-76de-43c7-b776-4fefc06a676e",
        "redirect_prefix": None,
        "redirect_url": "http://www.example.com",
        "rules": [{
            "id": "742600d9-2a14-4808-af69-336883dbb590"
        }],
        "updated_at": "2021-08-20T12:15:57"
    }
    fake_call_create = {
        'listener_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'description': 'test_description',
        'action': 'REDIRECT_TO_POOL',
        'fixed_response_config': None,
        'id': '8a1412f0-4c32-4257-8b07-af4770b604fd',
        'is_admin_state_up': True,
        'location': None,
        'name': 'test_l7_policy',
        'position': 1,
        'priority': None,
        'project_id': 'e3cd678b11784734bc366148aa37580e',
        'provisioning_status': 'ACTIVE',
        'redirect_listener_id': None,
        'redirect_pool_id': '6460f13a-76de-43c7-b776-4fefc06a676e',
        'redirect_url': 'http://www.example.com',
        'redirect_url_config': None,
        'rules': [{
            'id': '742600d9-2a14-4808-af69-336883dbb590'
        }]

    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.sess.vlb = mock.MagicMock()
        self.l7_policy = l7_policy.L7Policy(**self.attrs)
        self.sess.vlb.create_l7_policy = mock.MagicMock(
            return_value=self.l7_policy
        )
        self.sess.vlb.find_l7_policy = mock.MagicMock(
            return_value=self.l7_policy
        )
        self.sess.vlb.update_l7_policy = mock.MagicMock(
            return_value=self.l7_policy
        )

    def test_l7policies_no_qp(self):
        self.driver.l7policies(self.sess, 'l7')
        self.sess.vlb.l7_policies.assert_called_with()

    def test_l7policies_qp(self):
        self.driver.l7policies(
            self.sess, 'l7',
            query_filter={'a': 'b'}
        )
        self.sess.vlb.l7_policies.assert_called_with(
            a='b'
        )

    def test_l7policy_get(self):
        self.driver.l7policy_get(self.sess, 'test', self.l7_policy.id)
        self.sess.vlb.find_l7_policy.assert_called_with(
            name_or_id=self.l7_policy.id, ignore_missing=True)

    def test_l7policy_create(self):
        self.driver.l7policy_create(self.sess, self.l7_policy)
        self.sess.vlb.create_l7_policy.assert_called_with(
            **self.fake_call_create
        )

    def test_l7policy_update(self):
        attrs = {
            'description': 'New Description',
        }
        self.driver.l7policy_update(self.sess, self.l7_policy, attrs)
        self.sess.vlb.update_l7_policy.assert_called_with(
            l7_policy=self.l7_policy.id, **attrs
        )

    def test_l7policy_delete(self):
        self.driver.l7policy_delete(self.sess, self.l7_policy)
        self.sess.vlb.delete_l7_policy.assert_called_with(
            l7_policy=self.l7_policy.id,
            ignore_missing=True
        )


class TestElbv2L7RuleDriver(base.TestCase):

    attrs = {
        "compare_type": "EQUAL_TO",
        "key": None,
        "id": "6abba291-db52-4fe7-b568-a96bed73c643",
        "project_id": "5dd3c0b24cdc4d31952c49589182a89d",
        "provisioning_status": "ACTIVE",
        "tenant_id": "5dd3c0b24cdc4d31952c49589182a89d",
        "value": "/bbb.html",
        "invert": False,
        "admin_state_up": True,
        "type": "PATH"

    }
    fake_call_create = {
        'compare_type': 'EQUAL_TO',
        'conditions': None,
        'id': '6abba291-db52-4fe7-b568-a96bed73c643',
        'invert': False,
        'is_admin_state_up': True,
        'key': None,
        'location': None,
        'name': None,
        'project_id': '5dd3c0b24cdc4d31952c49589182a89d',
        'provisioning_status': 'ACTIVE',
        'rule_value': '/bbb.html',
        'type': 'PATH'
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.l7rule = l7_rule.L7Rule(**self.attrs)
        self.sess.vlb.create_l7_rule = mock.MagicMock(return_value=self.l7rule)
        self.sess.vlb.find_l7_rule = mock.MagicMock(return_value=self.l7rule)
        self.sess.vlb.update_l7_rule = mock.MagicMock(return_value=self.l7rule)
        self.sess.vlb.delete_l7_rule = mock.MagicMock(
            return_value=FakeResponse({}, status_code=204))

    def test_l7rules_no_qp(self):
        self.driver.l7rules(self.sess, 'l1', 'pid')
        self.sess.vlb.l7_rules.assert_called_with('pid')

    def test_l7rules_qp(self):
        self.driver.l7rules(
            self.sess, 'l1', 'pid',
            query_filter={'a': 'b'})
        self.sess.vlb.l7_rules.assert_called_with(
            'pid',
            a='b'
        )

    def test_l7rule_get(self):
        self.driver.l7rule_get(self.sess, 'test', 'pid', 'mid')
        self.sess.vlb.find_l7_rule.assert_called_with(
            name_or_id='mid', l7_policy='pid', ignore_missing=True)

    def test_l7rule_create(self):
        self.driver.l7rule_create(self.sess, l7policy_id='pid',
                                  l7rule=self.l7rule)
        self.sess.vlb.create_l7_rule.assert_called_with(
            l7_policy='pid',
            **self.fake_call_create
        )

    def test_l7rule_update(self):
        attrs = {
            'name': 'New Fake',
            'weight': 5,
        }
        self.driver.l7rule_update(self.sess, 'pid', self.l7rule, attrs)
        self.sess.vlb.update_l7_rule.assert_called_with(
            self.l7rule.id, 'pid', **attrs)

    def test_l7_rule_delete(self):
        self.driver.l7rule_delete(self.sess, l7policy_id='pid',
                                  l7rule=self.l7rule)
        self.sess.vlb.delete_l7_rule.assert_called_with(self.l7rule.id, 'pid')


class TestElbv3DriverRequests(base.TestCase):

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.resp = FakeResponse({})
        self.sess = mock.Mock(spec=adapter.Adapter)
        self.sess.default_microversion = None
        self.sess.post = mock.Mock(return_value=self.resp)
        self.sess.get = mock.Mock(return_value=self.resp)
        self.sess.delete = mock.Mock(
            return_value=FakeResponse({}, status_code=204))

    @property
    def example_response(self):
        return {
            "id": "06a034cb-6410-4077-a787-b3ee809ee229",
            "name": "lb3-unit-test",
            "description": "LB for unit tests",
            "operating_status": "ONLINE",
            "vip_address": "192.168.0.100",
            "vip_subnet_id": "29bb7aa5-44d2-4aaf-8e49-993091c7fa42",
            "provider": "elbv3",
            "provisioning_status": "ACTIVE",
            "tenant_id": "1867112d054b427e808cc6096d8193a1",
            "created_at": "2021-08-10T09:39:24+00:00",
            "admin_state_up": True,
            "updated_at": "2021-08-10T09:39:24+00:00",
            "listeners": [],
            "pools": [],
            "vip_port_id": "4b844946-985f-4e7f-bdc5-54658cbcbe31",
            "tags": []
        }

    def test_create_load_balancer(self):
        lb = load_balancer.LoadBalancer(**EXAMPLE_LB)
        self.resp.body = self.example_response
        expected = self.example_response

        result = lb.create(self.sess)
        self.sess.post.assert_called_once()
        self.sess.post.assert_called_with(
            "/elb/loadbalancers",
            headers={},
            json={"loadbalancer": EXAMPLE_LB},
            microversion=None,
            params={}
        )
        self.assertEquals(result.is_admin_state_up, expected["admin_state_up"])
        self.assertEquals(result.id, expected["id"])
        self.assertEquals(result.vip_address, expected["vip_address"])


class TestElbv3AzDriver(base.TestCase):
    attrs = {
        "code": "eu-nl-01",
        "state": 'ACTIVE'
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.az = availability_zone.AvailabilityZone(**self.attrs)
        self.sess.vlb.availability_zones = mock.MagicMock(
            return_value=[self.az]
        )

    def test_availability_zones_no_qp(self):
        az = self.driver.availability_zones(self.sess, 'pid')
        self.sess.vlb.availability_zones.assert_called()
        self.assertEquals(az[0].name, self.attrs['code'])
        self.assertEquals(az[0].enabled, True)

    def test_availability_zones_qp(self):
        self.driver.availability_zones(
            self.sess, 'pid',
            query_filter={'a': 'b'})
        self.sess.vlb.availability_zones.assert_called_with(
            a='b'
        )

    def test_availability_zones_de_region(self):
        self.sess.config.region_name = 'eu-de'
        self.sess.vlb.availability_zones = mock.MagicMock(
            return_value=[
                availability_zone.AvailabilityZone(
                    **{
                        "code": "eu-nl-01",
                        "state": 'ACTIVE'
                    }),
                availability_zone.AvailabilityZone(
                    **{
                        "code": "eu-de-01",
                        "state": 'ACTIVE'
                    }),
            ]
        )
        az = self.driver.availability_zones(self.sess, 'pid')
        self.sess.vlb.availability_zones.assert_called()
        self.assertEquals(len(az), 1)
        self.assertEquals(az[0].name, 'eu-de-01')
        self.assertEquals(az[0].enabled, True)


class TestElbv3QuotaDriver(base.TestCase):

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.sess.vlb.get_quotas = mock.MagicMock(
            return_value=quota.Quota(**{
                "member": 500,
                "members_per_pool": 500,
                "certificate": 120,
                "l7policy": 500,
                "listener": 100,
                "loadbalancer": 50,
                "healthmonitor": -1,
                "pool": 500,
                "ipgroup": 50,
                "project_id": "c742c92afd8d46b1b3083d004afffd70"
            })
        )

    def test_quotas_no_qp(self):
        self.driver.quotas(
            self.sess, 'pid')
        self.sess.vlb.get_quotas.assert_called()

    def test_quota_get(self):
        quotas = self.driver.quota_get(
            self.sess, 'test', 'c742c92afd8d46b1b3083d004afffd70'
        )
        self.sess.vlb.get_quotas.assert_called()
        self.assertEquals(quotas.member, 500)
        self.assertEquals(quotas.pool, 500)
        self.assertEquals(quotas.l7policy, 500)
        self.assertEquals(quotas.listener, 100)
        self.assertEquals(quotas.healthmonitor, -1)
