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

from oslo_utils import uuidutils

from octavia_proxy.common import constants
from octavia_proxy.tests.functional import base
import pecan.testing

from octavia_proxy.api import config as pconfig

_network = None
_sdk = None


class BaseAPITestV3(base.TestCase):

    BASE_PATH = '/v3'

    # /elb/flavors
    FLAVORS_PATH = '/elb/flavors'
    FLAVOR_PATH = FLAVORS_PATH + '/{flavor_id}'

    # /elb/availabilityzones
    AZS_PATH = '/elb/availability-zones'
    AZ_PATH = AZS_PATH + '/{az_name}'

    # /elb/loadbalancers
    LBS_PATH = '/elb/loadbalancers'
    LB_PATH = LBS_PATH + '/{lb_id}'
    LB_STATUS_PATH = LB_PATH + '/statuses'

    # /elb/listeners/
    LISTENERS_PATH = '/elb/listeners'
    LISTENER_PATH = LISTENERS_PATH + '/{listener_id}'

    # /elb/pools
    POOLS_PATH = '/elb/pools'
    POOL_PATH = POOLS_PATH + '/{pool_id}'

    # /elb/pools/{pool_id}/members
    MEMBERS_PATH = POOL_PATH + '/members'
    MEMBER_PATH = MEMBERS_PATH + '/{member_id}'

    # /elb/healthmonitors
    HMS_PATH = '/elb/healthmonitors'
    HM_PATH = HMS_PATH + '/{healthmonitor_id}'

    # /elb/l7policies
    L7POLICIES_PATH = '/elb/l7policies'
    L7POLICY_PATH = L7POLICIES_PATH + '/{l7policy_id}'
    L7RULES_PATH = L7POLICY_PATH + '/rules'
    L7RULE_PATH = L7RULES_PATH + '/{l7rule_id}'

    NOT_AUTHORIZED_BODY = {
        'debuginfo': None, 'faultcode': 'Client',
        'faultstring': 'Policy does not allow this request to be performed.'}

    def setUp(self):
        super().setUp()
        self._sdk_connection = self._get_sdk_connection()
        self._token = self._get_token()
        self._network = self._create_network()
        self.project_id = self._get_project_id()
        self.vip_subnet_id = None
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

    def _get_sdk_connection(self):
        global _sdk
        if not _sdk:
            _sdk = openstack.connect()
        return _sdk

    def _create_network(self):
        global _network
        cidr = '192.168.0.0/16'
        ipv4 = 4
        uuid_v4 = uuidutils.generate_uuid()
        router_name = 'octavia-proxy-test-router-' + uuid_v4
        net_name = 'octavia-proxy-test-net-' + uuid_v4
        subnet_name = 'octavia-proxy-test-subnet-' + uuid_v4

        if not _network:
            if not self._sdk_connection:
                self._sdk_connection = self._get_sdk_connection()
            network = self._sdk_connection.network.create_network(
                name=net_name)
            net_id = network.id
            subnet = self._sdk_connection.network.create_subnet(
                name=subnet_name,
                ip_version=ipv4,
                network_id=net_id,
                cidr=cidr
            )
            subnet_id = subnet.id

            router = self._sdk_connection.network.create_router(
                name=router_name)
            router_id = router.id
            router.add_interface(
                self._sdk_connection.network,
                subnet_id=subnet_id
            )
            _network = {
                'router_id': router_id,
                'subnet_id': subnet_id,
                'network_id': net_id
            }
        return _network

    def _destroy_network(self, params: dict):
        router_id = params.get('router_id')
        subnet_id = params.get('subnet_id')
        network_id = params.get('network_id')
        router = self._sdk_connection.network.get_router(router_id)

        router.remove_interface(
            self._sdk_connection.network,
            subnet_id=subnet_id
        )
        self._sdk_connection.network.delete_router(
            router_id,
            ignore_missing=False
        )
        self._sdk_connection.network.delete_subnet(
            subnet_id,
            ignore_missing=False
        )
        self._sdk_connection.network.delete_network(
            network_id,
            ignore_missing=False
        )

    def _cleanup_lb(self):
        try:
            self.delete(self.LB_PATH.format(lb_id=self.api_lb.get('id')))
        except Exception:
            pass

    def _cleanup_network(self):
        try:
            self._destroy_network(self._network)
        except Exception:
            pass

    def _cleanup(self):
        try:
            self._cleanup_lb()
            self._cleanup_network()
        except Exception:
            pass

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

    def _build_body(self, json):
        return {self.root_tag: json}

    def _get_token(self):
        if not self._sdk_connection:
            self._sdk_connection = self._get_sdk_connection()
        self._token = self._sdk_connection.auth_token
        return self._token

    def _get_project_id(self):
        if not self._sdk_connection:
            self._sdk_connection = self._get_sdk_connection()
        self.project_id = self._sdk_connection.current_project_id
        return self.project_id

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

    def post(self, path, body, headers=None, status=201, expect_errors=False,
             authorized=True):
        headers = headers or {}
        full_path = self._get_full_path(path)
        if authorized:
            if not headers:
                headers = dict()
            headers['X-Auth-Token'] = self._get_token()
        response = self.app.post_json(full_path,
                                      params=body,
                                      headers=headers,
                                      status=status,
                                      expect_errors=expect_errors)
        return response

    def delete(self, path, headers=None, params=None, status=204,
               expect_errors=False, authorized=True):
        headers = headers or {}
        params = params or {}
        full_path = self._get_full_path(path)
        param_string = ""
        for k, v in params.items():
            param_string += "{key}={value}&".format(key=k, value=v)
        if param_string:
            full_path = "{path}?{params}".format(
                path=full_path, params=param_string.rstrip("&"))
        if authorized:
            if not headers:
                headers = dict()
            headers['X-Auth-Token'] = self._get_token()
        response = self.app.delete(full_path,
                                   headers=headers,
                                   status=status,
                                   expect_errors=expect_errors)
        return response
