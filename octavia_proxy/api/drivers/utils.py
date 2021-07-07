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
from oslo_config import cfg
from oslo_context import context as oslo_context
from oslo_log import log as logging
from oslo_utils import excutils
from stevedore import driver as stevedore_driver

from octavia.common import constants
from octavia.common import data_models
from octavia.common import exceptions
from octavia.common.tls_utils import cert_parser
from octavia.i18n import _

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
            else _("This feature is not implemented by this provider."))
        usr_fault_string = (
            e.user_fault_string
            if hasattr(e, "user_fault_string")
            else _("This feature is not implemented by the provider."))
        LOG.info("Provider '%s' raised a not implemented error: %s",
                 provider, op_fault_string)
        raise exceptions.ProviderNotImplementedError(
            prov=provider, user_msg=usr_fault_string)
    except lib_exceptions.UnsupportedOptionError as e:
        LOG.info("Provider '%s' raised an unsupported option error: "
                 "%s", provider, e.operator_fault_string)
        raise exceptions.ProviderUnsupportedOptionError(
            prov=provider, user_msg=e.user_fault_string)
    except Exception as e:
        LOG.exception("Provider '%s' raised an unknown error: %s",
                      provider, str(e))
        raise exceptions.ProviderDriverError(prov=provider, user_msg=e)


def _base_to_provider_dict(current_dict, include_project_id=False):
    new_dict = copy.deepcopy(current_dict)
    if 'provisioning_status' in new_dict:
        del new_dict['provisioning_status']
    if 'operating_status' in new_dict:
        del new_dict['operating_status']
    if 'provider' in new_dict:
        del new_dict['provider']
    if 'created_at' in new_dict:
        del new_dict['created_at']
    if 'updated_at' in new_dict:
        del new_dict['updated_at']
    if 'enabled' in new_dict:
        new_dict['admin_state_up'] = new_dict.pop('enabled')
    if 'project_id' in new_dict and not include_project_id:
        del new_dict['project_id']
    if 'tenant_id' in new_dict:
        del new_dict['tenant_id']
    if 'tags' in new_dict:
        del new_dict['tags']
    if 'flavor_id' in new_dict:
        del new_dict['flavor_id']
    if 'topology' in new_dict:
        del new_dict['topology']
    if 'vrrp_group' in new_dict:
        del new_dict['vrrp_group']
    if 'amphorae' in new_dict:
        del new_dict['amphorae']
    if 'vip' in new_dict:
        del new_dict['vip']
    if 'listeners' in new_dict:
        del new_dict['listeners']
    if 'pools' in new_dict:
        del new_dict['pools']
    if 'server_group_id' in new_dict:
        del new_dict['server_group_id']
    return new_dict


# Note: The provider dict returned from this method will have provider
#       data model objects in it.
def lb_dict_to_provider_dict(lb_dict, vip=None, db_pools=None,
                             db_listeners=None, for_delete=False):
    new_lb_dict = _base_to_provider_dict(lb_dict, include_project_id=True)
    new_lb_dict['loadbalancer_id'] = new_lb_dict.pop('id')
    if vip:
        new_lb_dict['vip_address'] = vip.ip_address
        new_lb_dict['vip_network_id'] = vip.network_id
        new_lb_dict['vip_port_id'] = vip.port_id
        new_lb_dict['vip_subnet_id'] = vip.subnet_id
        new_lb_dict['vip_qos_policy_id'] = vip.qos_policy_id
    return new_lb_dict


def _get_secret_data(cert_manager, project_id, secret_ref, for_delete=False):
    """Get the secret from the certificate manager and upload it to the amp.

    :returns: The secret data.
    """
    context = oslo_context.RequestContext(project_id=project_id)
    try:
        secret_data = cert_manager.get_secret(context, secret_ref)
    except Exception as e:
        LOG.warning('Unable to retrieve certificate: %s due to %s.',
                    secret_ref, str(e))
        if for_delete:
            secret_data = None
        else:
            raise exceptions.CertificateRetrievalException(ref=secret_ref)
    # We need to have json convertible data for storing it in
    # persistence jobboard backend.
    if isinstance(secret_data, bytes):
        return secret_data.decode()
    return secret_data


def listener_dict_to_provider_dict(listener_dict, for_delete=False):
    new_listener_dict = _base_to_provider_dict(listener_dict,
                                               include_project_id=True)
    new_listener_dict['listener_id'] = new_listener_dict.pop('id')
    if 'load_balancer_id' in new_listener_dict:
        new_listener_dict['loadbalancer_id'] = new_listener_dict.pop(
            'load_balancer_id')

    # Pull the certs out of the certificate manager to pass to the provider
    if 'tls_certificate_id' in new_listener_dict:
        new_listener_dict['default_tls_container_ref'] = new_listener_dict.pop(
            'tls_certificate_id')
    if 'client_ca_tls_certificate_id' in new_listener_dict:
        new_listener_dict['client_ca_tls_container_ref'] = (
            new_listener_dict.pop('client_ca_tls_certificate_id'))
    if 'client_crl_container_id' in new_listener_dict:
        new_listener_dict['client_crl_container_ref'] = (
            new_listener_dict.pop('client_crl_container_id'))
    listener_obj = data_models.Listener(**listener_dict)
    if (listener_obj.tls_certificate_id or listener_obj.sni_containers or
            listener_obj.client_ca_tls_certificate_id):
        SNI_objs = []
        for sni in listener_obj.sni_containers:
            if isinstance(sni, dict):
                sni_obj = data_models.SNI(**sni)
                SNI_objs.append(sni_obj)
            elif isinstance(sni, str):
                sni_obj = data_models.SNI(tls_container_id=sni)
                SNI_objs.append(sni_obj)
            else:
                raise exceptions.ValidationException(
                    detail=_('Invalid SNI container on listener'))
        listener_obj.sni_containers = SNI_objs
        cert_manager = stevedore_driver.DriverManager(
            namespace='octavia.cert_manager',
            name=CONF.certificates.cert_manager,
            invoke_on_load=True,
        ).driver
        try:
            cert_dict = cert_parser.load_certificates_data(cert_manager,
                                                           listener_obj)
        except Exception as e:
            with excutils.save_and_reraise_exception() as ctxt:
                LOG.warning('Unable to retrieve certificate(s) due to %s.',
                            str(e))
                if for_delete:
                    ctxt.reraise = False
                    cert_dict = {}
        if 'tls_cert' in cert_dict and cert_dict['tls_cert']:
            new_listener_dict['default_tls_container_data'] = (
                cert_dict['tls_cert'].to_dict(recurse=True))
        if 'sni_certs' in cert_dict and cert_dict['sni_certs']:
            sni_data_list = []
            for sni in cert_dict['sni_certs']:
                sni_data_list.append(sni.to_dict(recurse=True))
            new_listener_dict['sni_container_data'] = sni_data_list

        if listener_obj.client_ca_tls_certificate_id:
            cert = _get_secret_data(cert_manager, listener_obj.project_id,
                                    listener_obj.client_ca_tls_certificate_id)
            new_listener_dict['client_ca_tls_container_data'] = cert
        if listener_obj.client_crl_container_id:
            crl_file = _get_secret_data(cert_manager, listener_obj.project_id,
                                        listener_obj.client_crl_container_id)
            new_listener_dict['client_crl_container_data'] = crl_file

    # Format the allowed_cidrs
    if ('allowed_cidrs' in new_listener_dict and
            new_listener_dict['allowed_cidrs'] and
            'cidr' in new_listener_dict['allowed_cidrs'][0]):
        cidrs_dict_list = new_listener_dict.pop('allowed_cidrs')
        new_listener_dict['allowed_cidrs'] = [cidr_dict['cidr'] for
                                              cidr_dict in cidrs_dict_list]

    # Format the sni_containers -> sni_container_refs
    sni_containers = new_listener_dict.pop('sni_containers', None)
    if sni_containers:
        new_listener_dict['sni_container_refs'] = []
        for sni in sni_containers:
            if isinstance(sni, dict):
                new_listener_dict['sni_container_refs'].append(
                    sni['tls_container_id'])
            elif isinstance(sni, str):
                new_listener_dict['sni_container_refs'].append(sni)
            else:
                raise exceptions.ValidationException(
                    detail=_('Invalid SNI container on listener'))

    # Remove the DB back references
    if 'load_balancer' in new_listener_dict:
        del new_listener_dict['load_balancer']
    if 'peer_port' in new_listener_dict:
        del new_listener_dict['peer_port']
    if 'pools' in new_listener_dict:
        del new_listener_dict['pools']
    if 'stats' in new_listener_dict:
        del new_listener_dict['stats']

    if ('default_pool' in new_listener_dict and
            new_listener_dict['default_pool']):
        pool = new_listener_dict.pop('default_pool')
        new_listener_dict['default_pool'] = pool_dict_to_provider_dict(
            pool, for_delete=for_delete)
    return new_listener_dict


def pool_dict_to_provider_dict(pool_dict, for_delete=False):
    new_pool_dict = _base_to_provider_dict(pool_dict, include_project_id=True)
    new_pool_dict['pool_id'] = new_pool_dict.pop('id')

    # Pull the certs out of the certificate manager to pass to the provider
    if 'tls_certificate_id' in new_pool_dict:
        new_pool_dict['tls_container_ref'] = new_pool_dict.pop(
            'tls_certificate_id')
    if 'ca_tls_certificate_id' in new_pool_dict:
        new_pool_dict['ca_tls_container_ref'] = new_pool_dict.pop(
            'ca_tls_certificate_id')
    if 'crl_container_id' in new_pool_dict:
        new_pool_dict['crl_container_ref'] = new_pool_dict.pop(
            'crl_container_id')

    pool_obj = data_models.Pool(**pool_dict)
    if (pool_obj.tls_certificate_id or pool_obj.ca_tls_certificate_id or
            pool_obj.crl_container_id):
        cert_manager = stevedore_driver.DriverManager(
            namespace='octavia.cert_manager',
            name=CONF.certificates.cert_manager,
            invoke_on_load=True,
        ).driver
        try:
            cert_dict = cert_parser.load_certificates_data(cert_manager,
                                                           pool_obj)
        except Exception as e:
            with excutils.save_and_reraise_exception() as ctxt:
                LOG.warning('Unable to retrieve certificate(s) due to %s.',
                            str(e))
                if for_delete:
                    ctxt.reraise = False
                    cert_dict = {}
        if 'tls_cert' in cert_dict and cert_dict['tls_cert']:
            new_pool_dict['tls_container_data'] = (
                cert_dict['tls_cert'].to_dict(recurse=True))

        if pool_obj.ca_tls_certificate_id:
            cert = _get_secret_data(cert_manager, pool_obj.project_id,
                                    pool_obj.ca_tls_certificate_id)
            new_pool_dict['ca_tls_container_data'] = cert

        if pool_obj.crl_container_id:
            crl_file = _get_secret_data(cert_manager, pool_obj.project_id,
                                        pool_obj.crl_container_id)
            new_pool_dict['crl_container_data'] = crl_file

    # Remove the DB back references
    if ('session_persistence' in new_pool_dict and
            new_pool_dict['session_persistence']):
        if 'pool_id' in new_pool_dict['session_persistence']:
            del new_pool_dict['session_persistence']['pool_id']
        if 'pool' in new_pool_dict['session_persistence']:
            del new_pool_dict['session_persistence']['pool']
    if 'l7policies' in new_pool_dict:
        del new_pool_dict['l7policies']
    if 'listeners' in new_pool_dict:
        del new_pool_dict['listeners']
    if 'load_balancer' in new_pool_dict:
        del new_pool_dict['load_balancer']
    if 'load_balancer_id' in new_pool_dict:
        new_pool_dict['loadbalancer_id'] = new_pool_dict.pop(
            'load_balancer_id')
    if 'health_monitor' in new_pool_dict:
        hm = new_pool_dict.pop('health_monitor')
        new_pool_dict['healthmonitor'] = hm
    if 'members' in new_pool_dict and new_pool_dict['members']:
        members = new_pool_dict.pop('members')
        provider_members = []
        for member in members:
            provider_member = member_dict_to_provider_dict(member)
            provider_members.append(provider_member)
        new_pool_dict['members'] = provider_members
    return new_pool_dict


def member_dict_to_provider_dict(member_dict):
    new_member_dict = _base_to_provider_dict(member_dict,
                                             include_project_id=True)
    new_member_dict['member_id'] = new_member_dict.pop('id')
    if 'ip_address' in new_member_dict:
        new_member_dict['address'] = new_member_dict.pop('ip_address')
    # Remove the DB back references
    if 'pool' in new_member_dict:
        del new_member_dict['pool']
    return new_member_dict


def vip_dict_to_provider_dict(vip_dict):
    new_vip_dict = {}
    if 'ip_address' in vip_dict:
        new_vip_dict['vip_address'] = vip_dict['ip_address']
    if 'network_id' in vip_dict:
        new_vip_dict['vip_network_id'] = vip_dict['network_id']
    if 'port_id' in vip_dict:
        new_vip_dict['vip_port_id'] = vip_dict['port_id']
    if 'subnet_id' in vip_dict:
        new_vip_dict['vip_subnet_id'] = vip_dict['subnet_id']
    if 'qos_policy_id' in vip_dict:
        new_vip_dict['vip_qos_policy_id'] = vip_dict['qos_policy_id']
    if constants.OCTAVIA_OWNED in vip_dict:
        new_vip_dict[constants.OCTAVIA_OWNED] = vip_dict[
            constants.OCTAVIA_OWNED]
    return new_vip_dict


def provider_vip_dict_to_vip_obj(vip_dictionary):
    vip_obj = data_models.Vip()
    if 'vip_address' in vip_dictionary:
        vip_obj.ip_address = vip_dictionary['vip_address']
    if 'vip_network_id' in vip_dictionary:
        vip_obj.network_id = vip_dictionary['vip_network_id']
    if 'vip_port_id' in vip_dictionary:
        vip_obj.port_id = vip_dictionary['vip_port_id']
    if 'vip_subnet_id' in vip_dictionary:
        vip_obj.subnet_id = vip_dictionary['vip_subnet_id']
    if 'vip_qos_policy_id' in vip_dictionary:
        vip_obj.qos_policy_id = vip_dictionary['vip_qos_policy_id']
    if constants.OCTAVIA_OWNED in vip_dictionary:
        vip_obj.octavia_owned = vip_dictionary[constants.OCTAVIA_OWNED]
    return vip_obj
