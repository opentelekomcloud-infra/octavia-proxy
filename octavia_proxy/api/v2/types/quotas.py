#    Copyright 2016 Rackspace
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

from wsme import types as wtypes

from octavia_proxy.api.common import types as base
from octavia_proxy.common import constants as consts


class QuotaBase(base.BaseType):
    _type_to_model_map = {}
    _child_map = {}


class QuotaResponse(QuotaBase):
    """Individual quota definitions."""
    project_id = wtypes.wsattr(wtypes.UuidType())
    loadbalancer = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))
    # Misspelled version, deprecated in Rocky
    load_balancer = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))
    listener = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))
    member = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))
    pool = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))
    healthmonitor = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))
    # Misspelled version, deprecated in Rocky
    health_monitor = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))
    l7policy = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))
    l7rule = wtypes.wsattr(wtypes.IntegerType(
        minimum=consts.MIN_QUOTA, maximum=consts.MAX_QUOTA))

    def to_dict(self, render_unsets=False):
        quota_dict = super().to_dict(render_unsets)
        if 'loadbalancer' in quota_dict:
            quota_dict['load_balancer'] = quota_dict.pop('loadbalancer')
        if 'healthmonitor' in quota_dict:
            quota_dict['health_monitor'] = quota_dict.pop('healthmonitor')
        return quota_dict

    @classmethod
    def from_data_model(cls, data_model, children=False):
        quotas = super(QuotaResponse, cls).from_data_model(
            data_model, children=children)
        quotas.quota = QuotaBase.from_data_model(data_model)
        return quotas

    @classmethod
    def from_sdk_object(cls, sdk_entity):
        quota = cls()
        for key in [
            'loadbalancer', 'load_balancer', 'listener', 'member',
            'pool', 'healthmonitor', 'health_monitor', 'l7policy',
            'l7rule', 'project_id'
        ]:

            if hasattr(sdk_entity, key):
                v = getattr(sdk_entity, key)
                if v:
                    setattr(quota, key, v)
        if hasattr(quota, 'loadbalancer'):
            quota.load_balancer = quota.loadbalancer
        if hasattr(quota, 'healthmonitor'):
            quota.health_monitor = quota.healthmonitor
        return quota


class QuotaFullResponse(QuotaResponse):
    @classmethod
    def _full_response(cls):
        return True


class QuotaAllBase(base.BaseType):
    """Wrapper object for get all quotas responses."""
    project_id = wtypes.wsattr(wtypes.StringType())
    loadbalancer = wtypes.wsattr(wtypes.IntegerType())
    # Misspelled version, deprecated in Rocky, remove in T
    load_balancer = wtypes.wsattr(wtypes.IntegerType())
    listener = wtypes.wsattr(wtypes.IntegerType())
    member = wtypes.wsattr(wtypes.IntegerType())
    pool = wtypes.wsattr(wtypes.IntegerType())
    healthmonitor = wtypes.wsattr(wtypes.IntegerType())
    # Misspelled version, deprecated in Rocky, remove in T
    health_monitor = wtypes.wsattr(wtypes.IntegerType())
    l7policy = wtypes.wsattr(wtypes.IntegerType())
    l7rule = wtypes.wsattr(wtypes.IntegerType())

    _type_to_model_map = {'loadbalancer': 'load_balancer',
                          'healthmonitor': 'health_monitor'}
    _child_map = {}

    @classmethod
    def from_data_model(cls, data_model, children=False):
        quotas = super(QuotaAllBase, cls).from_data_model(
            data_model, children=children)
        # For backwards compatibility, remove in T
        quotas.load_balancer = quotas.loadbalancer
        # For backwards compatibility, remove in T
        quotas.health_monitor = quotas.healthmonitor
        return quotas


class QuotaRootResponse(base.BaseType):
    quota = wtypes.wsattr(QuotaResponse)


class QuotasRootResponse(base.BaseType):
    quotas = wtypes.wsattr([QuotaResponse])
    quotas_links = wtypes.wsattr([base.PageType])


class QuotaPUT(base.BaseType):
    """Overall object for quota PUT request."""
    quota = wtypes.wsattr(QuotaBase)
