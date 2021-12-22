from wsme import types as wtypes

from octavia_proxy.api.v2.controllers import BaseV2Controller
from octavia_proxy.api.v2.types import (
    load_balancer as lb_types,
    listener as listener_types,
    pool as pool_types,
    member as member_types,
    health_monitor as hm_types,
    l7policy as l7policy_types,
    l7rule as l7rule_types
)
from octavia_proxy.tests.unit import base


class TestControlerFilterFields(base.TestCase):
    EXAMPLE_LB = {
        'id': '70d638f5-29ba-443a-ba76-4277eb420292',
        'name': 'test-lb',
        'vip_subnet_id': '70d638f5-29ba-443a-ba76-4277eb420292',
        'provisioning_status': 'ACTIVE',
    }

    EXAMPLE_LISTENER = {
        'id': '76d638f5-29ba-443a-ba76-4277eb420292',
        'name': 'test-listener',
        'protocol': 'TCP',
        'protocol_port': '483',
        'provisioning_status': 'ACTIVE',
        'loadbalancer_id': '90d638f5-29ba-443a-ba76-4277eb420292'
    }

    EXAMPLE_POOL = {
        'id': '12d638f5-29ba-443a-ba76-4277eb420292',
        'name': 'test-pool',
        'lb_algorithm': 'ROUND_ROBIN'
    }

    EXAMPLE_MEMBER = {
        'id': '45d638f5-29ba-443a-ba76-4277eb420292',
        'name': 'test-member',
        'protocol': 'TCP',
        'lb_algorithm': 'ROUND_ROBIN'
    }

    EXAMPLE_HM = {
        'id': '45d638f5-29ba-443a-ba76-4277eb420292',
        'name': 'test-hm',
        'delay': '56',
        'max_retries': '5',
        'pool_id': '98d638f5-29ba-443a-ba76-4277eb420292',
        'type': 'HTTP'
    }

    EXAMPLE_L7POLICY = {
        'id': '45d638f5-29ba-443a-ba76-4277eb420292',
        'type': 'HOST_NAME',
        'compare_type': '76d638f5-29ba-443a-ba76-4277eb420292',
        'action': 'REDIRECT_TO_LISTENER'
    }

    EXAMPLE_L7RULE = {
        'id': '12d638f5-29ba-443a-ba76-4277eb420292',
        'type': 'PATH',
        'compare_type': 'EQUAL_TO',
        'value': '/bbb.html'
    }

    LB_RESPONSE_TYPE_PROPERTIES = [
        'id', 'name', 'description',
        'provisioning_status', 'operating_status',
        'admin_state_up', 'project_id',
        'created_at',
        'updated_at', 'vip_address', 'vip_port_id',
        'vip_subnet_id', 'vip_network_id',
        'listeners',
        'pools', 'provider', 'flavor_id',
        'vip_qos_policy_id', 'tags',
        'availability_zone'
    ]

    LSNR_RESPONSE_TYPE_PROPERTIES = [
        'id', 'name', 'description',
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
        'tls_versions', 'tags', 'alpn_protocols'
    ]

    POOL_RESPONSE_TYPE_PROPERTIES = [
        'id', 'name', 'description',
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
        'tls_versions', 'alpn_protocols'
    ]

    MEMBER_RESPONSE_TYPE_PROPERTIES = [
        'id', 'name', 'operating_status',
        'provisioning_status', 'admin_state_up',
        'address', 'protocol_port', 'weight',
        'backup', 'subnet_id', 'project_id',
        'created_at', 'updated_at',
        'monitor_address', 'monitor_port',
        'tags'
    ]

    HM_RESPONSE_TYPE_PROPERTIES = [
        'id', 'name', 'type', 'delay', 'timeout',
        'max_retries', 'max_retries_down',
        'http_method', 'url_path', 'expected_codes',
        'admin_state_up', 'project_id', 'pools',
        'provisioning_status', 'operating_status',
        'created_at', 'updated_at', 'tags',
        'http_version', 'domain_name'
    ]

    L7POLICY_RESPONSE_TYPE_PROPERTIES = [
        'id', 'name', 'description',
        'provisioning_status',
        'operating_status',
        'admin_state_up',
        'project_id', 'action', 'listener_id',
        'redirect_pool_id', 'redirect_url',
        'redirect_prefix', 'position',
        'rules', 'created_at', 'updated_at',
        'tags', 'redirect_http_code'
    ]

    L7RULE_RESPONSE_TYPE_PROPERTIES = [
        'id', 'type', 'compare_type', 'key',
        'value', 'invert',
        'provisioning_status',
        'operating_status', 'created_at',
        'updated_at', 'project_id',
        'admin_state_up', 'tags'
    ]

    def setUp(self):
        super().setUp()
        self.controller = BaseV2Controller()
        self.fields = ['id', 'name']
        self.lb_response = lb_types.LoadBalancerResponse(**self.EXAMPLE_LB)
        self.lsnr_response = listener_types.ListenerResponse(
            **self.EXAMPLE_LISTENER
        )
        self.pool_response = pool_types.PoolResponse(
            **self.EXAMPLE_POOL
        )
        self.member_response = member_types.MemberResponse(
            **self.EXAMPLE_MEMBER
        )
        self.hm_response = hm_types.HealthMonitorResponse(
            **self.EXAMPLE_HM
        )
        self.l7policy_response = l7policy_types.L7PolicyResponse(
            **self.EXAMPLE_L7POLICY
        )
        self.l7rule_response = l7rule_types.L7RuleResponse(
            **self.EXAMPLE_L7RULE
        )

    def _assert_only_filtered_fields_present(
            self, list_objects, fields, type_properties
    ):
        for object in list_objects:
            for property in type_properties:
                if property not in fields:
                    self.assertIsInstance(
                        getattr(object, property),
                        wtypes.UnsetType
                    )

    def test_filter_fields_loadbalancer(self):
        lb_objects = [self.lb_response]
        result = self.controller._filter_fields(lb_objects, self.fields)
        self._assert_only_filtered_fields_present(
            result, self.fields, self.LB_RESPONSE_TYPE_PROPERTIES
        )

    def test_filter_fields_listener(self):
        lsnr_objects = [self.lsnr_response]
        result = self.controller._filter_fields(lsnr_objects, self.fields)
        self._assert_only_filtered_fields_present(
            result, self.fields, self.LSNR_RESPONSE_TYPE_PROPERTIES
        )

    def test_filter_fields_pool(self):
        pool_objects = [self.pool_response]
        result = self.controller._filter_fields(pool_objects, self.fields)
        self._assert_only_filtered_fields_present(
            result, self.fields, self.POOL_RESPONSE_TYPE_PROPERTIES
        )

    def test_filter_fields_member(self):
        member_objects = [self.member_response]
        result = self.controller._filter_fields(member_objects, self.fields)
        self._assert_only_filtered_fields_present(
            result, self.fields, self.MEMBER_RESPONSE_TYPE_PROPERTIES
        )

    def test_filter_fields_hm(self):
        hm_objects = [self.hm_response]
        result = self.controller._filter_fields(hm_objects, self.fields)
        self._assert_only_filtered_fields_present(
            result, self.fields, self.HM_RESPONSE_TYPE_PROPERTIES
        )

    def test_filter_fields_l7policy(self):
        l7policy_objects = [self.l7policy_response]
        result = self.controller._filter_fields(l7policy_objects, self.fields)
        self._assert_only_filtered_fields_present(
            result, self.fields, self.L7POLICY_RESPONSE_TYPE_PROPERTIES
        )
