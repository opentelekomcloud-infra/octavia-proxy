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
from otcextensions.sdk.vlb.v3 import load_balancer

from octavia_proxy.api.drivers.elbv3 import driver
from octavia_proxy.tests.unit import base

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
    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv3Driver()
        self.sess = mock.MagicMock()
        self.sess.vlb = mock.MagicMock()

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

    def test_flavors_qp(self):
        self.driver.flavors(
            self.sess, 'p1',
            query_filter={'a': 'b'})
        self.sess.vlb.flavors.assert_called_with(
            a='b'
        )

    def test_flavors_no_qp(self):
        self.driver.flavors(self.sess, 'p1')
        self.sess.vlb.flavors.assert_called_with()


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
