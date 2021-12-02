#    Copyright 2014 Rackspace
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

from oslo_utils import uuidutils

from octavia_proxy.common import constants
from octavia_proxy.tests.functional.api.v2 import base


class TestLoadBalancer(base.BaseAPITest):
    root_tag = 'loadbalancer'
    root_tag_list = 'loadbalancers'
    root_tag_links = 'loadbalancers_links'
    api_lb = None

    @classmethod
    def tearDownClass(cls):
        pass

    def _assert_request_matches_response(self, req, resp, **optionals):
        self.assertTrue(uuidutils.is_uuid_like(resp.get('id')))
        req_name = req.get('name')
        req_description = req.get('description')
        if not req_name:
            self.assertEqual('', resp.get('name'))
        else:
            self.assertEqual(req.get('name'), resp.get('name'))
        if not req_description:
            self.assertEqual(None, resp.get('description'))
        else:
            self.assertEqual(req.get('description'), resp.get('description'))
        self.assertEqual(constants.ACTIVE,
                         resp.get('provisioning_status'))
        self.assertEqual(constants.ONLINE, resp.get('operating_status'))
        self.assertEqual(req.get('admin_state_up', True),
                         resp.get('admin_state_up'))
        self.assertIsNotNone(resp.get('created_at'))
        self.assertIsNotNone(resp.get('updated_at'))
        for key, value in optionals.items():
            self.assertEqual(value, req.get(key))
        if req.get('tags'):
            self.assertEqual(req.get('tags'),
                             resp.get('tags'))

    def test_create_without_project_id(self, **optionals):
        lb_json = {'name': 'test1',
                   'vip_subnet_id': self._network['subnet_id']
                   }
        lb_json.update(optionals)
        body = self._build_body(lb_json)
        response = self.post(self.LBS_PATH, body)
        self.api_lb = response.json.get(self.root_tag)
        self._assert_request_matches_response(lb_json, self.api_lb)
        self.delete(self.LB_PATH.format(lb_id=self.api_lb.get('id')))

    def test_create_v2_0_with_project_id(self, **optionals):
        lb_json = {'name': 'test2',
                   'vip_subnet_id': self._network['subnet_id'],
                   'project_id': self.project_id
                   }
        lb_json.update(optionals)
        body = self._build_body(lb_json)
        response = self.post(self.LBS_PATH, body, use_v2_0=True)
        self.api_lb = response.json.get(self.root_tag)
        self._assert_request_matches_response(lb_json, self.api_lb)
        self.delete(self.LB_PATH.format(lb_id=self.api_lb.get('id')))

    def test_create_with_tags(self, **optionals):
        lb_json = {'name': 'test3',
                   'vip_subnet_id': self._network['subnet_id'],
                   'tags': ['test_tag1', 'test_tag2']
                   }
        lb_json.update(optionals)
        body = self._build_body(lb_json)
        response = self.post(self.LBS_PATH, body)
        self.api_lb = response.json.get(self.root_tag)
        self._assert_request_matches_response(lb_json, self.api_lb)
        self.delete(self.LB_PATH.format(lb_id=self.api_lb.get('id')))

    def test_complex_create_v2_0(self, **optionals):
        lb_json = {'name': 'test4',
                   'vip_subnet_id': self._network['subnet_id'],
                   'project_id': self.project_id,
                   "listeners": [{"name": "listener-4",
                                  "protocol": "HTTP",
                                  "protocol_port": "483",
                                 "default_pool": {"name": "default-pool-4",
                                                  "lb_algorithm":
                                                      "ROUND_ROBIN",
                                                  "protocol": "HTTP"},
                                  "l7policies": [{"name": "policy-4",
                                                  "rules": [{
                                                      "compare_type":
                                                          "EQUAL_TO",
                                                      "type": "PATH",
                                                      "value": "/bbb.html"}],
                                                  "action": "REDIRECT_TO_POOL",
                                                  "redirect_pool":
                                                      {"name": "pool-4"}}]}],
                   "pools": [{"name": "pool-4",
                              "lb_algorithm": "ROUND_ROBIN",
                              "protocol": "HTTP",
                              "healthmonitor": {"type": "HTTP", "delay": "3",
                                                "max_retries": 2,
                                                "timeout": 1},
                              "members": [{"address": "192.168.115.184",
                                           "protocol_port": "80"}]
                              }]
                   }
        lb_json.update(optionals)
        body = self._build_body(lb_json)
        response = self.post(self.LBS_PATH, body, use_v2_0=True)
        self.api_lb = response.json.get(self.root_tag)
        listeners = self.api_lb['listeners']
        pools = self.api_lb['pools']
        hm = pools[0]['healthmonitor']
        default_pool = listeners[0]["default_pool_id"]
        members = pools[0]['members']
        self.assertTrue(listeners)
        self.assertTrue(pools)
        self.assertTrue(hm)
        self.assertTrue(default_pool)
        self.assertTrue(members)
        self.delete(self.LB_PATH.format(lb_id=self.api_lb.get('id')),
                    params={'cascade': True})

    def test_create_get_all_delete(self):
        lb = self.create_load_balancer(
            self._network['subnet_id'], name='lb'
        ).get(self.root_tag)
        lbs = self.get(self.LBS_PATH).json.get(self.root_tag_list)
        # One lb already created according setUp() in base.py
        self.assertIsInstance(lbs, list)
        self.assertEqual(2, len(lbs))
        self.delete(self.LB_PATH.format(lb_id=lb.get('id')))

    def test_create_without_vip(self):
        lb_json = {'name': 'test1',
                   'project_id': self.project_id}
        body = self._build_body(lb_json)
        response = self.post(self.LBS_PATH, body, status=400)
        err_msg = ('Validation failure: VIP must contain one of: '
                   'vip_network_id, vip_subnet_id.')
        self.assertIn(err_msg, response.json.get('faultstring'))

    def test_create_with_empty_vip(self):
        lb_json = {'vip_subnet_id': '',
                   'project_id': self.project_id}
        body = self._build_body(lb_json)
        response = self.post(self.LBS_PATH, body, status=400)
        err_msg = ("Invalid input for field/attribute vip_subnet_id. "
                   "Value: ''. Value should be UUID format")
        self.assertEqual(err_msg, response.json.get('faultstring'))

    def test_create_with_invalid_vip_subnet(self):
        subnet_id = uuidutils.generate_uuid()
        lb_json = {'vip_subnet_id': subnet_id,
                   'project_id': self.project_id}
        body = self._build_body(lb_json)
        response = self.post(self.LBS_PATH, body, status=400)
        err_msg = 'Subnet {} not found.'.format(subnet_id)
        self.assertIn(err_msg, response.json.get('faultstring'))

    def test_create_with_long_name(self):
        lb_json = {'name': 'n' * 256,
                   'vip_subnet_id': self._network['subnet_id'],
                   'project_id': self.project_id}
        response = self.post(self.LBS_PATH, self._build_body(lb_json),
                             status=400)
        self.assertIn('Invalid input for field/attribute name',
                      response.json.get('faultstring'))

    def test_create_with_long_description(self):
        lb_json = {'description': 'n' * 256,
                   'vip_subnet_id': self._network['subnet_id'],
                   'project_id': self.project_id}
        response = self.post(self.LBS_PATH, self._build_body(lb_json),
                             status=400)
        self.assertIn('Invalid input for field/attribute description',
                      response.json.get('faultstring'))

    def test_create_with_nonuuid_vip_attributes(self):
        lb_json = {'vip_subnet_id': 'HI',
                   'project_id': self.project_id}
        response = self.post(self.LBS_PATH, self._build_body(lb_json),
                             status=400)
        self.assertIn('Invalid input for field/attribute vip_subnet_id',
                      response.json.get('faultstring'))
