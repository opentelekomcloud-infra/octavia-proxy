# Copyright 2021 Open Telekom Cloud, T-Systems International
# Copyright 2018 Rackspace, US Inc.
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

import copy

from octavia_lib.api.drivers import exceptions as lib_exceptions
from openstack import exceptions as openstack_exceptions
from oslo_config import cfg
from oslo_log import log as logging

from octavia_proxy.common import exceptions

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def call_provider(provider, driver_method, *args, **kwargs):
    """Wrap calls to the provider driver to handle driver errors.

    This allows Octavia to return user friendly errors when a provider driver
    has an issue.

    :param driver_method: Method in the driver to call.
    :raises ProviderDriverError: Catch all driver error.
    :raises ProviderNotImplementedError: The driver doesn't support this
                                         action.
    :raises ProviderUnsupportedOptionError: The driver doesn't support a
                                            provided option.
    """

    try:
        return driver_method(*args, **kwargs)
    except lib_exceptions.DriverError as e:
        LOG.exception("Provider '%s' raised a driver error: %s",
                      provider, e.operator_fault_string)
        raise exceptions.ProviderDriverError(prov=provider,
                                             user_msg=e.user_fault_string)
    except (lib_exceptions.NotImplementedError, NotImplementedError) as e:
        op_fault_string = (
            e.operator_fault_string
            if hasattr(e, "operator_fault_string")
            else ("This feature is not implemented by this provider."))
        usr_fault_string = (
            e.user_fault_string
            if hasattr(e, "user_fault_string")
            else ("This feature is not implemented by the provider."))
        LOG.info("Provider '%s' raised a not implemented error: %s",
                 provider, op_fault_string)
        raise exceptions.ProviderNotImplementedError(
            prov=provider, user_msg=usr_fault_string)
    except lib_exceptions.UnsupportedOptionError as e:
        LOG.info("Provider '%s' raised an unsupported option error: "
                 "%s", provider, e.operator_fault_string)
        raise exceptions.ProviderUnsupportedOptionError(
            prov=provider, user_msg=e.user_fault_string)
    except openstack_exceptions.ResourceNotFound as e:
        LOG.info("Provider '%s' raised ResourceNotFound error: "
                 "%s", provider, e.message)
        raise exceptions.ResourceNotFound(detail=e.message)
    except openstack_exceptions.BadRequestException as e:
        LOG.info("Provider '%s' raised BadRequestException error: "
                 "%s", provider, e.message)
        raise exceptions.ValidationException(detail=e.message)
    except Exception as e:
        LOG.exception("Provider '%s' raised an unknown error: %s",
                      provider, str(e))
        raise exceptions.ProviderDriverError(prov=provider, user_msg=e)


def _base_to_provider_dict(current_dict, include_project_id=False):
    new_dict = copy.deepcopy(current_dict)
    new_dict.pop('provisioning_status', None)
    new_dict.pop('operating_status', None)
    new_dict.pop('provider', None)
    new_dict.pop('created_at', None)
    new_dict.pop('updated_at', None)
    new_dict.pop('tenant_id', None)
    new_dict.pop('tags', None)
    new_dict.pop('flavor_id', None)
    new_dict.pop('topology', None)
    new_dict.pop('vrrp_group', None)
    new_dict.pop('amphorae', None)
    new_dict.pop('vip', None)
    new_dict.pop('listeners', None)
    new_dict.pop('pools', None)
    new_dict.pop('server_group_id', None)
    if 'enabled' in new_dict:
        new_dict['admin_state_up'] = new_dict.pop('enabled')
    if not include_project_id:
        new_dict.pop('project_id', None)

    return new_dict


# Note: The provider dict returned from this method will have provider
#       data model objects in it.
def lb_dict_to_provider_dict(lb_dict, vip=None):
    new_lb_dict = _base_to_provider_dict(lb_dict, include_project_id=True)
    new_lb_dict['loadbalancer_id'] = new_lb_dict.pop('id')
    if vip:
        new_lb_dict['vip_address'] = vip.ip_address
        new_lb_dict['vip_network_id'] = vip.network_id
        new_lb_dict['vip_port_id'] = vip.port_id
        new_lb_dict['vip_subnet_id'] = vip.subnet_id
        new_lb_dict['vip_qos_policy_id'] = vip.qos_policy_id
    return new_lb_dict
