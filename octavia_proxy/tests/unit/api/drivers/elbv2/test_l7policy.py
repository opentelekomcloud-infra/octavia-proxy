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
import uuid
from unittest import mock

from openstack.load_balancer.v2 import l7_policy

from octavia_proxy.api.drivers.elbv2 import driver
from octavia_proxy.tests.unit import base
from octavia_proxy.tests.unit.api.drivers.elbv2.fixtures import FakeResponse


class TestElbv2L7Policy(base.TestCase):
    attrs = {
        "action": "REDIRECT_TO_POOL",
        "admin_state_up": True,
        "created_at": "2017-07-17T12:14:57.233772",
        "description": "test_description",
        "id": uuid.uuid4(),
        "listener_id": uuid.uuid4(),
        "name": 'test_l7_policy',
        "operating_status": 'ONLINE',
        "position": 7,
        "project_id": uuid.uuid4(),
        "provisioning_status": "ACTIVE",
        "redirect_pool_id": uuid.uuid4(),
        "redirect_prefix": "https://www.example.com",
        "redirect_url": "/test_url",
        "rules": [{"id": uuid.uuid4()}],
        "updated_at": "2017-07-17T12:16:57.233772",

    }
    fakeCallCreate = {
        "listener_id": "023f2e34-7806-443b-bfae-16c324569a3d",
        "description": "Redirect requests to example.com",
        "admin_state_up": True,
        "rules": [
            {
                "id": "efd6a3f8-73bf-47f0-8ae6-503ebda57372"
            }
        ],
        "created_at": "2017-06-24T23:25:14",
        "provisioning_status": "ACTIVE",
        "updated_at": "2017-06-24T23:30:05",
        "redirect_http_code": 301,
        "redirect_pool_id": None,
        "redirect_prefix": None,
        "redirect_url": "http://www.example.com",
        "action": "REDIRECT_TO_POOL",
        "position": 1,
        "project_id": "e3cd678b11784734bc366148aa37580e",
        "id": "8a1412f0-4c32-4257-8b07-af4770b604fd",
        "operating_status": "OFFLINE",
        "name": "redirect-example.com",
        "tags": ["test_tag"]
    }
    def setUp(self):
        super().setUp()
        self.driver = driver.ELBv2Driver()
        self.resp = FakeResponse({})
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
            self.l7_policy.id, **attrs
        )

    def test_l7policy_delete(self):
        self.driver.l7policy_delete(self.sess, self.l7_policy)
        self.sess.elb.delete_l7_policy.assert_called_with(self.l7_policy.id)
