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
from wsme import types as wtypes
from octavia_proxy.api.drivers.elbv2 import driver
from octavia_proxy.api.v2.controllers import BaseV2Controller
from octavia_proxy.api.v2.types import (load_balancer as lb_types,
                                        listener as listener_types)
from octavia_proxy.tests.unit import base
from openstack.load_balancer.v2 import (listener, pool, member, l7_policy,
                                        load_balancer, health_monitor,
                                        l7_rule)


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


class TestElbv2Driver(base.TestCase):

    EXAMPLE_LB = {'id': '70d638f5-29ba-443a-ba76-4277eb420292',
                  'name': 'ex_name', 'project_id': '7823987',
                  'vip_address': '192.168.0.10',
                  'provisioning_status': 'ACTIVE',
                  'operating_status': 'ACTIVE', 'provider': 'elbv2'}

    attrs = {
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'name': 'test',
        'availability_zone': 'eu-nl-01',
        'admin_state_up': True,
        'tags': [],
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
        'provider': 'elbv2',
        'vpc_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'network_ids': ['07f0a424-cdb9-4584-b9c0-6a38fbacdc3a'],
    }
    fake_call_create = {
        'availability_zone': 'eu-nl-01',
        'created_at': '2021-08-10T09:39:24+00:00',
        'updated_at': '2021-08-10T09:39:24+00:00',
        'description': 'Test',
        'flavor_id': None,
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'project_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'is_admin_state_up': True,
        'location': None,
        'name': 'test',
        'provider': 'elbv2',
        'operating_status': None,
        'provisioning_status': None,
        'vip_address': None,
        'vip_port_id': None,
        'vip_qos_policy_id': None,
        'vip_subnet_id': None,
        'tags': [],
    }

    LB_RESPONSE_TYPE_PROPERTIES = ['id', 'name', 'description',
                                   'provisioning_status', 'operating_status',
                                   'admin_state_up', 'project_id',
                                   'created_at',
                                   'updated_at', 'vip_address', 'vip_port_id',
                                   'vip_subnet_id', 'vip_network_id',
                                   'listeners',
                                   'pools', 'provider', 'flavor_id',
                                   'vip_qos_policy_id', 'tags',
                                   'availability_zone']

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.sess.elb = mock.MagicMock()
        self.lb = load_balancer.LoadBalancer(**self.attrs)
        self.sess.elb.create_load_balancer = mock.MagicMock(
            return_value=self.lb)
        self.sess.elb.find_load_balancer = mock.MagicMock(
            return_value=self.lb)
        self.sess.elb.update_load_balancer = mock.MagicMock(
            return_value=self.lb)
        self.lb_response1 = lb_types.LoadBalancerResponse(**self.EXAMPLE_LB)
        self.lb_response2 = lb_types.LoadBalancerResponse(**self.EXAMPLE_LB)

    def _assert_only_filtered_fields_present(self, list_objects, fields):
        for object in list_objects:
            for property in self.LB_RESPONSE_TYPE_PROPERTIES:
                if property not in fields:
                    self.assertIsInstance(getattr(object, property),
                                          wtypes.UnsetType)

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

    def test_loadbalancer_get(self):
        self.driver.loadbalancer_get(self.sess, 'test', self.lb)
        self.sess.elb.find_load_balancer.assert_called_with(
            name_or_id=self.lb, ignore_missing=True)

    def test_loadbalancer_create(self):
        self.driver.loadbalancer_create(self.sess, self.lb)
        self.sess.elb.create_load_balancer.assert_called_with(
            **self.fake_call_create)

    def test_loadbalancer_update(self):
        attrs = {
            'description': 'New Description',
            'operating_status': 'ACTIVE',
        }
        self.driver.loadbalancer_update(self.sess, self.lb, attrs)
        self.sess.elb.update_load_balancer.assert_called_with(
            self.lb.id, **attrs)

    def test_loadbalancer_delete(self):
        self.driver.loadbalancer_delete(self.sess, self.lb)
        self.sess.elb.delete_load_balancer.assert_called_with(
            self.lb.id,
            cascade=False
        )

    def test_loadbalancer_delete_cascade(self):
        self.driver.loadbalancer_delete(self.sess, self.lb, cascade=True)
        self.sess.elb.delete_load_balancer.assert_called_with(
            self.lb.id,
            cascade=True
        )

    def test_filter_fields_loadbalancer(self):
        lb_objects = []
        fields = ['id', 'name']
        lb_objects.append(self.lb_response1)
        lb_objects.append(self.lb_response2)
        controller = BaseV2Controller()
        self.driver.loadbalancers = mock.MagicMock(return_value=lb_objects)
        result = controller._filter_fields(lb_objects, fields)
        self._assert_only_filtered_fields_present(lb_objects, fields)


class TestElbv2ListenerDriver(base.TestCase):

    EXAMPLE_LISTENER = {'id': '70d638f5-29ba-443a-ba76-4277eb420292',
                        'name': 'ex_name', 'project_id': '7823987',
                        'vip_address': '192.168.0.10',
                        'provisioning_status': 'ACTIVE',
                        'operating_status': 'ACTIVE', 'provider': 'elbv2'}

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
    fake_call_create = {
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

    LISTENER_RESPONSE_TYPE_PROPERTIES = ['id', 'name', 'description',
                                         'provisioning_status',
                                         'operating_status','admin_state_up',
                                         'protocol', 'protocol_port',
                                         'connection_limit',
                                         'default_tls_container_ref',
                                         'sni_container_refs', 'project_id',
                                         'default_pool_id', 'l7policies',
                                         'insert_headers', 'created_at',
                                         'updated_at', 'loadbalancers',
                                         'timeout_client_data',
                                         'timeout_member_connect',
                                         'timeout_member_data',
                                         'timeout_tcp_inspect',
                                         'client_ca_tls_container_ref',
                                         'client_authentication',
                                         'client_crl_container_ref',
                                         'allowed_cidrs',
                                         'tls_ciphers', 'tls_versions',
                                         'alpn_protocols', 'tags']

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.lsnr = listener.Listener(**self.attrs)
        self.sess.elb.create_listener = mock.MagicMock(return_value=self.lsnr)
        self.sess.elb.find_listener = mock.MagicMock(return_value=self.lsnr)
        self.sess.elb.update_listener = mock.MagicMock(return_value=self.lsnr)
        self.lsnr_response1 = listener_types.ListenerResponse(
            **self.EXAMPLE_LISTENER)
        self.lsnr_response2 = listener_types.ListenerResponse(
            **self.EXAMPLE_LISTENER)

    def _assert_only_filtered_fields_present(self, list_objects, fields):
        for object in list_objects:
            for property in self.LISTENER_RESPONSE_TYPE_PROPERTIES:
                if property not in fields:
                    self.assertIsInstance(getattr(object, property),
                                          wtypes.UnsetType)

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
        self.sess.elb.create_listener.assert_called_with(
            **self.fake_call_create)

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

    def test_filter_fields_listener(self):
        lstn_objects = []
        fields = ['id', 'name']
        lstn_objects.append(self.lsnr_response1)
        lstn_objects.append(self.lsnr_response2)
        controller = BaseV2Controller()
        self.driver.listeners = mock.MagicMock(return_value=lstn_objects)
        result = controller._filter_fields(lstn_objects, fields)
        self._assert_only_filtered_fields_present(result, fields)


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
    fake_call_create = {
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
        self.sess.elb.create_pool.assert_called_with(**self.fake_call_create)

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
    fake_call_create = {
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
            **self.fake_call_create
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


class TestElbv2HealthMonitorDriver(base.TestCase):

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
        'created_at': None,
        'delay': 3,
        'expected_codes': None,
        'http_method': None,
        'id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'is_admin_state_up': True,
        'location': None,
        'max_retries': 3,
        'max_retries_down': None,
        'name': None,
        'operating_status': None,
        'pool_id': '07f0a424-cdb9-4584-b9c0-6a38fbacdc3a',
        'pools': None,
        'project_id': None,
        'provisioning_status': None,
        'tags': [],
        'timeout': 3,
        'type': 'TCP',
        'updated_at': None,
        'url_path': None
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.healthmonitor = health_monitor.HealthMonitor(**self.attrs)
        self.sess.elb.create_health_monitor = mock.MagicMock(
            return_value=self.healthmonitor)
        self.sess.elb.find_health_monitor = mock.MagicMock(
            return_value=self.healthmonitor)
        self.sess.elb.update_health_monitor = mock.MagicMock(
            return_value=self.healthmonitor)

    def test_healthmonitors_no_qp(self):
        self.driver.health_monitors(self.sess, 'l1')
        self.sess.elb.health_monitors.assert_called_with()

    def test_health_monitors_qp(self):
        self.driver.health_monitors(
            self.sess, 'l1',
            query_filter={'a': 'b'})
        self.sess.elb.health_monitors.assert_called_with(
            a='b'
        )

    def test_health_monitor_get(self):
        self.driver.health_monitor_get(
            self.sess, 'test', healthmonitor_id=self.healthmonitor.id)
        self.sess.elb.find_health_monitor.assert_called_with(
            name_or_id=self.healthmonitor.id, ignore_missing=True)

    def test_health_monitor_create(self):
        self.driver.health_monitor_create(self.sess, self.healthmonitor)
        self.sess.elb.create_health_monitor.assert_called_with(
            **self.fake_call_create)

    def test_health_monitor_update(self):
        attrs = {'delay': 5, 'name': 'hm'}
        self.driver.health_monitor_update(self.sess, self.healthmonitor, attrs)
        self.sess.elb.update_health_monitor.assert_called_with(
            self.healthmonitor.id, **attrs)

    def test_healthmonitor_delete(self):
        self.driver.health_monitor_delete(self.sess, self.healthmonitor)
        self.sess.elb.delete_health_monitor.assert_called_with(
            self.healthmonitor.id)


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
            "id": "742600d9-2a14-4808-af69-336883dbb590"
        }],
        "updated_at": "2021-08-20T12:15:57"
    }
    fake_call_create = {
        "listener_id": "07f0a424-cdb9-4584-b9c0-6a38fbacdc3a",
        "description": "test_description",
        "is_admin_state_up": True,
        "rules": [{
            "id": "742600d9-2a14-4808-af69-336883dbb590"
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
        "tags": []
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
        self.sess.elb.create_l7_policy.assert_called_with(
            **self.fake_call_create
        )

    def test_l7policy_update(self):
        attrs = {
            'description': 'New Description',
        }
        self.driver.l7policy_update(self.sess, self.l7_policy, attrs)
        self.sess.elb.update_l7_policy.assert_called_with(
            l7_policy=self.l7_policy.id, **attrs
        )

    def test_l7policy_delete(self):
        self.driver.l7policy_delete(self.sess, self.l7_policy)
        self.sess.elb.delete_l7_policy.assert_called_with(
            l7_policy=self.l7_policy.id,
            ignore_missing=True
        )


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
        'created_at': None,
        'id': '6abba291-db52-4fe7-b568-a96bed73c643',
        'invert': False,
        'is_admin_state_up': True,
        'key': None,
        'location': None,
        'name': None,
        'operating_status': None,
        'project_id': '5dd3c0b24cdc4d31952c49589182a89d',
        'provisioning_status': 'ACTIVE',
        'rule_value': '/bbb.html',
        'tags': [],
        'type': 'PATH',
        'updated_at': None
    }

    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.sess = mock.MagicMock()
        self.l7rule = l7_rule.L7Rule(**self.attrs)
        self.sess.elb.create_l7_rule = mock.MagicMock(return_value=self.l7rule)
        self.sess.elb.find_l7_rule = mock.MagicMock(return_value=self.l7rule)
        self.sess.elb.update_l7_rule = mock.MagicMock(return_value=self.l7rule)
        self.sess.elb.delete_l7_rule = mock.MagicMock(
            return_value=FakeResponse({}, status_code=204))

    def test_l7rules_no_qp(self):
        self.driver.l7rules(self.sess, 'l1', 'pid')
        self.sess.elb.l7_rules.assert_called_with('pid')

    def test_l7rules_qp(self):
        self.driver.l7rules(
            self.sess, 'l1', 'pid',
            query_filter={'a': 'b'})
        self.sess.elb.l7_rules.assert_called_with(
            'pid',
            a='b'
        )

    def test_l7rule_get(self):
        self.driver.l7rule_get(self.sess, 'test', 'pid', 'mid')
        self.sess.elb.find_l7_rule.assert_called_with(
            name_or_id='mid', l7_policy='pid', ignore_missing=True)

    def test_l7rule_create(self):
        self.driver.l7rule_create(self.sess, l7policy_id='pid',
                                  l7rule=self.l7rule)
        self.sess.elb.create_l7_rule.assert_called_with(
            l7_policy='pid',
            **self.fake_call_create
        )

    def test_l7rule_update(self):
        attrs = {
            'name': 'New Fake',
            'weight': 5,
        }
        self.driver.l7rule_update(self.sess, 'pid', self.l7rule, attrs)
        self.sess.elb.update_l7_rule.assert_called_with(
            self.l7rule.id, 'pid', **attrs)

    def test_l7_rule_delete(self):
        self.driver.l7rule_delete(self.sess, l7policy_id='pid',
                                  l7rule=self.l7rule)
        self.sess.elb.delete_l7_rule.assert_called_with(self.l7rule.id, 'pid')
