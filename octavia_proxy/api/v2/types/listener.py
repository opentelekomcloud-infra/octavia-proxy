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
        listener = super(ListenerResponse, cls).from_data_model(
            data_model, children=children)

        listener.sni_container_refs = [
            sni_c.tls_container_id for sni_c in data_model.sni_container_refs]
        listener.allowed_cidrs = [
            c.cidr for c in data_model.allowed_cidrs] or None
        if cls._full_response():
            del listener.loadbalancers
            l7policy_type = l7policy.L7PolicyFullResponse
        else:
            listener.loadbalancers = [
                types.IdOnlyType.from_data_model(data_model.load_balancer)]
            l7policy_type = types.IdOnlyType

        listener.l7policies = [
            l7policy_type.from_data_model(i) for i in data_model.l7policies]

        listener.tls_versions = data_model.tls_versions
        listener.alpn_protocols = data_model.alpn_protocols

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
            'sni_container_refs',
            'tags',
            'timeout_client_data', 'timeout_memeber_connect',
            'timeout_member_data', 'timeout_tcp_inspect', 'tls_ciphers'
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

        full_response.id = self.id
        full_response.name = self.name
        full_response.description = self.description
        full_response.provisioning_status = self.provisioning_status
        full_response.operating_status = self.operating_status
        full_response.admin_state_up = self.admin_state_up
        full_response.protocol = self.protocol
        full_response.protocol_port = self.protocol_port
        full_response.connection_limit = self.connection_limit
        full_response.default_tls_container_ref =\
            self.default_tls_container_ref
        full_response.sni_container_refs = self.sni_container_refs
        full_response.project_id = self.project_id
        full_response.default_pool_id = self.default_pool_id
        full_response.insert_headers = self.insert_headers
        full_response.created_at = self.created_at
        full_response.updated_at = self.updated_at
        full_response.loadbalancers = self.loadbalancers
        full_response.timeout_client_data = self.timeout_client_data
        full_response.timeout_member_connect = self. timeout_member_connect
        full_response.timeout_member_data = self.timeout_member_data
        full_response.timeout_tcp_inspect = self.timeout_tcp_inspect
        full_response.tags = self.tags
        full_response.client_ca_tls_container_ref\
            = self.client_ca_tls_container_ref
        full_response.client_authentication = self.client_authentication
        full_response.client_crl_container_ref = self.client_crl_container_ref
        full_response.allowed_cidrs = self.allowed_cidrs
        full_response.tls_ciphers = self.tls_ciphers
        full_response.tls_versions = self.tls_versions
        full_response.alpn_protocols = self.alpn_protocols

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
    l7policies = wtypes.wsattr([l7policy.L7PolicySingleCreate], default=[])
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
    l7policies = wtypes.wsattr([l7policy.L7PolicySingleCreate], default=[])
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

        if self.name:
            setattr(listener_post, 'name', self.name)

        if self.description:
            setattr(listener_post, 'description', self.description)
        if self.admin_state_up:
            setattr(listener_post, 'admin_state_up', self.admin_state_up)
        if self.protocol:
            setattr(listener_post, 'protocol', self.protocol)
        if self.protocol_port:
            setattr(listener_post, 'protocol_port', self.protocol_port)
        if self.connection_limit:
            setattr(listener_post, 'connection_limit', self.connection_limit)
        if self.default_tls_container_ref:
            setattr(listener_post, 'protocol_port', self.protocol_port)
        if self.sni_container_refs:
            setattr(listener_post, 'connection_limit', self.connection_limit)
        if self.l7policies:
            setattr(listener_post, 'l7policies', self.l7policies)
        if self.insert_headers:
            setattr(listener_post, 'insert_headers', self.insert_headers)
        if self.timeout_client_data:
            setattr(listener_post, 'timeout_client_data',
                    self.timeout_client_data)
        if self.timeout_member_connect:
            setattr(listener_post, 'timeout_member_connect',
                    self.timeout_member_connect)
        if self.timeout_member_data:
            setattr(listener_post, 'timeout_member_data',
                    self.timeout_member_data)
        if self.timeout_tcp_inspect:
            setattr(listener_post, 'timeout_tcp_inspect',
                    self.timeout_tcp_inspect)
        if self.tags:
            setattr(listener_post, 'tags',
                    self.tags)
        if self.client_ca_tls_container_ref:
            setattr(listener_post, 'client_ca_tls_container_ref',
                    self.client_ca_tls_container_ref)
        if self.client_authentication:
            setattr(listener_post, 'client_authentication',
                    self.client_authentication)
        if self.client_crl_container_ref:
            setattr(listener_post, 'client_crl_container_ref',
                    self.client_crl_container_ref)
        if self.allowed_cidrs:
            setattr(listener_post, 'allowed_cidrs',
                    self.allowed_cidrs)
        if self.tls_ciphers:
            setattr(listener_post, 'tls_ciphers',
                    self.tls_ciphers)
        if self.tls_versions:
            setattr(listener_post, 'tls_versions',
                    self.tls_versions)
        if self.alpn_protocols:
            setattr(listener_post, 'alpn_protocols',
                    self.alpn_protocols)
        if project_id:
            setattr(listener_post, 'project_id', project_id)
        if loadbalancer_id:
            setattr(listener_post, 'loadbalancer_id', loadbalancer_id)
        if default_pool_id:
            setattr(listener_post, 'default_pool_id', default_pool_id)
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
