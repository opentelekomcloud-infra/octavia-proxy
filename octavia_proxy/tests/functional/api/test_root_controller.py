# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from octavia_proxy.tests.functional import base
import pecan.testing

from octavia_proxy.api import config as pconfig


class TestRootController(base.TestCase):
    def get(self, app, path, params=None, headers=None, status=200,
            expect_errors=False):
        response = app.get(
            path, params=params, headers=headers, status=status,
            expect_errors=expect_errors)
        return response

    def _get_versions_with_config(self):
        # Note: we need to set argv=() to stop the wsgi setup_app from
        # pulling in the testing tool sys.argv
        app = pecan.testing.load_test_app({'app': pconfig.app,
                                           'wsme': pconfig.wsme}, argv=())
        return self.get(app=app, path='/').json.get('versions', None)

    def test_api_versions(self):
        versions = self._get_versions_with_config()
        version_ids = tuple(v.get('id') for v in versions)
        self.assertIn('v2.0', version_ids)
