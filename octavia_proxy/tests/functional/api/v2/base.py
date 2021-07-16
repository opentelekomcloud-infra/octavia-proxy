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

import openstack

from octavia_proxy.common import constants
from octavia_proxy.tests.functional import base
import pecan.testing

from octavia_proxy.api import config as pconfig


class BaseAPITest(base.TestCase):

    BASE_PATH = '/v2'
    BASE_PATH_v2_0 = '/v2.0'

    # /lbaas/flavors
    FLAVORS_PATH = '/flavors'
    FLAVOR_PATH = FLAVORS_PATH + '/{flavor_id}'

    # /lbaas/flavorprofiles
    FPS_PATH = '/flavorprofiles'
    FP_PATH = FPS_PATH + '/{fp_id}'

    # /lbaas/availabilityzones
    AZS_PATH = '/availabilityzones'
    AZ_PATH = AZS_PATH + '/{az_name}'

    # /lbaas/availabilityzoneprofiles
    AZPS_PATH = '/availabilityzoneprofiles'
    AZP_PATH = AZPS_PATH + '/{azp_id}'

    # /lbaas/loadbalancers
    LBS_PATH = '/lbaas/loadbalancers'
    LB_PATH = LBS_PATH + '/{lb_id}'
    LB_STATUS_PATH = LB_PATH + '/statuses'
    LB_STATS_PATH = LB_PATH + '/stats'

    # /lbaas/listeners/
    LISTENERS_PATH = '/lbaas/listeners'
    LISTENER_PATH = LISTENERS_PATH + '/{listener_id}'
    LISTENER_STATS_PATH = LISTENER_PATH + '/stats'

    # /lbaas/pools
    POOLS_PATH = '/lbaas/pools'
    POOL_PATH = POOLS_PATH + '/{pool_id}'

    # /lbaas/pools/{pool_id}/members
    MEMBERS_PATH = POOL_PATH + '/members'
    MEMBER_PATH = MEMBERS_PATH + '/{member_id}'

    # /lbaas/healthmonitors
    HMS_PATH = '/lbaas/healthmonitors'
    HM_PATH = HMS_PATH + '/{healthmonitor_id}'

    # /lbaas/l7policies
    L7POLICIES_PATH = '/lbaas/l7policies'
    L7POLICY_PATH = L7POLICIES_PATH + '/{l7policy_id}'
    L7RULES_PATH = L7POLICY_PATH + '/rules'
    L7RULE_PATH = L7RULES_PATH + '/{l7rule_id}'

    QUOTAS_PATH = '/lbaas/quotas'
    QUOTA_PATH = QUOTAS_PATH + '/{project_id}'
    QUOTA_DEFAULT_PATH = QUOTAS_PATH + '/{project_id}/default'

    PROVIDERS_PATH = '/lbaas/providers'
    FLAVOR_CAPABILITIES_PATH = (
        PROVIDERS_PATH + '/{provider}/flavor_capabilities')
    AVAILABILITY_ZONE_CAPABILITIES_PATH = (
        PROVIDERS_PATH + '/{provider}/availability_zone_capabilities')

    NOT_AUTHORIZED_BODY = {
        'debuginfo': None, 'faultcode': 'Client',
        'faultstring': 'Policy does not allow this request to be performed.'}

    def setUp(self):
        super().setUp()
        self._token = None
        self._sdk_connection = None
        self.project_id = None
        self.conf.config(
            group='api_settings',
            auth_strategy=constants.KEYSTONE_EXT)
        self.app = self._make_app()

        def reset_pecan():
            pecan.set_config({}, overwrite=True)

        self.addCleanup(reset_pecan)

    def tearDown(self):
        if self._sdk_connection:
            self._sdk_connection.close()
        super().tearDown()

    def _make_app(self):
        # Note: we need to set argv=() to stop the wsgi setup_app from
        # pulling in the testing tool sys.argv
        return pecan.testing.load_test_app(
            {
                'app': pconfig.app,
                'wsme': pconfig.wsme,
                'debug': True,
            }, argv=())

    def _get_full_path(self, path):
        return ''.join([self.BASE_PATH, path])

    def _get_full_path_v2_0(self, path):
        return ''.join([self.BASE_PATH_v2_0, path])

    def _build_body(self, json):
        return {self.root_tag: json}

    def _get_token(self):
        if not self._sdk_connection:
            self._sdk_connection = openstack.connect()
        if not self._token:
            self._token = self._sdk_connection.auth_token
        self.project_id = self._sdk_connection.current_project_id
        return self._token

    def get(self, path, params=None, headers=None, status=200,
            expect_errors=False, authorized=True):
        full_path = self._get_full_path(path)
        if authorized:
            if not headers:
                headers = dict()
            headers['X-Auth-Token'] = self._get_token()
        response = self.app.get(
            full_path,
            params=params,
            headers=headers,
            status=status,
            expect_errors=expect_errors
        )
        return response
