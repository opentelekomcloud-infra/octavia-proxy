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
from wsme import types as wtypes

from oslo_log import log as logging

from octavia_proxy.api.common import types
from octavia_proxy.api.v2.types import listener
from octavia_proxy.api.v2.types import pool


LOG = logging.getLogger(__name__)


class BaseLoadBalancerType(types.BaseType):
    _type_to_model_map = {
        # 'vip_address': 'vip.ip_address',
        # 'vip_subnet_id': 'vip.subnet_id',
        # 'vip_port_id': 'vip.port_id',
        # 'vip_network_id': 'vip.network_id',
        # 'vip_qos_policy_id': 'vip.qos_policy_id',
        'admin_state_up': 'enabled'
    }
#    _child_map = {'vip': {
#        'ip_address': 'vip_address',
#        'subnet_id': 'vip_subnet_id',
#        'port_id': 'vip_port_id',
#        'network_id': 'vip_network_id',
#        'qos_policy_id': 'vip_qos_policy_id',
#        },
#        'listeners': 'listeners'}


class LoadBalancerResponse(BaseLoadBalancerType):
    """Defines which attributes are to be shown on any response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    description = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    admin_state_up = wtypes.wsattr(bool)
    project_id = wtypes.wsattr(wtypes.StringType())
    created_at = wtypes.wsattr(wtypes.datetime.datetime)
    updated_at = wtypes.wsattr(wtypes.datetime.datetime)
    vip_address = wtypes.wsattr(types.IPAddressType())
    vip_port_id = wtypes.wsattr(wtypes.UuidType())
    vip_subnet_id = wtypes.wsattr(wtypes.UuidType())
    vip_network_id = wtypes.wsattr(wtypes.UuidType())
    listeners = wtypes.wsattr([types.IdOnlyType])
    pools = wtypes.wsattr([types.IdOnlyType])
    provider = wtypes.wsattr(wtypes.StringType())
    flavor_id = wtypes.wsattr(wtypes.UuidType())
    vip_qos_policy_id = wtypes.wsattr(wtypes.UuidType())
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType()))
    availability_zone = wtypes.wsattr(wtypes.StringType())

    @classmethod
    def from_data_model(cls, data_model, children=False):
        listeners = data_model.get('listeners', [])
        pools = data_model.get('pools', [])
        data_model['listeners'] = []
        data_model['pools'] = []

        result = super(LoadBalancerResponse, cls).from_data_model(
            data_model, children=children)
#        if data_model.vip:
#            result.vip_subnet_id = data_model.vip.subnet_id
#            result.vip_port_id = data_model.vip.port_id
#            result.vip_address = data_model.vip.ip_address
#            result.vip_network_id = data_model.vip.network_id
#            result.vip_qos_policy_id = data_model.vip.qos_policy_id
        if cls._full_response():
            listener_model = listener.ListenerFullResponse
            pool_model = pool.PoolFullResponse
        else:
            listener_model = types.IdOnlyType
            pool_model = types.IdOnlyType
        result.listeners = [
            listener_model(id=i['id']) for i in listeners]
        result.pools = [
            pool_model(id=i['id']) for i in pools]
#       result.admin_state_up = data_model.is_admin_state_up

        if not result.provider:
            result.provider = "octavia"

        return result

    @classmethod
    def from_sdk_object(cls, sdk_entity, children=False):
        load_balancer = cls()
        for key in [
            'id', 'name',
            'availability_zone', 'description', 'flavor_id',
            'operating_status', 'project_id', 'provider',
            'provisioning_status', 'tags', 'vip_address', 'vip_network_id',
            'vip_port_id', 'vip_qos_policy_id', 'vip_subnet_id'
        ]:

            if hasattr(sdk_entity, key):
                v = getattr(sdk_entity, key)
                if v:
                    setattr(load_balancer, key, v)

        load_balancer.admin_state_up = sdk_entity.is_admin_state_up
        for attr in ['created_at', 'updated_at']:
            setattr(load_balancer, attr, parser.parse(sdk_entity[attr]))

        if sdk_entity.listeners:
            load_balancer.listeners = [
                types.IdOnlyType(id=i['id']) for i in sdk_entity.listeners
            ]
        else:
            load_balancer.listeners = []
        if sdk_entity.pools:
            load_balancer.pools = [
                types.IdOnlyType(id=i['id']) for i in sdk_entity.pools
            ]
        else:
            load_balancer.pools = []
        return load_balancer

    def to_full_response(self, pools=None, listeners=None):
        full_response = LoadBalancerFullResponse()

        for key in [
            'id', 'name',
            'availability_zone', 'description', 'flavor_id',
            'operating_status', 'project_id', 'provider',
            'provisioning_status', 'tags', 'vip_address', 'vip_network_id',
            'vip_port_id', 'vip_qos_policy_id', 'vip_subnet_id'
        ]:

            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(full_response, key, v)

        full_response.created_at = self.created_at
        full_response.updated_at = self.updated_at
        full_response.admin_state_up = self.admin_state_up
        if listeners:
            full_response.listeners = listeners
        if pools:
            full_response.pools = pools
        return full_response


class LoadBalancerFullResponse(LoadBalancerResponse):
    @classmethod
    def _full_response(cls):
        return True

    listeners = wtypes.wsattr([listener.ListenerFullResponse])
    pools = wtypes.wsattr([pool.PoolFullResponse])


class LoadBalancerRootResponse(types.BaseType):
    loadbalancer = wtypes.wsattr(LoadBalancerResponse)


class LoadBalancerFullRootResponse(LoadBalancerRootResponse):
    loadbalancer = wtypes.wsattr(LoadBalancerFullResponse)


class LoadBalancersRootResponse(types.BaseType):
    loadbalancers = wtypes.wsattr([LoadBalancerResponse])
    loadbalancers_links = wtypes.wsattr([types.PageType])


class LoadBalancerPOST(BaseLoadBalancerType):
    """Defines mandatory and optional attributes of a POST request."""

    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    vip_address = wtypes.wsattr(types.IPAddressType())
    vip_port_id = wtypes.wsattr(wtypes.UuidType())
    vip_subnet_id = wtypes.wsattr(wtypes.UuidType())
    vip_network_id = wtypes.wsattr(wtypes.UuidType())
    vip_qos_policy_id = wtypes.wsattr(wtypes.UuidType())
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    listeners = wtypes.wsattr([listener.ListenerSingleCreate], default=None)
    pools = wtypes.wsattr([pool.PoolSingleCreate], default=None)
    provider = wtypes.wsattr(wtypes.StringType(max_length=64))
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))
    flavor_id = wtypes.wsattr(wtypes.UuidType())
    availability_zone = wtypes.wsattr(wtypes.StringType(max_length=255))


class LoadBalancerRootPOST(types.BaseType):
    loadbalancer = wtypes.wsattr(LoadBalancerPOST)


class LoadBalancerPUT(BaseLoadBalancerType):
    """Defines attributes that are acceptable of a PUT request."""

    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    description = wtypes.wsattr(wtypes.StringType(max_length=255))
    vip_qos_policy_id = wtypes.wsattr(wtypes.UuidType())
    admin_state_up = wtypes.wsattr(bool)
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))


class LoadBalancerRootPUT(types.BaseType):
    loadbalancer = wtypes.wsattr(LoadBalancerPUT)


class LoadBalancerStatusResponse(BaseLoadBalancerType):
    """Defines which attributes are to be shown on status response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    listeners = wtypes.wsattr([listener.ListenerStatusResponse])

    @classmethod
    def from_data_model(cls, data_model, children=False):
        result = super(LoadBalancerStatusResponse, cls).from_data_model(
            data_model, children=children)
        listener_model = listener.ListenerStatusResponse
        result.listeners = [
            listener_model.from_data_model(i) for i in data_model.listeners]
        if not result.name:
            result.name = ""

        return result


class StatusResponse(wtypes.Base):
    loadbalancer = wtypes.wsattr(LoadBalancerStatusResponse)


class StatusRootResponse(types.BaseType):
    statuses = wtypes.wsattr(StatusResponse)


class LoadBalancerStatisticsResponse(BaseLoadBalancerType):
    """Defines which attributes are to show on stats response."""
    bytes_in = wtypes.wsattr(wtypes.IntegerType())
    bytes_out = wtypes.wsattr(wtypes.IntegerType())
    active_connections = wtypes.wsattr(wtypes.IntegerType())
    total_connections = wtypes.wsattr(wtypes.IntegerType())
    request_errors = wtypes.wsattr(wtypes.IntegerType())

    @classmethod
    def from_data_model(cls, data_model, children=False):
        result = super(LoadBalancerStatisticsResponse, cls).from_data_model(
            data_model, children=children)
        return result


class StatisticsRootResponse(types.BaseType):
    stats = wtypes.wsattr(LoadBalancerStatisticsResponse)
