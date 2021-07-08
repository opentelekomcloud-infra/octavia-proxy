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

from oslo_config import cfg
from oslo_log import log as logging
from pecan import abort as pecan_abort
from wsmeext import pecan as wsme_pecan
from wsme import types as wtypes

from octavia_proxy.api.v2.types import health_monitor as hm_types
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.common import constants as consts


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class HealthMonitorController(base.BaseController):
    RBAC_TYPE = consts.RBAC_HEALTHMONITOR

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a single healthmonitor's details."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(hm_types.HealthMonitorsRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Gets all health monitors."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse,
                         body=hm_types.HealthMonitorRootPOST, status_code=201)
    def post(self, health_monitor_):
        """Creates a health monitor on a pool."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(hm_types.HealthMonitorRootResponse, wtypes.text,
                         body=hm_types.HealthMonitorRootPUT, status_code=200)
    def put(self, id, health_monitor_):
        """Updates a health monitor."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a health monitor."""
        pecan_abort(501)
