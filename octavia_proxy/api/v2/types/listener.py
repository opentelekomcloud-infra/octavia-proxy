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
from dateutil import parser

from oslo_config import cfg
from wsme import types as wtypes
from octavia_proxy.api.common import types
from octavia_proxy.api.v2.types import l7policy
from octavia_proxy.api.v2.types import pool
from octavia_proxy.common import constants

CONF = cfg.CONF


class BaseListenerType(types.BaseType):
    _type_to_model_map = {
        'admin_state_up': 'enabled',
        'default_tls_container_ref': 'tls_certificate_id',
        'sni_container_refs': 'sni_containers',
        'client_ca_tls_container_ref': 'client_ca_tls_certificate_id',
        'client_crl_container_ref': 'client_crl_container_id'}
    _child_map = {}


class ListenerResponse(BaseListenerType):
    """Defines which attributes are to be shown on any response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    description = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    admin_state_up = wtypes.wsattr(bool)
    protocol = wtypes.wsattr(wtypes.text)
    protocol_port = wtypes.wsattr(wtypes.IntegerType())
    connection_limit = wtypes.wsattr(wtypes.IntegerType())
    default_tls_container_ref = wtypes.wsattr(wtypes.StringType())
    sni_container_refs = [wtypes.StringType()]
    project_id = wtypes.wsattr(wtypes.StringType())
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    l7policies = wtypes.wsattr([types.IdOnlyType])
    insert_headers = wtypes.wsattr(wtypes.DictType(str, str))
    created_at = wtypes.wsattr(wtypes.datetime.datetime)
    updated_at = wtypes.wsattr(wtypes.datetime.datetime)
    loadbalancers = wtypes.wsattr([types.IdOnlyType])
    timeout_client_data = wtypes.wsattr(wtypes.IntegerType())
    timeout_member_connect = wtypes.wsattr(wtypes.IntegerType())
    timeout_member_data = wtypes.wsattr(wtypes.IntegerType())
    timeout_tcp_inspect = wtypes.wsattr(wtypes.IntegerType())
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType()))
    client_ca_tls_container_ref = wtypes.StringType()
    client_authentication = wtypes.wsattr(wtypes.StringType())
    client_crl_container_ref = wtypes.wsattr(wtypes.StringType())
    allowed_cidrs = wtypes.wsattr([types.CidrType()])
    tls_ciphers = wtypes.StringType()
    tls_versions = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType()))
    alpn_protocols = wtypes.wsattr(wtypes.ArrayType(types.AlpnProtocolType()))

    @classmethod
    def from_data_model(cls, data_model, children=False):
        loadbalancers = data_model.get('loadbalancers', [])
        l7policies = data_model.get('l7policies', [])
        sni_container_refs = data_model.get('sni_container_refs', [])
        allowed_cidrs = data_model.get('allowed_cidrs', [])
        tls_versions = data_model.get('tls_versions', [])
        alpn_protocols = data_model.get('alpn_protocols', [])
        data_model['loadbalancers'] = []
        data_model['l7policies'] = []
        data_model['sni_container_refs'] = []
        data_model['allowed_cidrs'] = []
        data_model['tls_versions'] = []
        data_model['alpn_protocols'] = []
        listener = super(ListenerResponse, cls).from_data_model(
            data_model, children=children)

        if sni_container_refs:
            listener.sni_container_refs = [
                sni_c.tls_container_id for sni_c in sni_container_refs]
        else:
            listener.sni_container_refs = []
        if allowed_cidrs:
            listener.allowed_cidrs = [c.cidr for c in allowed_cidrs]
        else:
            listener.allowed_cidrs = []
        if cls._full_response():
            del listener.loadbalancers
            l7policy_type = l7policy.L7PolicyFullResponse
        else:
            listener.loadbalancers = [
                types.IdOnlyType.from_data_model(loadbalancers)]
            l7policy_type = types.IdOnlyType

        if l7policies:
            listener.l7policies = [
                l7policy_type.from_data_model(i) for i in l7policies]
        else:
            listener.l7policies = []

        listener.tls_versions = tls_versions
        listener.alpn_protocols = alpn_protocols
        return listener

    @classmethod
    def from_sdk_object(cls, sdk_entity, children=False):
        listener = cls()
        for key in [
            'id', 'name',
            'client_authentication', 'client_ca_tls_container_ref',
            'client_crl_container_ref', 'connection_limit', 'default_pool_id',
            'default_tls_container_ref', 'description', 'operation_status',
            'project_id', 'protocol', 'protocol_port', 'provisioning_status',
            'sni_container_refs', 'tags', 'timeout_client_data',
            'timeout_member_connect', 'timeout_member_data',
            'timeout_tcp_inspect', 'tls_ciphers'
        ]:
            if hasattr(sdk_entity, key):
                v = getattr(sdk_entity, key)
                if v:
                    setattr(listener, key, v)

        listener.admin_state_up = sdk_entity.is_admin_state_up
        for attr in ['created_at', 'updated_at']:
            setattr(listener, attr, parser.parse(sdk_entity[attr]))

        listener.allowed_cidrs = []
        listener.alpn_protocols = []
        try:
            headers = dict()
            for k, v in sdk_entity.insert_headers.items():
                headers[k] = str(v)
            listener.insert_headers = headers
        except (AttributeError):
            pass
        if sdk_entity.l7_policies:
            listener.l7policies = [
                types.IdOnlyType(id=i['id']) for i in sdk_entity.l7_policies
            ]
        listener.loadbalancers = [
            types.IdOnlyType(id=i['id']) for i in sdk_entity.load_balancers
        ]
        listener.tls_versions = []
        return listener

    def to_full_response(self, l7policies=None):
        full_response = ListenerFullResponse()

        for key in [
            'id', 'name',
            'client_authentication', 'client_ca_tls_container_ref',
            'client_crl_container_ref', 'connection_limit', 'default_pool_id',
            'default_tls_container_ref', 'description', 'operation_status',
            'project_id', 'protocol', 'protocol_port', 'provisioning_status',
            'sni_container_refs', 'tags',
            'timeout_client_data', 'timeout_member_connect',
            'timeout_member_data', 'timeout_tcp_inspect', 'tls_ciphers'
        ]:
            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(full_response, key, v)

        full_response.admin_state_up = self.admin_state_up
        full_response.allowed_cidrs = self.allowed_cidrs
        full_response.alpn_protocols = self.alpn_protocols
        full_response.insert_headers = self.insert_headers
        full_response.created_at = self.created_at
        full_response.updated_at = self.updated_at
        full_response.loadbalancers = self.loadbalancers
        full_response.tls_versions = self.tls_versions

        if l7policies:
            full_response.l7policies = l7policies
        return full_response


class ListenerFullResponse(ListenerResponse):
    @classmethod
    def _full_response(cls):
        return True

    l7policies = wtypes.wsattr([l7policy.L7PolicyFullResponse])


class ListenerRootResponse(types.BaseType):
    listener = wtypes.wsattr(ListenerResponse)


class ListenersRootResponse(types.BaseType):
    listeners = wtypes.wsattr([ListenerResponse])
    listeners_links = wtypes.wsattr([types.PageType])


class ListenerPOST(BaseListenerType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    protocol = wtypes.wsattr(wtypes.Enum(str, *constants.SUPPORTED_PROTOCOLS),
                             mandatory=True)
    protocol_port = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_PORT_NUMBER,
                           maximum=constants.MAX_PORT_NUMBER), mandatory=True)
    connection_limit = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_CONNECTION_LIMIT),
        default=constants.DEFAULT_CONNECTION_LIMIT)
    default_tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    sni_container_refs = [wtypes.StringType(max_length=255)]
    # TODO(johnsom) Remove after deprecation (R series)
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    default_pool = wtypes.wsattr(pool.PoolSingleCreate)
    l7policies = wtypes.wsattr([l7policy.L7PolicySingleCreate], default=None)
    insert_headers = wtypes.wsattr(
        wtypes.DictType(str, wtypes.StringType(max_length=255)))
    loadbalancer_id = wtypes.wsattr(wtypes.UuidType(), mandatory=True)
    timeout_client_data = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT),
        # default=CONF.haproxy_amphora.timeout_client_data
    )
    timeout_member_connect = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT),
        # default=CONF.haproxy_amphora.timeout_member_connect
    )
    timeout_member_data = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT),
        # default=CONF.haproxy_amphora.timeout_member_data
    )
    timeout_tcp_inspect = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT),
        # default=CONF.haproxy_amphora.timeout_tcp_inspect
    )
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    client_ca_tls_container_ref = wtypes.StringType(max_length=255)
    client_authentication = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_CLIENT_AUTH_MODES),
        default=constants.CLIENT_AUTH_NONE)
    client_crl_container_ref = wtypes.StringType(max_length=255)
    allowed_cidrs = wtypes.wsattr([types.CidrType()])
    tls_ciphers = wtypes.StringType(max_length=2048)
    tls_versions = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(
        max_length=32)))
    alpn_protocols = wtypes.wsattr(wtypes.ArrayType(types.AlpnProtocolType()))


class ListenerRootPOST(types.BaseType):
    listener = wtypes.wsattr(ListenerPOST)


class ListenerPUT(BaseListenerType):
    """Defines attributes that are acceptable of a PUT request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool)
    connection_limit = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_CONNECTION_LIMIT))
    default_tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    sni_container_refs = [wtypes.StringType(max_length=255)]
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    insert_headers = wtypes.wsattr(
        wtypes.DictType(str, wtypes.StringType(max_length=255)))
    timeout_client_data = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT))
    timeout_member_connect = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT))
    timeout_member_data = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT))
    timeout_tcp_inspect = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT))
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    client_ca_tls_container_ref = wtypes.StringType(max_length=255)
    client_authentication = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_CLIENT_AUTH_MODES))
    client_crl_container_ref = wtypes.StringType(max_length=255)
    allowed_cidrs = wtypes.wsattr([types.CidrType()])
    tls_ciphers = wtypes.StringType(max_length=2048)
    tls_versions = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(
        max_length=32)))
    alpn_protocols = wtypes.wsattr(wtypes.ArrayType(types.AlpnProtocolType()))


class ListenerRootPUT(types.BaseType):
    listener = wtypes.wsattr(ListenerPUT)


class ListenerSingleCreate(BaseListenerType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    protocol = wtypes.wsattr(wtypes.Enum(str, *constants.SUPPORTED_PROTOCOLS),
                             mandatory=True)
    protocol_port = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_PORT_NUMBER,
                           maximum=constants.MAX_PORT_NUMBER), mandatory=True)
    connection_limit = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_CONNECTION_LIMIT),
        default=constants.DEFAULT_CONNECTION_LIMIT)
    default_tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    sni_container_refs = [wtypes.StringType(max_length=255)]
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    default_pool = wtypes.wsattr(pool.PoolSingleCreate)
    l7policies = wtypes.wsattr([l7policy.L7PolicySingleCreate], default=None)
    insert_headers = wtypes.wsattr(
        wtypes.DictType(str, wtypes.StringType(max_length=255)))
    timeout_client_data = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT),
        # default=CONF.haproxy_amphora.timeout_client_data
    )
    timeout_member_connect = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT),
        # default=CONF.haproxy_amphora.timeout_member_connect
    )
    timeout_member_data = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT),
        # default=CONF.haproxy_amphora.timeout_member_data
    )
    timeout_tcp_inspect = wtypes.wsattr(
        wtypes.IntegerType(minimum=constants.MIN_TIMEOUT,
                           maximum=constants.MAX_TIMEOUT),
        # default=CONF.haproxy_amphora.timeout_tcp_inspect
    )
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    client_ca_tls_container_ref = wtypes.StringType(max_length=255)
    client_authentication = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_CLIENT_AUTH_MODES),
        default=constants.CLIENT_AUTH_NONE)
    client_crl_container_ref = wtypes.StringType(max_length=255)
    allowed_cidrs = wtypes.wsattr([types.CidrType()])
    tls_ciphers = wtypes.StringType(max_length=2048)
    tls_versions = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(
        max_length=32)))
    alpn_protocols = wtypes.wsattr(wtypes.ArrayType(types.AlpnProtocolType()))

    def to_listener_post(self, project_id=None, loadbalancer_id=None,
                         default_pool_id=None):
        listener_post = ListenerPOST()

        for key in [
            'name', 'client_ca_tls_container_ref',
            'client_crl_container_ref', 'connection_limit',
            'default_tls_container_ref', 'description',
            'protocol_port', 'sni_container_refs', 'tags',
            'timeout_client_data', 'timeout_member_connect',
            'timeout_member_data', 'timeout_tcp_inspect', 'tls_ciphers'
        ]:
            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(listener_post, key, v)

        listener_post.admin_state_up = self.admin_state_up
        listener_post.allowed_cidrs = self.allowed_cidrs
        listener_post.l7policies = self.l7policies
        listener_post.insert_headers = self.insert_headers
        listener_post.protocol = self.protocol
        listener_post.tls_versions = self.tls_versions
        listener_post.alpn_protocols = self.alpn_protocols
        listener_post.client_authentication = self.client_authentication
        if project_id:
            listener_post.project_id = project_id
        if loadbalancer_id:
            listener_post.loadbalancer_id = loadbalancer_id
        if default_pool_id:
            listener_post.default_pool_id = default_pool_id
        return listener_post


class ListenerStatusResponse(BaseListenerType):
    """Defines which attributes are to be shown on status response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    pools = wtypes.wsattr([pool.PoolStatusResponse])

    @classmethod
    def from_data_model(cls, data_model, children=False):
        listener = super(ListenerStatusResponse, cls).from_data_model(
            data_model, children=children)

        pool_model = pool.PoolStatusResponse
        listener.pools = [
            pool_model.from_data_model(i) for i in data_model.pools]

        if not listener.name:
            listener.name = ""

        return listener


class ListenerStatisticsResponse(BaseListenerType):
    """Defines which attributes are to show on stats response."""
    bytes_in = wtypes.wsattr(wtypes.IntegerType())
    bytes_out = wtypes.wsattr(wtypes.IntegerType())
    active_connections = wtypes.wsattr(wtypes.IntegerType())
    total_connections = wtypes.wsattr(wtypes.IntegerType())
    request_errors = wtypes.wsattr(wtypes.IntegerType())

    @classmethod
    def from_data_model(cls, data_model, children=False):
        result = super(ListenerStatisticsResponse, cls).from_data_model(
            data_model, children=children)
        return result


class StatisticsRootResponse(types.BaseType):
    stats = wtypes.wsattr(ListenerStatisticsResponse)
