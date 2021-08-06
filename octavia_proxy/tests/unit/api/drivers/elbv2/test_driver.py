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
from openstack.load_balancer.v2 import load_balancer

from octavia_proxy.api.drivers.elbv2 import driver
from octavia_proxy.tests.unit import base

EXAMPLE = {
    "name": "lb-unit-test",
    "description": "LB for unit tests",
    "vip_subnet_id": "29bb7aa5-44d2-4aaf-8e49-993091c7fa42",
    "provider": "vlb",
}


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


class TestElbv2DriverRequests(base.TestCase):
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
        lb = load_balancer.LoadBalancer(**EXAMPLE)
        self.resp.body = self.example_response
        expected = self.example_response

        result = lb.create(self.sess)
        self.sess.post.assert_called_once()
        self.sess.post.assert_called_with(
            "/lbaas/loadbalancers",
            headers={},
            json={"loadbalancer": EXAMPLE},
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
