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
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import quotas as q_types
from octavia_proxy.common import constants
from octavia_proxy.common import exceptions

LOG = logging.getLogger(__name__)


class QuotasController(base.BaseController):
    RBAC_TYPE = constants.RBAC_QUOTA

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(q_types.QuotaRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, project_id, fields=None):
        """Gets an Quota's detail."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)

        quota = driver_invocation(
            context, 'quota_get', is_parallel, project_id
        )
        if not quota:
            raise exceptions.NotFound(
                resource='Quota',
                id=id)
        quota = quota[0]
        if fields is not None:
            quota = self._filter_fields([quota], fields)[0]
        return q_types.QuotaRootResponse(quota=quota)

    @wsme_pecan.wsexpose(q_types.QuotasRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all Quotas."""
        pcontext = pecan_request.context
        context = pcontext.get('octavia_context')

        query_filter = self._auth_get_all(context, project_id)
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        query_filter.update(query_params)
        is_parallel = query_filter.pop('is_parallel', True)

        links = []
        result = driver_invocation(
            context, 'quotas', is_parallel, query_filter
        )
        if fields is not None:
            result = self._filter_fields(result, fields)
        return q_types.QuotasRootResponse(
            quotas=result, quotas_links=links)
