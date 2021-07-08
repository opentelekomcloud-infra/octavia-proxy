#    Copyright 2019 Verizon Media
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
from octavia_proxy.api.v2.types import availability_zones as az_types
from octavia_proxy.common import constants


LOG = logging.getLogger(__name__)


class AvailabilityZonesController(base.BaseController):
    RBAC_TYPE = constants.RBAC_AVAILABILITY_ZONE

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(az_types.AvailabilityZoneRootResponse,
                         wtypes.text, [wtypes.text], ignore_extra_args=True)
    def get_one(self, name, fields=None):
        """Gets an Availability Zone's detail."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(az_types.AvailabilityZonesRootResponse,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, fields=None):
        """Lists all Availability Zones."""
        pecan_abort(501)
