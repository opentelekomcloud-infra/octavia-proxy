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

from octavia_lib.common import constants as lib_constants
from wsme import types as wtypes

from octavia_proxy.api.common import types
from octavia_proxy.api.v2.types import health_monitor
from octavia_proxy.api.v2.types import member
from octavia_proxy.common import constants
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class SessionPersistenceResponse(types.BaseType):
    """Defines which attributes are to be shown on any response."""
    type = wtypes.wsattr(wtypes.text)
    cookie_name = wtypes.wsattr(wtypes.text)
    persistence_timeout = wtypes.wsattr(wtypes.IntegerType())
    persistence_granularity = wtypes.wsattr(types.IPAddressType())


class SessionPersistencePOST(types.BaseType):
    """Defines mandatory and optional attributes of a POST request."""
    type = wtypes.wsattr(wtypes.Enum(str, *constants.SUPPORTED_SP_TYPES),
                         mandatory=True)
    cookie_name = wtypes.wsattr(wtypes.StringType(max_length=255),
                                default=None)
    persistence_timeout = wtypes.wsattr(wtypes.IntegerType(), default=None)
    persistence_granularity = wtypes.wsattr(types.IPAddressType(),
                                            default=None)


class SessionPersistencePUT(types.BaseType):
    """Defines attributes that are acceptable of a PUT request."""
    type = wtypes.wsattr(wtypes.Enum(str, *constants.SUPPORTED_SP_TYPES))
    cookie_name = wtypes.wsattr(wtypes.StringType(max_length=255),
                                default=None)
    persistence_timeout = wtypes.wsattr(wtypes.IntegerType(), default=None)
    persistence_granularity = wtypes.wsattr(types.IPAddressType(),
                                            default=None)


class BasePoolType(types.BaseType):
    _type_to_model_map = {'admin_state_up': 'enabled',
                          'healthmonitor': 'health_monitor',
                          'healthmonitor_id': 'health_monitor.id',
                          'tls_container_ref': 'tls_certificate_id',
                          'ca_tls_container_ref': 'ca_tls_certificate_id',
                          'crl_container_ref': 'crl_container_id'}

    _child_map = {'health_monitor': {'id': 'healthmonitor_id'}}


class PoolResponse(BasePoolType):
    """Defines which attributes are to be shown on any response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    description = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    admin_state_up = wtypes.wsattr(bool)
    protocol = wtypes.wsattr(wtypes.text)
    lb_algorithm = wtypes.wsattr(wtypes.text)
    session_persistence = wtypes.wsattr(SessionPersistenceResponse)
    project_id = wtypes.wsattr(wtypes.StringType())
    loadbalancers = wtypes.wsattr([types.IdOnlyType])
    listeners = wtypes.wsattr([types.IdOnlyType])
    created_at = wtypes.wsattr(wtypes.datetime.datetime)
    updated_at = wtypes.wsattr(wtypes.datetime.datetime)
    healthmonitor_id = wtypes.wsattr(wtypes.UuidType())
    members = wtypes.wsattr([types.IdOnlyType])
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType()))
    tls_container_ref = wtypes.wsattr(wtypes.StringType())
    ca_tls_container_ref = wtypes.wsattr(wtypes.StringType())
    crl_container_ref = wtypes.wsattr(wtypes.StringType())
    tls_enabled = wtypes.wsattr(bool)
    tls_ciphers = wtypes.wsattr(wtypes.StringType())
    tls_versions = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType()))
    alpn_protocols = wtypes.wsattr(wtypes.ArrayType(types.AlpnProtocolType()))

    @classmethod
    def from_data_model(cls, data_model, children=False):
        loadbalancers = data_model.get('loadbalancers', [])
        listeners = data_model.get('listeners', [])
        members = data_model.get('members', [])
        tls_versions = data_model.get('tls_versions', [])
        alpn_protocols = data_model.get('alpn_protocols', [])
        session_persistence = data_model.get('session_persistence')
        healthmonitor = data_model.get('health_monitor')
        data_model['loadbalancers'] = []
        data_model['listeners'] = []
        data_model['members'] = []
        data_model['tls_versions'] = []
        data_model['alpn_protocols'] = []
        pool = super(PoolResponse, cls).from_data_model(
            data_model, children=children)
        if session_persistence:
            pool.session_persistence = (
                SessionPersistenceResponse.from_data_model(
                    session_persistence))

        if cls._full_response():
            del pool.loadbalancers
            member_model = member.MemberFullResponse
            if pool.healthmonitor:
                pool.healthmonitor = (
                    health_monitor.HealthMonitorFullResponse
                    .from_data_model(healthmonitor))
        else:
            if loadbalancers:
                pool.loadbalancers = [
                    types.IdOnlyType.from_data_model(loadbalancers)]
            else:
                pool.loadbalancers = []
            member_model = types.IdOnlyType
            if health_monitor:
                pool.healthmonitor_id = healthmonitor.id
        if listeners:
            pool.listeners = [
                types.IdOnlyType.from_data_model(i) for i in listeners]
        else:
            pool.listeners = []
        if members:
            pool.members = [member_model.from_data_model(i) for i in members]
        else:
            pool.members = []

        pool.tls_versions = tls_versions
        pool.alpn_protocols = alpn_protocols

        return pool

    @classmethod
    def from_sdk_object(cls, sdk_entity, children=False):
        pool = cls()
        for key in [
            'id', 'name',
            'availability_zone', 'description',
            'protocol', 'lb_algorithm',
            'session_persistence', 'project_id', 'provider',
            'healthmonitor_id'
        ]:

            if hasattr(sdk_entity, key):
                v = getattr(sdk_entity, key)
                if v:
                    setattr(pool, key, v)

        pool.admin_state_up = sdk_entity.is_admin_state_up

        if sdk_entity.loadbalancers:
            pool.loadbalancers = [
                types.IdOnlyType(id=i['id']) for i in sdk_entity.loadbalancers
            ]
        if sdk_entity.listeners:
            pool.listeners = [
                types.IdOnlyType(id=i['id']) for i in sdk_entity.listeners
            ]
        if sdk_entity.members:
            pool.members = [
                types.IdOnlyType(id=i['id']) for i in sdk_entity.members
            ]
        return pool

    def to_full_response(self, members=None, healthmonitor=None):
        full_response = PoolFullResponse()

        for key in [
            'id', 'name',
            'operating_status', 'provisioning_status',
            'description', 'protocol', 'lb_algorithm',
            'session_persistence', 'project_id',
            'healthmonitor_id', 'tags', 'tls_container_ref',
            'tls_ciphers', 'ca_tls_container_ref', 'crl_container_ref'
        ]:

            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(full_response, key, v)

        full_response.admin_state_up = self.admin_state_up
        full_response.loadbalancers = self.loadbalancers
        full_response.listeners = self.listeners
        full_response.created_at = self.created_at
        full_response.updated_at = self.updated_at
        full_response.tls_enabled = self.tls_enabled
        full_response.tls_versions = self.tls_versions
        full_response.alpn_protocols = self.alpn_protocols

        if members:
            full_response.members = members
        if healthmonitor:
            full_response.healthmonitor = healthmonitor
        return full_response


class PoolFullResponse(PoolResponse):
    @classmethod
    def _full_response(cls):
        return True

    members = wtypes.wsattr([member.MemberFullResponse])
    healthmonitor = wtypes.wsattr(health_monitor.HealthMonitorFullResponse)


class PoolRootResponse(types.BaseType):
    pool = wtypes.wsattr(PoolResponse)


class PoolsRootResponse(types.BaseType):
    pools = wtypes.wsattr([PoolResponse])
    pools_links = wtypes.wsattr([types.PageType])


class PoolPOST(BasePoolType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    listener_id = wtypes.wsattr(wtypes.UuidType())
    loadbalancer_id = wtypes.wsattr(wtypes.UuidType())
    protocol = wtypes.wsattr(
        wtypes.Enum(str, *lib_constants.POOL_SUPPORTED_PROTOCOLS),
        mandatory=True)
    lb_algorithm = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_LB_ALGORITHMS),
        mandatory=True)
    session_persistence = wtypes.wsattr(SessionPersistencePOST)
    # TODO(johnsom) Remove after deprecation (R series)
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    healthmonitor = wtypes.wsattr(health_monitor.HealthMonitorSingleCreate)
    members = wtypes.wsattr([member.MemberSingleCreate])
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    tls_container_ref = wtypes.wsattr(
        wtypes.StringType(max_length=255))
    ca_tls_container_ref = wtypes.wsattr(wtypes.StringType(max_length=255))
    crl_container_ref = wtypes.wsattr(wtypes.StringType(max_length=255))
    tls_enabled = wtypes.wsattr(bool, default=False)
    tls_ciphers = wtypes.wsattr(wtypes.StringType(max_length=2048))
    tls_versions = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(
        max_length=32)))
    alpn_protocols = wtypes.wsattr(wtypes.ArrayType(types.AlpnProtocolType()))


class PoolRootPOST(types.BaseType):
    pool = wtypes.wsattr(PoolPOST)


class PoolPUT(BasePoolType):
    """Defines attributes that are acceptable of a PUT request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool)
    lb_algorithm = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_LB_ALGORITHMS))
    session_persistence = wtypes.wsattr(SessionPersistencePUT)
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    tls_container_ref = wtypes.wsattr(wtypes.StringType(max_length=255))
    ca_tls_container_ref = wtypes.wsattr(wtypes.StringType(max_length=255))
    crl_container_ref = wtypes.wsattr(wtypes.StringType(max_length=255))
    tls_enabled = wtypes.wsattr(bool)
    tls_ciphers = wtypes.wsattr(wtypes.StringType(max_length=2048))
    tls_versions = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(
        max_length=32)))
    alpn_protocols = wtypes.wsattr(wtypes.ArrayType(types.AlpnProtocolType()))


class PoolRootPut(types.BaseType):
    pool = wtypes.wsattr(PoolPUT)


class PoolSingleCreate(BasePoolType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    protocol = wtypes.wsattr(
        wtypes.Enum(str, *lib_constants.POOL_SUPPORTED_PROTOCOLS))
    lb_algorithm = wtypes.wsattr(
        wtypes.Enum(str, *constants.SUPPORTED_LB_ALGORITHMS))
    session_persistence = wtypes.wsattr(SessionPersistencePOST)
    healthmonitor = wtypes.wsattr(health_monitor.HealthMonitorSingleCreate)
    members = wtypes.wsattr([member.MemberSingleCreate])
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    tls_container_ref = wtypes.wsattr(wtypes.StringType(max_length=255))
    ca_tls_container_ref = wtypes.wsattr(wtypes.StringType(max_length=255))
    crl_container_ref = wtypes.wsattr(wtypes.StringType(max_length=255))
    tls_enabled = wtypes.wsattr(bool, default=False)
    tls_ciphers = wtypes.wsattr(wtypes.StringType(max_length=2048))
    tls_versions = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(
        max_length=32)))
    alpn_protocols = wtypes.wsattr(wtypes.ArrayType(types.AlpnProtocolType()))

    def to_pool_post(self, project_id=None, loadbalancer_id=None,
                     listener_id=None):
        pool_post = PoolPOST()

        for key in [
            'name', 'description', 'protocol', 'lb_algorithm',
            'tls_container_ref', 'ca_tls_container_ref',
            'crl_container_ref', 'tls_ciphers', 'tags'
        ]:

            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(pool_post, key, v)

        pool_post.admin_state_up = self.admin_state_up
        pool_post.session_persistence = self.session_persistence
        pool_post.healthmonitor = self.healthmonitor
        pool_post.tls_enabled = self.tls_enabled
        pool_post.tls_versions = self.tls_versions
        pool_post.alpn_protocols = self.alpn_protocols
        if loadbalancer_id:
            pool_post.loadbalancer_id = loadbalancer_id
        if listener_id:
            pool_post.listener_id = listener_id
        if project_id:
            pool_post.project_id = project_id
        return pool_post


class PoolStatusResponse(BasePoolType):
    """Defines which attributes are to be shown on status response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    health_monitor = wtypes.wsattr(
        health_monitor.HealthMonitorStatusResponse)
    members = wtypes.wsattr([member.MemberStatusResponse])

    @classmethod
    def from_data_model(cls, data_model, children=False):
        pool = super(PoolStatusResponse, cls).from_data_model(
            data_model, children=children)

        member_model = member.MemberStatusResponse
        if data_model.health_monitor:
            pool.health_monitor = (
                health_monitor.HealthMonitorStatusResponse.from_data_model(
                    data_model.health_monitor))
        pool.members = [
            member_model.from_data_model(i) for i in data_model.members]

        return pool
