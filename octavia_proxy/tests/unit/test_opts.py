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

from octavia_proxy import opts
import octavia_proxy.tests.unit.base as base


class TestOpts(base.TestCase):

    def setUp(self):
        super().setUp()

    def test_list_opts(self):
        opts_list = opts.list_opts()[0]
        self.assertIn('DEFAULT', opts_list)
