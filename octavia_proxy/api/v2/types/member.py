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

from octavia_proxy.api.common import types
from octavia_proxy.common import constants


class BaseMemberType(types.BaseType):
    _type_to_model_map = {'admin_state_up': 'enabled',
                          'address': 'ip_address'}
    _child_map = {}


class MemberResponse(BaseMemberType):
    """Defines which attributes are to be shown on any response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    admin_state_up = wtypes.wsattr(bool)
    address = wtypes.wsattr(types.IPAddressType())
    protocol_port = wtypes.wsattr(wtypes.IntegerType())
    weight = wtypes.wsattr(wtypes.IntegerType())
    backup = wtypes.wsattr(bool)
    subnet_id = wtypes.wsattr(wtypes.UuidType())
    project_id = wtypes.wsattr(wtypes.StringType())
    created_at = wtypes.wsattr(wtypes.datetime.datetime)
    updated_at = wtypes.wsattr(wtypes.datetime.datetime)
    monitor_address = wtypes.wsattr(types.IPAddressType())
    monitor_port = wtypes.wsattr(wtypes.IntegerType())
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType()))

    @classmethod
    def from_data_model(cls, data_model, children=False):
        member = super(MemberResponse, cls).from_data_model(
            data_model, children=children)
        return member

    @classmethod
    def from_sdk_object(cls, sdk_entity):
        member = cls()
        for key in [
            'id', 'name', 'operating_status', 'provisioning_status',
            'address', 'protocol_port', 'weight', 'backup',
            'subnet_id', 'project_id', 'monitor_address',
            'monitor_port', 'tags'
        ]:
            v = sdk_entity.get(key)
            if v:
                setattr(member, key, v)

        member.admin_state_up = sdk_entity.is_admin_state_up
        for attr in ['created_at', 'updated_at']:
            v = sdk_entity.get(attr)
            if v:
                setattr(member, attr, parser.parse(v) or None)
        return member

    def to_full_response(self):
        full_response = MemberFullResponse()

        for key in [
            'id', 'name', 'operating_status', 'provisioning_status',
            'address', 'protocol_port', 'weight',
            'subnet_id', 'project_id', 'monitor_address',
            'monitor_port', 'tags'
        ]:
            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(full_response, key, v)

        full_response.admin_state_up = self.admin_state_up
        full_response.backup = self.backup
        full_response.created_at = self.created_at
        full_response.updated_at = self.updated_at
        return full_response


class MemberFullResponse(MemberResponse):
    @classmethod
    def _full_response(cls):
        return True


class MemberRootResponse(types.BaseType):
    member = wtypes.wsattr(MemberResponse)


class MembersRootResponse(types.BaseType):
    members = wtypes.wsattr([MemberResponse])
    members_links = wtypes.wsattr([types.PageType])


class MemberPOST(BaseMemberType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    address = wtypes.wsattr(types.IPAddressType(), mandatory=True)
    protocol_port = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_PORT_NUMBER, maximum=constants.MAX_PORT_NUMBER),
        mandatory=True)
    weight = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_WEIGHT, maximum=constants.MAX_WEIGHT),
        default=constants.DEFAULT_WEIGHT)
    backup = wtypes.wsattr(bool, default=False)
    subnet_id = wtypes.wsattr(wtypes.UuidType())
    # TODO(johnsom) Remove after deprecation (R series)
    project_id = wtypes.wsattr(wtypes.StringType(max_length=36))
    monitor_port = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_PORT_NUMBER, maximum=constants.MAX_PORT_NUMBER),
        default=None)
    monitor_address = wtypes.wsattr(types.IPAddressType(), default=None)
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))


class MemberRootPOST(types.BaseType):
    member = wtypes.wsattr(MemberPOST)


class MemberPUT(BaseMemberType):
    """Defines attributes that are acceptable of a PUT request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool)
    weight = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_WEIGHT, maximum=constants.MAX_WEIGHT))
    backup = wtypes.wsattr(bool)
    monitor_port = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_PORT_NUMBER, maximum=constants.MAX_PORT_NUMBER))
    monitor_address = wtypes.wsattr(types.IPAddressType())
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))


class MemberRootPUT(types.BaseType):
    member = wtypes.wsattr(MemberPUT)


class MembersRootPUT(types.BaseType):
    members = wtypes.wsattr([MemberPOST])


class MemberSingleCreate(BaseMemberType):
    """Defines mandatory and optional attributes of a POST request."""
    name = wtypes.wsattr(wtypes.StringType(max_length=255))
    admin_state_up = wtypes.wsattr(bool, default=True)
    address = wtypes.wsattr(types.IPAddressType(), mandatory=True)
    protocol_port = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_PORT_NUMBER, maximum=constants.MAX_PORT_NUMBER),
        mandatory=True)
    weight = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_WEIGHT, maximum=constants.MAX_WEIGHT),
        default=constants.DEFAULT_WEIGHT)
    backup = wtypes.wsattr(bool, default=False)
    subnet_id = wtypes.wsattr(wtypes.UuidType())
    monitor_port = wtypes.wsattr(wtypes.IntegerType(
        minimum=constants.MIN_PORT_NUMBER, maximum=constants.MAX_PORT_NUMBER))
    monitor_address = wtypes.wsattr(types.IPAddressType())
    tags = wtypes.wsattr(wtypes.ArrayType(wtypes.StringType(max_length=255)))

    def to_member_post(self, project_id=None):
        member_post = MemberPOST()

        for key in [
            'name',
            'address', 'protocol_port', 'weight',
            'subnet_id', 'project_id', 'monitor_address',
            'monitor_port', 'tags'
        ]:
            if hasattr(self, key):
                v = getattr(self, key)
                if v:
                    setattr(member_post, key, v)

        member_post.admin_state_up = self.admin_state_up
        member_post.backup = self.backup
        member_post.project_id = project_id

        return member_post


class MemberStatusResponse(BaseMemberType):
    """Defines which attributes are to be shown on status response."""
    id = wtypes.wsattr(wtypes.UuidType())
    name = wtypes.wsattr(wtypes.StringType())
    operating_status = wtypes.wsattr(wtypes.StringType())
    provisioning_status = wtypes.wsattr(wtypes.StringType())
    address = wtypes.wsattr(types.IPAddressType())
    protocol_port = wtypes.wsattr(wtypes.IntegerType())

    @classmethod
    def from_data_model(cls, data_model, children=False):
        member = super(MemberStatusResponse, cls).from_data_model(
            data_model, children=children)

        if not member.name:
            member.name = ""

        return member
