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

from octavia_proxy.api.v2.controllers import load_balancer
from octavia_proxy.tests.unit.api.controllers import base


class TestLoadBalancerController(base.TestCase):

    def setUp(self):
        super().setUp()

    def test_basic(self):
        controller = load_balancer.LoadBalancersController
        self.assertEqual(
            controller.RBAC_TYPE,
            'os_load-balancer_api:loadbalancer:'
        )
        self.assertEqual(getattr(controller, 'get_one').exposed, True)
        self.assertEqual(getattr(controller, 'get_all').exposed, True)
        self.assertEqual(getattr(controller, 'post').exposed, True)
        self.assertEqual(getattr(controller, 'put').exposed, True)
        self.assertEqual(getattr(controller, 'delete').exposed, True)
        self.assertIsNotNone(getattr(controller, '_get_provider'))
        self.assertIsNotNone(getattr(controller, '_lookup'))
        self.assertIsNotNone(getattr(controller, '_validate_flavor'))
        self.assertIsNotNone(getattr(controller, '_graph_create'))
        self.assertIsNotNone(
            getattr(
                controller,
                '_validate_network_and_fill_or_validate_subnet'
            ))
        self.assertIsNotNone(
            getattr(
                controller,
                '_validate_vip_request_object'
            ))
        self.assertIsNotNone(
            getattr(
                controller,
                '_validate_availability_zone'
            ))
