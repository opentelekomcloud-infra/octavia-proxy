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

_network = None
_sdk = None
_lb = None


def _destroy_lb(_lb: dict):
    if _lb.get('provider') == 'elbv2':
        for listener in _sdk.elb.listeners():
            if any(lb['id'] == _lb.get('id')
                   for lb in listener.load_balancers):
                for l7policy in _sdk.elb.l7_policies():
                    if l7policy.get('listener_id') == listener.get('id'):
                        _sdk.elb.delete_l7_policy(l7policy)
                _sdk.elb.delete_listener(listener)
        for pool in _sdk.elb.pools(loadbalancer_id=_lb.get('id')):
            for member in _sdk.elb.members(pool):
                _sdk.elb.delete_member(member, pool)
            for hm in _sdk.elb.health_monitors():
                if any(pl['id'] == pool.get('id') for pl in hm.pools):
                    _sdk.elb.delete_health_monitor(hm)
            _sdk.elb.delete_pool(pool)
        _sdk.elb.delete_load_balancer(_lb.get('id'))
    else:
        # TODO implement cleanup for elbv3 _sdk.vlb.delete_
        pass


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
        self._sdk_connection = self._get_sdk_connection()
        self._token = self._get_token()
        self._network = self._create_network()
        self.project_id = self._get_project_id()
        self.vip_subnet_id = None
        self.conf.config(
            group='api_settings',
            auth_strategy=constants.KEYSTONE_EXT)
        self.conf.config(
            group='validatetoken',
            www_authenticate_uri='https://iam.eu-de.otc.t-systems.com')
        self.app = self._make_app()
        self._lb = self._create_lb()

        def reset_pecan():
            pecan.set_config({}, overwrite=True)

        self.addCleanup(reset_pecan)

    def tearDown(self):
        if self._sdk_connection:
            self._sdk_connection.close()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        try:
            _destroy_lb(_lb)
        except Exception:
            pass

    def _get_sdk_connection(self):
        global _sdk
        if not _sdk:
            _sdk = openstack.connect()
        return _sdk

    def _create_network(self):
        global _network
        cidr = '192.168.0.0/16'
        ipv4 = 4
        router_name = 'octavia-proxy-test-router'
        net_name = 'octavia-proxy-test-net'
        subnet_name = 'octavia-proxy-test-subnet'

        if not _network:
            if not self._sdk_connection:
                self._sdk_connection = self._get_sdk_connection()
            network = self._sdk_connection.network.find_network(net_name)
            if not network:
                network = self._sdk_connection.network.create_network(
                    name=net_name)
            net_id = network.id
            subnet = self._sdk_connection.network.find_subnet(subnet_name)
            if not subnet:
                subnet = self._sdk_connection.network.create_subnet(
                    name=subnet_name,
                    ip_version=ipv4,
                    network_id=net_id,
                    cidr=cidr
                )
            subnet_id = subnet.id

            router = self._sdk_connection.network.find_router(router_name)
            if not router:
                router = self._sdk_connection.network.create_router(
                    name=router_name)
                router.add_interface(
                    self._sdk_connection.network,
                    subnet_id=subnet_id)
            router_id = router.id

            _network = {
                'router_id': router_id,
                'subnet_id': subnet_id,
                'network_id': net_id
            }
        return _network

    def _create_lb(self):
        global _lb
        if not _lb:
            body = {'loadbalancer': {
                    'name': 'lb-common',
                    'vip_subnet_id': self._network['subnet_id'],
                    'project_id': self.project_id}
                    }
            response = self.post(self.LBS_PATH, body)
            _lb = response.json.get('loadbalancer')
        return _lb

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

    def get_lb_id(self):
        return _lb.get('id')

    def post(self, path, body, headers=None, status=201, expect_errors=False,
             use_v2_0=False, authorized=True):
        headers = headers or {}
        if use_v2_0:
            full_path = self._get_full_path_v2_0(path)
        else:
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

    def create_load_balancer(self, vip_subnet_id,
                             **optionals):
        req_dict = {'vip_subnet_id': vip_subnet_id,
                    'project_id': self.project_id}
        req_dict.update(optionals)
        body = {'loadbalancer': req_dict}
        response = self.post(self.LBS_PATH, body)
        return response.json

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

    def create_listener(self, protocol, protocol_port, lb_id,
                        status=None, **optionals):
        req_dict = {'protocol': protocol, 'protocol_port': protocol_port,
                    'loadbalancer_id': lb_id}
        req_dict.update(optionals)
        path = self.LISTENERS_PATH
        body = {'listener': req_dict}
        status = {'status': status} if status else {}
        response = self.post(path, body, **status)
        return response.json

    def create_pool(self, lb_id, protocol, lb_algorithm,
                    status=None, **optionals):
        req_dict = {'loadbalancer_id': lb_id, 'protocol': protocol,
                    'lb_algorithm': lb_algorithm}
        req_dict.update(optionals)
        body = {'pool': req_dict}
        path = self.POOLS_PATH
        status = {'status': status} if status else {}
        response = self.post(path, body, **status)
        return response.json

    def create_member(self, pool_id, address, protocol_port,
                      status=None, **optionals):
        req_dict = {'address': address, 'protocol_port': protocol_port}
        req_dict.update(optionals)
        body = {'member': req_dict}
        path = self.MEMBERS_PATH.format(pool_id=pool_id)
        status = {'status': status} if status else {}
        response = self.post(path, body, **status)
        return response.json

    def create_health_monitor(self, pool_id, type, delay, timeout,
                              max_retries_down, max_retries,
                              status=None, **optionals):
        req_dict = {'pool_id': pool_id,
                    'type': type,
                    'delay': delay,
                    'timeout': timeout,
                    'max_retries_down': max_retries_down,
                    'max_retries': max_retries}
        req_dict.update(optionals)
        body = {'healthmonitor': req_dict}
        path = self.HMS_PATH
        status = {'status': status} if status else {}
        response = self.post(path, body, **status)
        return response.json

    def create_l7policy(self, listener_id, action, status=None, **optionals):
        req_dict = {'listener_id': listener_id, 'action': action}
        req_dict.update(optionals)
        body = {'l7policy': req_dict}
        path = self.L7POLICIES_PATH
        status = {'status': status} if status else {}
        response = self.post(path, body, **status)
        return response.json

    def create_l7rule(self, l7policy_id, type, compare_type,
                      value, status=None, **optionals):
        req_dict = {'type': type, 'compare_type': compare_type, 'value': value}
        req_dict.update(optionals)
        body = {'rule': req_dict}
        path = self.L7RULES_PATH.format(l7policy_id=l7policy_id)
        status = {'status': status} if status else {}
        response = self.post(path, body, **status)
        return response.json
