#    Copyright 2014 Rackspace
#    Copyright 2016 Blue Box, an IBM Company
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

from oslo_log import log as logging
from pecan import abort as pecan_abort
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import member as member_types
from octavia_proxy.common import constants


LOG = logging.getLogger(__name__)


class MemberController(base.BaseController):
    RBAC_TYPE = constants.RBAC_MEMBER

    def __init__(self, pool_id):
        super().__init__()
        self.pool_id = pool_id

    @wsme_pecan.wsexpose(member_types.MemberRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get(self, id, fields=None):
        """Gets a single pool member's details."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(member_types.MembersRootResponse, [wtypes.text],
                         ignore_extra_args=True)
    def get_all(self, fields=None):
        """Lists all pool members of a pool."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(member_types.MemberRootResponse,
                         body=member_types.MemberRootPOST, status_code=201)
    def post(self, member_):
        """Creates a pool member on a pool."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(member_types.MemberRootResponse,
                         wtypes.text, body=member_types.MemberRootPUT,
                         status_code=200)
    def put(self, id, member_):
        """Updates a pool member."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a pool member."""
        pecan_abort(501)


class MembersController(MemberController):

    def __init__(self, pool_id):
        super().__init__(pool_id)

    @wsme_pecan.wsexpose(None, wtypes.text,
                         body=member_types.MembersRootPUT, status_code=202)
    def put(self, additive_only=False, members_=None):
        """Updates all members."""
        pecan_abort(501)
