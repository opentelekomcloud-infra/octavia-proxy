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

from oslo_config import cfg
from oslo_log import log as logging
from pecan import abort as pecan_abort
from pecan import expose as pecan_expose
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import l7policy as l7policy_types
from octavia_proxy.common import constants


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class L7PolicyController(base.BaseController):
    RBAC_TYPE = constants.RBAC_L7POLICY

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(l7policy_types.L7PolicyRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get(self, id, fields=None):
        """Gets a single l7policy's details."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(l7policy_types.L7PoliciesRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all l7policies of a listener."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(l7policy_types.L7PolicyRootResponse,
                         body=l7policy_types.L7PolicyRootPOST, status_code=201)
    def post(self, l7policy_):
        """Creates a l7policy on a listener."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(l7policy_types.L7PolicyRootResponse,
                         wtypes.text, body=l7policy_types.L7PolicyRootPUT,
                         status_code=200)
    def put(self, id, l7policy_):
        """Updates a l7policy."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a l7policy."""
        pecan_abort(501)

    @pecan_expose()
    def _lookup(self, l7policy_id, *remainder):
        """Overridden pecan _lookup method for custom routing.

        Verifies that the l7policy passed in the url exists, and if so decides
        which controller, if any, should control be passed.
        """
        pecan_abort(501)
