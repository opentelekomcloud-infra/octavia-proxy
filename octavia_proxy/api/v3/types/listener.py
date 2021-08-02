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
from octavia_proxy.api.v3.types import l7policy
from octavia_proxy.api.v3.types import pool
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

    admin_state_up = wtypes.wsattr(bool)
    client_ca_tls_container_ref = wtypes.StringType()
    connection_limit = wtypes.wsattr(wtypes.IntegerType())
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    default_tls_container_ref = wtypes.wsattr(wtypes.StringType())
    description = wtypes.wsattr(wtypes.StringType())
    http2_enable = wtypes.wsattr(bool)
    insert_headers = wtypes.wsattr(wtypes.DictType(str, str))
    loadbalancers = wtypes.wsattr([types.IdOnlyType])
    project_id = wtypes.wsattr(wtypes.StringType())
    protocol = wtypes.wsattr(wtypes.text)
    protocol_port = wtypes.wsattr(wtypes.IntegerType())
    sni_container_refs = [wtypes.StringType()]
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType()))
    tls_ciphers_policy = wtypes.StringType()
    updated_at = wtypes.wsattr(wtypes.datetime.datetime)
    created_at = wtypes.wsattr(wtypes.datetime.datetime)
    enable_member_retry = wtypes.wsattr(bool)
    keepalive_timeout = wtypes.wsattr(wtypes.IntegerType())
    client_timeout = wtypes.wsattr(wtypes.IntegerType(), default=60)
    member_timeout = wtypes.wsattr(wtypes.IntegerType(), default=60)
    ipgroup = wtypes.wsattr(dict)
    transparent_client_ip_enable = wtypes.wsattr(bool)
    enhance_l7policy_enable = wtypes.wsattr(bool)

    @classmethod
    def from_data_model(cls, data_model, children=False):
        listener = super(ListenerResponse, cls).from_data_model(
            data_model, children=children)

        listener.sni_container_refs = [
            sni_c.tls_container_id for sni_c in data_model.sni_container_refs]
        if cls._full_response():
            del listener.loadbalancers
            l7policy_type = l7policy.L7PolicyFullResponse
        else:
            listener.loadbalancers = [
                types.IdOnlyType.from_data_model(data_model.load_balancer)]
            l7policy_type = types.IdOnlyType

        listener.l7policies = [
            l7policy_type.from_data_model(i) for i in data_model.l7policies]

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
            v = sdk_entity.get(key)
            if v:
                setattr(listener, key, v)

        listener.admin_state_up = sdk_entity.is_admin_state_up
        for attr in ['created_at', 'updated_at']:
            setattr(listener, attr, parser.parse(sdk_entity[attr]))

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
        return listener


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
    admin_state_up = wtypes.wsattr(bool, default=True)
    client_ca_tls_container_ref = wtypes.StringType(max_length=255)
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    default_tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    http2_enable = wtypes.wsattr(bool)
    insert_headers = wtypes.wsattr(
        wtypes.DictType(str, wtypes.StringType(max_length=255)))
    loadbalancer_id = wtypes.wsattr(wtypes.UuidType(), mandatory=True)
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    protocol = wtypes.wsattr(
        wtypes.Enum(str, *constants.LISTENER_SUPPORTED_PROTOCOLS),
        mandatory=True)
    protocol_port = wtypes.wsattr(
        wtypes.IntegerType(
            minimum=constants.MIN_PORT_NUMBER,
            maximum=constants.MAX_PORT_NUMBER),
        mandatory=True)
    sni_container_refs = [wtypes.StringType(max_length=255)]
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    tls_ciphers_policy = wtypes.StringType()

    enable_member_retry = wtypes.wsattr(bool)
    keepalive_timeout = wtypes.wsattr(wtypes.IntegerType())
    client_timeout = wtypes.wsattr(
        wtypes.IntegerType(
            minimum=constants.MIN_TIMEOUT,
            maximum=constants.MAX_TIMEOUT),
        default=60)
    member_timeout = wtypes.wsattr(
        wtypes.IntegerType(
            minimum=constants.MIN_TIMEOUT,
            maximum=constants.MAX_TIMEOUT),
        default=60)
    ipgroup = wtypes.wsattr(wtypes.DictType)
    transparent_client_ip_enable = wtypes.wsattr(bool)
    enhance_l7policy_enable = wtypes.wsattr(bool)

    default_pool = wtypes.wsattr(pool.PoolSingleCreate)
    l7policies = wtypes.wsattr([l7policy.L7PolicySingleCreate], default=[])


class ListenerRootPOST(types.BaseType):
    listener = wtypes.wsattr(ListenerPOST)


class ListenerPUT(BaseListenerType):
    """Defines attributes that are acceptable of a PUT request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool)
    default_tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    http2_enable = wtypes.wsattr(bool)
    insert_headers = wtypes.wsattr(
        wtypes.DictType(str, wtypes.StringType(max_length=255)))
    sni_container_refs = [wtypes.StringType(max_length=255)]
    enable_member_retry = wtypes.wsattr(bool)
    keepalive_timeout = wtypes.wsattr(wtypes.IntegerType())
    client_timeout = wtypes.wsattr(
        wtypes.IntegerType(
            minimum=constants.MIN_TIMEOUT,
            maximum=constants.MAX_TIMEOUT),
        default=60)
    member_timeout = wtypes.wsattr(
        wtypes.IntegerType(
            minimum=constants.MIN_TIMEOUT,
            maximum=constants.MAX_TIMEOUT),
        default=60)
    ipgroup = wtypes.wsattr(wtypes.DictType)
    transparent_client_ip_enable = wtypes.wsattr(bool)
    enhance_l7policy_enable = wtypes.wsattr(bool)


class ListenerRootPUT(types.BaseType):
    listener = wtypes.wsattr(ListenerPUT)


class ListenerSingleCreate(BaseListenerType):
    """Defines mandatory and optional attributes of a POST request."""

    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    client_ca_tls_container_ref = wtypes.StringType(max_length=255)
    default_pool_id = wtypes.wsattr(wtypes.UuidType())
    default_tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    http2_enable = wtypes.wsattr(bool)
    insert_headers = wtypes.wsattr(
        wtypes.DictType(str, wtypes.StringType(max_length=255)))
    loadbalancer_id = wtypes.wsattr(wtypes.UuidType(), mandatory=True)
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    protocol = wtypes.wsattr(
        wtypes.Enum(str, *constants.LISTENER_SUPPORTED_PROTOCOLS),
        mandatory=True)
    protocol_port = wtypes.wsattr(
        wtypes.IntegerType(
            minimum=constants.MIN_PORT_NUMBER,
            maximum=constants.MAX_PORT_NUMBER),
        mandatory=True)
    sni_container_refs = [wtypes.StringType(max_length=255)]
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    tls_ciphers_policy = wtypes.StringType()

    enable_member_retry = wtypes.wsattr(bool)
    keepalive_timeout = wtypes.wsattr(wtypes.IntegerType())
    client_timeout = wtypes.wsattr(
        wtypes.IntegerType(
            minimum=constants.MIN_TIMEOUT,
            maximum=constants.MAX_TIMEOUT),
        default=60)
    member_timeout = wtypes.wsattr(
        wtypes.IntegerType(
            minimum=constants.MIN_TIMEOUT,
            maximum=constants.MAX_TIMEOUT),
        default=60)
    ipgroup = wtypes.wsattr(wtypes.DictType)
    transparent_client_ip_enable = wtypes.wsattr(bool)
    enhance_l7policy_enable = wtypes.wsattr(bool)
    default_pool = wtypes.wsattr(pool.PoolSingleCreate)
    l7policies = wtypes.wsattr([l7policy.L7PolicySingleCreate], default=[])


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