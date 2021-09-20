from wsme import types as wtypes
from octavia_proxy.api.v2.controllers import BaseV2Controller
from octavia_proxy.api.v2.types import (load_balancer as lb_types,
                                        listener as listener_types,
                                        pool as pool_types,
                                        member as member_types)
from octavia_proxy.tests.unit import base


class TestElbv2Controler(base.TestCase):

    EXAMPLE_LB = {'id': '70d638f5-29ba-443a-ba76-4277eb420292',
                  'name': 'ex_name', 'project_id': '7823987',
                  'vip_address': '192.168.0.10',
                  'provisioning_status': 'ACTIVE',
                  'operating_status': 'ACTIVE', 'provider': 'elbv2'}

    EXAMPLE_LSNR = {'id': '70d638f5-29ba-443a-ba76-4277eb420292',
                    'name': 'ex_name', 'project_id': '7823987',
                    'provisioning_status': 'ACTIVE'}

    EXAMPLE_POOL = {'id': '70d638f5-29ba-443a-ba76-4277eb420292',
                    'name': 'ex_name', 'project_id': '7823987',
                    'provisioning_status': 'ACTIVE'}

    EXAMPLE_MEMBER = {'id': '70d638f5-29ba-443a-ba76-4277eb420292',
                      'name': 'ex_name', 'project_id': '7823987',
                      'provisioning_status': 'ACTIVE'}

    LB_RESPONSE_TYPE_PROPERTIES = ['id', 'name', 'description',
                                   'provisioning_status', 'operating_status',
                                   'admin_state_up', 'project_id',
                                   'created_at',
                                   'updated_at', 'vip_address', 'vip_port_id',
                                   'vip_subnet_id', 'vip_network_id',
                                   'listeners',
                                   'pools', 'provider', 'flavor_id',
                                   'vip_qos_policy_id', 'tags',
                                   'availability_zone']

    LSNR_RESPONSE_TYPE_PROPERTIES = ['id', 'name', 'description',
                                     'provisioning_status', 'operating_status',
                                     'admin_state_up', 'protocol',
                                     'protocol_port', 'project_id',
                                     'connection_limit',
                                     'default_tls_container_ref',
                                     'sni_container_refs', 'default_pool_id',
                                     'l7policies', 'insert_headers',
                                     'created_at', 'updated_at',
                                     'loadbalancers',
                                     'timeout_client_data',
                                     'timeout_member_connect',
                                     'timeout_member_data',
                                     'timeout_tcp_inspect',
                                     'client_ca_tls_container_ref',
                                     'client_authentication',
                                     'client_crl_container_ref',
                                     'allowed_cidrs', 'tls_ciphers',
                                     'tls_versions', 'tags', 'alpn_protocols']

    POOL_RESPONSE_TYPE_PROPERTIES = ['id', 'name', 'description',
                                     'provisioning_status',
                                     'operating_status',
                                     'admin_state_up', 'protocol',
                                     'lb_algorithm', 'session_persistence',
                                     'project_id', 'loadbalancers',
                                     'listeners', 'created_at', 'updated_at',
                                     'healthmonitor_id', 'members', 'tags',
                                     'tls_container_ref',
                                     'ca_tls_container_ref',
                                     'crl_container_ref',
                                     'tls_enabled', 'tls_ciphers',
                                     'tls_versions', 'alpn_protocols']

    MEMBER_RESPONSE_TYPE_PROPERTIES = ['id', 'name', 'operating_status',
                                       'provisioning_status', 'admin_state_up',
                                       'address', 'protocol_port', 'weight',
                                       'backup', 'subnet_id', 'project_id',
                                       'created_at', 'updated_at',
                                       'monitor_address', 'monitor_port',
                                       'tags']

    def setUp(self):
        super().setUp()
        self.controller = BaseV2Controller()
        self.lb_response = lb_types.LoadBalancerResponse(**self.EXAMPLE_LB)
        self.lsnr_response = listener_types.ListenerResponse(
            **self.EXAMPLE_LSNR)
        self.pool_response = pool_types.PoolResponse(
            **self.EXAMPLE_POOL)
        self.member_response = member_types.MemberResponse(
            **self.EXAMPLE_MEMBER)

    def _assert_only_filtered_fields_present(self, list_objects, fields,
                                             type_properties):
        for object in list_objects:
            for property in type_properties:
                if property not in fields:
                    self.assertIsInstance(getattr(object, property),
                                          wtypes.UnsetType)

    def test_filter_fields_loadbalancer(self):
        lb_objects = [self.lb_response]
        fields = ['id', 'name']
        result = self.controller._filter_fields(lb_objects, fields)
        self._assert_only_filtered_fields_present(
            result, fields, self.LB_RESPONSE_TYPE_PROPERTIES)

    def test_filter_fields_listener(self):
        lsnr_objects = [self.lsnr_response]
        fields = ['id', 'name']
        result = self.controller._filter_fields(lsnr_objects, fields)
        self._assert_only_filtered_fields_present(
            result, fields, self.LSNR_RESPONSE_TYPE_PROPERTIES)

    def test_filter_fields_pool(self):
        pool_objects = [self.pool_response]
        fields = ['id', 'name']
        result = self.controller._filter_fields(pool_objects, fields)
        self._assert_only_filtered_fields_present(
            result, fields, self.POOL_RESPONSE_TYPE_PROPERTIES)

    def test_filter_fields_member(self):
        member_objects = [self.member_response]
        fields = ['id', 'name']
        result = self.controller._filter_fields(member_objects, fields)
        self._assert_only_filtered_fields_present(
            result, fields, self.MEMBER_RESPONSE_TYPE_PROPERTIES)
