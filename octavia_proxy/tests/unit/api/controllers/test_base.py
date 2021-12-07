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

from octavia_proxy.api.v2.controllers import base as _b
from octavia_proxy.tests.unit.api.controllers import base


class TestBaseController(base.TestCase):

    def setUp(self):
        super().setUp()

    def test_basic(self):
        controller = _b.BaseController
        self.assertEqual(controller.RBAC_TYPE, None)
        self.assertIsNotNone(getattr(controller, 'find_load_balancer'))
        self.assertIsNotNone(getattr(controller, 'find_listener'))
        self.assertIsNotNone(getattr(controller, 'find_pool'))
        self.assertIsNotNone(getattr(controller, 'find_member'))
        self.assertIsNotNone(getattr(controller, 'find_health_monitor'))
        self.assertIsNotNone(getattr(controller, 'find_l7policy'))
        self.assertIsNotNone(getattr(controller, 'find_l7rule'))
        self.assertIsNotNone(getattr(controller, 'find_flavor'))
        self.assertIsNotNone(getattr(controller, '_convert_sdk_to_type'))
        self.assertIsNotNone(getattr(controller, '_validate_protocol'))
        self.assertIsNotNone(
            getattr(controller, '_is_only_specified_in_request')
        )
        self.assertIsNotNone(
            getattr(controller, '_validate_pool_request_for_tcp_udp')
        )
        self.assertIsNotNone(
            getattr(controller, '_validate_healthmonitor_request_for_udp')
        )
        self.assertIsNotNone(getattr(controller, '_auth_get_all'))
        self.assertIsNotNone(getattr(controller, '_auth_validate_action'))
        self.assertIsNotNone(getattr(controller, '_filter_fields'))
        self.assertIsNotNone(getattr(controller, '_get_attrs'))
