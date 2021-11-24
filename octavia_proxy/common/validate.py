# Copyright 2016 Blue Box, an IBM Company
# All Rights Reserved.
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

"""
Several handy validation functions that go beyond simple type checking.
Defined here so these can also be used at deeper levels than the API.
"""
import re
import rfc3986
import netaddr
from oslo_config import cfg

from octavia_proxy.common import constants, exceptions
from octavia_proxy.i18n import _

CONF = cfg.CONF


def url_path(url_path):
    """Raises an error if the url_path doesn't look like a URL Path."""
    try:
        p_url = rfc3986.urlparse(rfc3986.normalize_uri(url_path))

        invalid_path = (
            p_url.scheme or p_url.userinfo or p_url.host or
            p_url.port or
            p_url.path is None or
            not p_url.path.startswith('/')
        )

        if invalid_path:
            raise exceptions.InvalidURLPath(url_path=url_path)
    except Exception as e:
        raise exceptions.InvalidURLPath(url_path=url_path) from e
    return True


def check_session_persistence(SP_dict):
    try:
        if SP_dict['cookie_name']:
            if SP_dict['type'] != constants.SESSION_PERSISTENCE_APP_COOKIE:
                raise exceptions.ValidationException(detail=_(
                    'Field "cookie_name" can only be specified with session '
                    'persistence of type "APP_COOKIE".'))
            bad_cookie_name = re.compile(r'[\x00-\x20\x22\x28-\x29\x2c\x2f'
                                         r'\x3a-\x40\x5b-\x5d\x7b\x7d\x7f]+')
            valid_chars = re.compile(r'[\x00-\xff]+')
            if (bad_cookie_name.search(SP_dict['cookie_name']) or
                    not valid_chars.search(SP_dict['cookie_name'])):
                raise exceptions.ValidationException(detail=_(
                    'Supplied "cookie_name" is invalid.'))
        if (SP_dict['type'] == constants.SESSION_PERSISTENCE_APP_COOKIE and
                not SP_dict['cookie_name']):
            raise exceptions.ValidationException(detail=_(
                'Field "cookie_name" must be specified when using the '
                '"APP_COOKIE" session persistence type.'))
    except exceptions.ValidationException:
        raise
    except Exception as e:
        raise exceptions.ValidationException(detail=_(
            'Invalid session_persistence provided.')) from e


def subnet_exists(subnet_id, context=None):
    """Raises an exception when a subnet does not exist."""
    session = context.session
    try:
        subnet = session.network.get_subnet(subnet_id)
    except Exception as e:
        raise exceptions.InvalidSubresource(
            resource='Subnet', id=subnet_id) from e
    return subnet


def network_exists_optionally_contains_subnet(network_id, subnet_id=None,
                                              context=None):
    """Raises an exception when a network does not exist.
    If a subnet is provided, also validate the network contains that subnet.
    """
    session = context.session
    try:
        network = session.network.get_network(network_id)
    except Exception as e:
        raise exceptions.InvalidSubresource(
            resource='Network', id=network_id) from e
    if subnet_id:
        if not network.subnet_ids or subnet_id not in network.subnet_ids:
            raise exceptions.InvalidSubresource(resource='Subnet',
                                                id=subnet_id)
    return network


def is_ip_member_of_cidr(address, cidr):
    if netaddr.IPAddress(address) in netaddr.IPNetwork(cidr):
        return True
    return False
