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

from octavia_lib.api.drivers import exceptions as lib_exceptions

from octavia_proxy.api.drivers import utils
from octavia_proxy.common import exceptions
from octavia_proxy.tests.unit import base
from oslo_log import log as logging


class TestUtils(base.TestCase):
    def setUp(self):
        super().setUp()

    def test_call_provider(self):
        mock_driver_method = mock.MagicMock()

        # Test happy path
        utils.call_provider("provider_name", mock_driver_method,
                            "arg1", foo="arg2")
        mock_driver_method.assert_called_with("arg1", foo="arg2")

        # Test driver raising DriverError
        mock_driver_method.side_effect = lib_exceptions.DriverError
        self.assertRaises(exceptions.ProviderDriverError,
                          utils.call_provider, "provider_name",
                          mock_driver_method)

        # Test driver raising different types of NotImplementedError
        mock_driver_method.side_effect = NotImplementedError
        self.assertRaises(exceptions.ProviderNotImplementedError,
                          utils.call_provider, "provider_name",
                          mock_driver_method)
        mock_driver_method.side_effect = lib_exceptions.NotImplementedError
        self.assertRaises(exceptions.ProviderNotImplementedError,
                          utils.call_provider, "provider_name",
                          mock_driver_method)

        # Test driver raising UnsupportedOptionError
        mock_driver_method.side_effect = (
            lib_exceptions.UnsupportedOptionError)
        self.assertRaises(exceptions.ProviderUnsupportedOptionError,
                          utils.call_provider, "provider_name",
                          mock_driver_method)

        # Test driver raising ProviderDriverError
        mock_driver_method.side_effect = Exception
        self.assertLogs(logging.getLogger(__name__), 'exception')
