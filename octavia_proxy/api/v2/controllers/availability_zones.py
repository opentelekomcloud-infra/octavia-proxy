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

from oslo_config import cfg
from oslo_log import log as logging
from pecan import abort as pecan_abort
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan
from pecan import request as pecan_request

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import availability_zones as az_types
from octavia_proxy.api.common import types
from octavia_proxy.common import constants


CONF = cfg.CONF
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

    @wsme_pecan.wsexpose(az_types.AvailabilityZonesRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all Availability Zones."""
        pcontext = pecan_request.context
        context = pcontext.get('octavia_context')

        query_filter = self._auth_get_all(context, project_id)
        pagination_helper = pcontext.get(constants.PAGINATION_HELPER)

        query_params = pagination_helper.params
        query_filter.update(query_params)

        is_parallel = query_filter.pop('is_parallel', True)
        allow_pagination = CONF.api_settings.allow_pagination

        links = []
        result = driver_invocation(
            context, 'availability_zones', is_parallel, query_filter
        )

        if allow_pagination:
            result_to_dict = [az_obj.to_dict() for az_obj in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, az_types.AvailabilityZoneFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)
        return az_types.AvailabilityZonesRootResponse(
            availability_zones=result, availability_zones_links=links)
