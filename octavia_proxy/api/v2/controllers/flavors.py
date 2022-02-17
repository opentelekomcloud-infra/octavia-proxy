#  Copyright 2021 Open Telekom Cloud, T-Systems International
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
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import flavors as flavor_types
from octavia_proxy.api.common import types
from octavia_proxy.common import constants

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class FlavorsController(base.BaseController):
    RBAC_TYPE = constants.RBAC_FLAVOR

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(flavor_types.FlavorRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a single flavor's details."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)

        flavor = self.find_flavor(context, id, is_parallel)[0]

        if fields is not None:
            flavor = self._filter_fields([flavor], fields)[0]
        return flavor_types.FlavorRootResponse(flavor=flavor)

    @wsme_pecan.wsexpose(flavor_types.FlavorsRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all flavors."""
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
            context, 'flavors', is_parallel, query_filter
        )

        if allow_pagination:
            result_to_dict = [flvr_obj.to_dict() for flvr_obj in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, flavor_types.FlavorFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)
        return flavor_types.FlavorsRootResponse(
            flavors=result, flavors_links=links)

    @wsme_pecan.wsexpose(flavor_types.FlavorRootResponse,
                         body=flavor_types.FlavorRootPOST, status_code=201)
    def post(self, flavor_):
        """Creates a flavor."""
        # NOTE(gtema): normally not allowed to regular user
        pecan_abort(403)

    @wsme_pecan.wsexpose(flavor_types.FlavorRootResponse,
                         wtypes.text, status_code=200,
                         body=flavor_types.FlavorRootPUT)
    def put(self, id, flavor_):
        # NOTE(gtema): normally not allowed to regular user
        pecan_abort(403)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, flavor_id):
        """Deletes a Flavor"""
        # NOTE(gtema): normally not allowed to regular user
        pecan_abort(403)
