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
from openstack.load_balancer.v2._proxy import Proxy
from openstack.load_balancer.v2.health_monitor import HealthMonitor

from octavia_proxy.api.drivers.elbv2 import driver
from octavia_proxy.tests.unit import base
from openstack.load_balancer.v2 import (listener, pool, member, l7_policy,
                                        load_balancer)

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


class TestElbv2Driver(base.TestCase):
    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.sess.elb = mock.MagicMock()

    def test_get_supported_flavor_metadata(self):
        resp = self.driver.get_supported_flavor_metadata()
        self.assertDictEqual(
            resp,
            {"elbv2": "Plain ELBv2 (Neutron-like)"}
        )

    def test_get_supported_availability_zone_metadata(self):
        resp = self.driver.get_supported_availability_zone_metadata()
        self.assertDictEqual(
            resp,
            {"compute_zone": "The compute availability zone to use for "
                             "this loadbalancer."}
        )

    def test_loadbalancers_no_qp(self):
        self.driver.loadbalancers(self.sess, 'p1')
        self.sess.elb.load_balancers.assert_called_with()

    def test_loadbalancers_qp(self):
        self.driver.loadbalancers(
            self.sess, 'p1',
            query_filter={'a': 'b'})
        self.sess.elb.load_balancers.assert_called_with(
            a='b'
        )


class TestElbv2ListenerDriver(base.TestCase):
    attrs = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'loadbalancer_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'protocol_port': 80,
        'protocol': "TCP",
        'insert_headers': {'X-Forwarded-ELB-IP': True},
        'name': 'test',
        'admin_state_up': True,
        'tags': [],
        'timeout_client_data': 10,
        'timeout_member_data': 10,
        'timeout_member_connect': 10,
        'timeout_tcp_inspect': 10,
        'created_at': '2021-08-10T09:39:24+00:00',
        'updated_at': '2021-08-10T09:39:24+00:00',
        'load_balancers': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}]
    }
    fakeCallCreate = {
        'allowed_cidrs': None,
        'alpn_protocols': None,
        'connection_limit': None,
        'created_at': '2021-08-10T09:39:24+00:00',
        'default_pool': None,
        'default_pool_id': None,
        'default_tls_container_ref': None,
        'description': None,
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'insert_headers': {'X-Forwarded-ELB-IP': True},
        'is_admin_state_up': True,
        'l7_policies': None,
        'load_balancer_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'load_balancers': [{'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'}],
        'location': None,
        'name': 'test',
        'operating_status': None,
        'project_id': None,
        'protocol': 'TCP',
        'protocol_port': 80,
        'provisioning_status': None,
        'sni_container_refs': None,
        'tags': [],
        'timeout_client_data': 10,
        'timeout_member_connect': 10,
        'timeout_member_data': 10,
        'timeout_tcp_inspect': 10,
        'tls_ciphers': None,
        'tls_versions': None,
        'updated_at': '2021-08-10T09:39:24+00:00'
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.lsnr = listener.Listener(**self.attrs)
        self.sess.elb.create_listener = mock.MagicMock(return_value=self.lsnr)
        self.sess.elb.find_listener = mock.MagicMock(return_value=self.lsnr)
        self.sess.elb.update_listener = mock.MagicMock(return_value=self.lsnr)

    def test_listeners_no_qp(self):
        self.driver.listeners(self.sess, 'l1')
        self.sess.elb.listeners.assert_called_with()

    def test_listeners_qp(self):
        self.driver.listeners(
            self.sess, 'l1',
            query_filter={'a': 'b'})
        self.sess.elb.listeners.assert_called_with(
            a='b'
        )

    def test_listener_get(self):
        self.driver.listener_get(self.sess, 'test', self.lsnr)
        self.sess.elb.find_listener.assert_called_with(
            name_or_id=self.lsnr, ignore_missing=True)

    def test_listener_create(self):
        self.driver.listener_create(self.sess, self.lsnr)
        self.sess.elb.create_listener.assert_called_with(**self.fakeCallCreate)

    def test_listener_delete(self):
        self.driver.listener_delete(self.sess, self.lsnr)
        self.sess.elb.delete_listener.assert_called_with(self.lsnr.id)

    def test_listener_update(self):
        attrs = {
            'description': 'New Description',
            'operating_status': 'ACTIVE',
        }
        self.driver.listener_update(self.sess, self.lsnr, attrs)
        self.sess.elb.update_listener.assert_called_with(self.lsnr.id, **attrs)


class TestElbv2PoolDriver(base.TestCase):

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
    fakeCallCreate = {
        'alpn_protocols': None,
        'created_at': None,
        'description': 'desc',
        'health_monitor_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'is_admin_state_up': True,
        'lb_algorithm': 'ROUND_ROBIN',
        'listener_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'listeners': [],
        'loadbalancer_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'loadbalancers': [],
        'location': None,
        'members': [],
        'name': 'pool',
        'operating_status': None,
        'project_id': None,
        'protocol': 'TCP',
        'provisioning_status': None,
        'session_persistence': None,
        'tags': [],
        'tls_ciphers': None,
        'tls_versions': None,
        'updated_at': None
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.pool = pool.Pool(**self.attrs)
        self.sess.elb.create_pool = mock.MagicMock(return_value=self.pool)
        self.sess.elb.find_pool = mock.MagicMock(return_value=self.pool)
        self.sess.elb.update_pool = mock.MagicMock(return_value=self.pool)

    def test_pools_no_qp(self):
        self.driver.pools(self.sess, 'l1')
        self.sess.elb.pools.assert_called_with()

    def test_pools_qp(self):
        self.driver.pools(
            self.sess, 'l1',
            query_filter={'a': 'b'})
        self.sess.elb.pools.assert_called_with(
            a='b'
        )

    def test_pool_get(self):
        self.driver.pool_get(self.sess, 'test', self.pool)
        self.sess.elb.find_pool.assert_called_with(
            name_or_id=self.pool, ignore_missing=True)

    def test_pool_create(self):
        self.driver.pool_create(self.sess, self.pool)
        self.sess.elb.create_pool.assert_called_with(**self.fakeCallCreate)

    def test_pool_update(self):
        attrs = {
            'description': 'New Description',
            'operating_status': 'ACTIVE',
        }
        self.driver.pool_update(self.sess, self.pool, attrs)
        self.sess.elb.update_pool.assert_called_with(self.pool.id, **attrs)

    def test_pool_delete(self):
        self.driver.pool_delete(self.sess, self.pool)
        self.sess.elb.delete_pool.assert_called_with(self.pool.id)


class TestElbv2MemberDriver(base.TestCase):
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
    fakeCallCreate = {
        'address': None,
        'created_at': None,
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'is_admin_state_up': True,
        'location': None,
        'name': 'fake',
        'operating_status': None,
        'project_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'protocol_port': 4321,
        'provisioning_status': None,
        'subnet_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'tags': [],
        'updated_at': None,
        'weight': 10

    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.member = member.Member(**self.attrs)
        self.sess.elb.create_member = mock.MagicMock(return_value=self.member)
        self.sess.elb.find_member = mock.MagicMock(return_value=self.member)
        self.sess.elb.update_member = mock.MagicMock(return_value=self.member)

    def test_members_no_qp(self):
        self.driver.members(self.sess, 'l1', 'pid')
        self.sess.elb.members.assert_called_with('pid')

    def test_members_qp(self):
        self.driver.members(
            self.sess, 'l1', 'pid',
            query_filter={'a': 'b'})
        self.sess.elb.members.assert_called_with(
            'pid',
            a='b'
        )

    def test_member_get(self):
        self.driver.member_get(self.sess, 'test', 'pid', 'mid')
        self.sess.elb.find_member.assert_called_with(
            name_or_id='mid', pool='pid', ignore_missing=True)

    def test_member_create(self):
        self.driver.member_create(self.sess, 'pid', self.member)
        self.sess.elb.create_member.assert_called_with(
            'pid',
            **self.fakeCallCreate
        )

    def test_member_update(self):
        attrs = {
            'name': 'New Fake',
            'weight': 5,
        }
        self.driver.member_update(self.sess, 'pid', self.member, attrs)
        self.sess.elb.update_member.assert_called_with(
            self.member.id, 'pid', **attrs)

    def test_member_delete(self):
        self.driver.member_delete(self.sess, 'pid', self.member)
        self.sess.elb.delete_member.assert_called_with(self.member.id, 'pid')


class TestElbv2L7Policy(base.TestCase):
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
            "id":"742600d9-2a14-4808-af69-336883dbb590"
        }],
        "updated_at": "2021-08-20T12:15:57"
    }
    fakeCallCreate = {
        "listener_id": "07f0a424-cdb9-4584-b9c0-6a38fbacdc3a",
        "description": "test_description",
        "is_admin_state_up": True,
        "rules": [{
            "id":"742600d9-2a14-4808-af69-336883dbb590"
        }],
        "created_at": "2021-08-20T12:14:57",
        "provisioning_status": "ACTIVE",
        "updated_at": "2021-08-20T12:15:57",
        "redirect_pool_id": "6460f13a-76de-43c7-b776-4fefc06a676e",
        "redirect_prefix": None,
        "redirect_url": "http://www.example.com",
        "action": "REDIRECT_TO_POOL",
        "position": 1,
        "project_id": "e3cd678b11784734bc366148aa37580e",
        "id": "8a1412f0-4c32-4257-8b07-af4770b604fd",
        "operating_status": "ONLINE",
        "name": "test_l7_policy",
        "location": None,
        "tags":[]
    }
    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.sess.elb = mock.MagicMock()
        self.l7_policy = l7_policy.L7Policy(**self.attrs)
        self.sess.elb.create_l7_policy = mock.MagicMock(
            return_value=self.l7_policy
        )
        self.sess.elb.find_l7_policy = mock.MagicMock(
            return_value=self.l7_policy
        )
        self.sess.elb.update_l7_policy = mock.MagicMock(
            return_value=self.l7_policy
        )

    def test_l7policies_no_qp(self):
        self.driver.l7policies(self.sess, 'l7')
        self.sess.elb.l7_policies.assert_called_with()

    def test_l7policies_qp(self):
        self.driver.l7policies(
            self.sess, 'l7',
            query_filter={'a': 'b'}
        )
        self.sess.elb.l7_policies.assert_called_with(
            a='b'
        )

    def test_l7policy_get(self):
        self.driver.l7policy_get(self.sess, 'l7', self.l7_policy)
        self.sess.elb.find_l7_policy.assert_called_with(
            name_or_id=self.l7_policy, ignore_missing=True
        )

    def test_l7policy_create(self):
        self.driver.l7policy_create(self.sess, self.l7_policy)
        self.sess.elb.create_l7_policy.assert_called_with(**self.fakeCallCreate)

    def test_l7policy_update(self):
        attrs = {
            'description': 'New Description',
        }
        self.driver.l7policy_update(self.sess, self.l7_policy, attrs)
        self.sess.elb.update_l7_policy.assert_called_with(
            l7_policy=self.l7_policy, **attrs
        )

    def test_l7policy_delete(self):
        self.driver.l7policy_delete(self.sess, self.l7_policy)
        self.sess.elb.delete_l7_policy.assert_called_with(
            l7_policy=self.l7_policy,
            ignore_missing=True
        )


class TestElbv2HealthMonitors(base.TestCase):
    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.resp = FakeResponse({})
        self.sess = mock.Mock(spec=adapter.Adapter)
        self.sess.default_microversion = None
        self.sess.elb = Proxy(self.sess)
        self.sess.elb.post = mock.Mock(return_value=self.resp)
        self.sess.elb.get = mock.Mock(return_value=self.resp)
        self.sess.elb.put = mock.Mock(return_value=self.resp)
        self.sess.elb.delete = mock.Mock(
            return_value=FakeResponse({}, status_code=204))

    @property
    def example_monitor(self):
        return {
            'monitor_port': None,
            'name': '',
            'admin_state_up': True,
            'tenant_id': '601240b9c5c94059b63d484c92cfe308',
            'domain_name': None,
            'delay': 5,
            'max_retries': 3,
            'http_method': 'GET',
            'timeout': 10,
            'pools': [
                {
                    'id': 'caef8316-6b65-4676-8293-cf41fb63cc2a'
                }
            ],
            'url_path': '/',
            'type': 'HTTP',
            'id': '1b587819-d619-49c1-9101-fe72d8b361ef'
        }

    def test_list(self):
        response = {
            'healthmonitors': [
                self.example_monitor
            ]
        }

        query = {
            'pool_id': 'bb44bffb-05d9-412c-9d9c-b189d9e14193',
            'delay': 5,
            'max_retries': 3,
            'timeout': 10,
            'type': 'HTTP',
            'admin_state_up': True,
        }
        self.resp.body = response
        monitor_list = self.driver.health_monitors(self.sess, query)
        self.assertEqual(1, len(monitor_list))
        self.sess.elb.get.assert_called_once()
        self.sess.elb.get.assert_called_with(
            '/lbaas/healthmonitors',
            headers={'Accept': 'application/json'},
            params=query,
            microversion=None,
        )

    def test_get(self):
        expected_monitor = self.example_monitor
        self.resp.body = {
            'healthmonitor': self.example_monitor
        }

        monitor = self.driver.health_monitor_get(self.sess,
                                                 expected_monitor['id'])
        self.sess.elb.get.assert_called_once()
        self.sess.elb.get.assert_called_with(
            f'lbaas/healthmonitors/{expected_monitor["id"]}',
            microversion=None,
            params={},
        )
        self.assertEqual(expected_monitor['id'], monitor.id)
        self.assertEqual(expected_monitor['admin_state_up'],
                         monitor.admin_state_up)

    def test_create(self):
        self.resp.body = {
            'healthmonitor': self.example_monitor
        }
        opts = {
            'delay': 5,
            'max_retries': 3,
            'http_method': 'GET',
            'timeout': 10,
            'pools': [
                {
                    'id': 'caef8316-6b65-4676-8293-cf41fb63cc2a'
                }
            ],
            'url_path': '/',
            'type': 'HTTP',
        }
        self.driver.health_monitor_create(self.sess, opts)
        self.sess.elb.post.assert_called_once()
        self.sess.elb.post.assert_called_with(
            '/lbaas/healthmonitors',
            json={
                'healthmonitor': opts
            },
            headers={},
            params={},
            microversion=None,
        )

    def test_update(self):
        response_monitor = self.example_monitor
        response_monitor["max_retries"] = 5
        response_monitor["delay"] = 10
        response_monitor["timeout"] = 20

        self.resp.body = {
            'healthmonitor': response_monitor
        }
        opts = {
            'delay': 10,
            'max_retries': 5,
            'timeout': 20,
        }
        old = HealthMonitor(**self.example_monitor)
        self.driver.health_monitor_update(self.sess, old, opts)
        self.sess.elb.put.assert_called_once()
        self.sess.elb.put.assert_called_with(
            f'lbaas/healthmonitors/{old.id}',
            json={
                'healthmonitor': opts
            },
            headers={},
            microversion=None,
        )

    def test_delete(self):
        monitor = HealthMonitor(**self.example_monitor)
        self.driver.health_monitor_delete(self.sess, monitor)
        self.sess.elb.delete.assert_called_once()
        self.sess.elb.delete.assert_called_with(
            f'lbaas/healthmonitors/{monitor.id}',
            headers={},
            microversion=None,
        )

    @property
    def invalid_opts(self):
        return {
            'delay': 5,
            'max_retries': 3,
            'http_method': 'GET',
            'timeout': 10,
            'url_path': '/',
            'type': 'INVALID_TYPE',
        }

    def test_create_validate(self):
        self.assertRaises(ValueError,
                          self.driver.health_monitor_create,
                          self.sess, self.invalid_opts)

    def test_update_validate(self):
        self.assertRaises(ValueError,
                          self.driver.health_monitor_update,
                          self.sess, self.example_monitor, self.invalid_opts)


class TestElbv2Loadbalancers(base.TestCase):
    attrs = {
        "name": "lb-unit-test",
        "description": "LB for unit tests",
        "vip_subnet_id": "29bb7aa5-44d2-4aaf-8e49-993091c7fa42",
        "provider": "elb",
    }
    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
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
            "id": "38c5e26b-9955-4b15-bc5a-0c587fd1947f",
            "name": "lb-unit-test",
            "description": "LB for unit tests",
            "operating_status": "ONLINE",
            "vip_address": "192.168.0.100",
            "vip_subnet_id": "29bb7aa5-44d2-4aaf-8e49-993091c7fa42",
            "provider": "vlb",
            "provisioning_status": "ACTIVE",
            "tenant_id": "1867112d054b427e808cc6096d8193a1",
            "created_at": "2019-01-19T05:32:56",
            "admin_state_up": True,
            "updated_at": "2019-01-19T05:32:57",
            "listeners": [],
            "vip_port_id": "a7ecbdb5-5a63-41dd-a830-e16c0a7e04a7",
            "tags": []
        }

    def test_create(self):
        lb = load_balancer.LoadBalancer(**self.attrs)
        self.resp.body = self.example_response
        expected = self.example_response

        result = lb.create(self.sess)
        self.sess.post.assert_called_once()
        self.sess.post.assert_called_with(
            "/lbaas/loadbalancers",
            headers={},
            json={"loadbalancer": self.attrs},
            microversion=None,
            params={}
        )
        self.assertEquals(result.is_admin_state_up, expected["admin_state_up"])
        self.assertEquals(result.id, expected["id"])
        self.assertEquals(result.vip_address, expected["vip_address"])

    def test_list(self):
        params = {
            "name": "lb-unit-test",
            "description": "LB for unit tests",
            "operating_status": "ONLINE",
            "provisioning_status": "ACTIVE",
            "vip_address": "192.168.0.100",
            "vip_subnet_id": "29bb7aa5-44d2-4aaf-8e49-993091c7fa42",
            "vip_port_id": "a7ecbdb5-5a63-41dd-a830-e16c0a7e04a7",
            "tags": ["foo", "bar"],
            "project_id": "1867112d054b427e808cc6096d8193a1",
        }
        self.resp.body = {"loadbalancers": []}
        result = load_balancer.LoadBalancer.list(self.sess, **params)
        elements = list(result)  # lazy list loading stuff
        self.assertListEqual([], elements)
        self.sess.get.assert_called_once()
        self.sess.get.assert_called_with(
            "/lbaas/loadbalancers",
            headers={"Accept": "application/json"},
            params=params,
            microversion=None
        )

    def test_get(self):
        lb_id = self.example_response["id"]
        lb = load_balancer.LoadBalancer(id=lb_id)
        self.resp.body = self.example_response

        lb.fetch(self.sess)
        self.sess.get.assert_called_once()
        self.sess.get.assert_called_with(
            f"lbaas/loadbalancers/{lb_id}",
            microversion=None,
            params={},
        )

        self.assertEquals(lb.vip_address, self.example_response["vip_address"])

    def test_delete(self):
        lb_id = self.example_response["id"]
        lb = load_balancer.LoadBalancer(id=lb_id)
        lb.delete(self.sess)
        self.sess.delete.assert_called_once()
        self.sess.delete.assert_called_with(
            f"lbaas/loadbalancers/{lb_id}",
            headers={
                "Accept": ""
            },
            params={},
        )
