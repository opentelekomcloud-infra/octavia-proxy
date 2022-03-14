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
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import member as member_types
from octavia_proxy.api.common import types
from octavia_proxy.common import constants

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class MemberController(base.BaseController):
    RBAC_TYPE = constants.RBAC_MEMBER

    def __init__(self, pool_id):
        super().__init__()
        self.pool_id = pool_id

    @wsme_pecan.wsexpose(member_types.MemberRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a single pool member's details."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)
        member = self.find_member(context, self.pool_id, id, is_parallel)[0]

        self._auth_validate_action(context, member.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            member = self._filter_fields([member], fields)[0]
        return member_types.MemberRootResponse(member=member)

    @wsme_pecan.wsexpose(member_types.MembersRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all pool members of a pool."""
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
            context, 'members', is_parallel, self.pool_id, query_filter
        )

        if allow_pagination:
            result_to_dict = [mmbr_obj.to_dict() for mmbr_obj in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, member_types.MemberFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)
        return member_types.MembersRootResponse(
            members=result, members_links=links)

    @wsme_pecan.wsexpose(member_types.MemberRootResponse,
                         body=member_types.MemberRootPOST, status_code=201)
    def post(self, member_):
        """Creates a pool member on a pool."""

        member = member_.member
        context = pecan_request.context.get('octavia_context')
        pool = self.find_pool(context, id=self.pool_id)[0]

        if not member.project_id and context.project_id:
            member.project_id = context.project_id

        self._auth_validate_action(context, member.project_id,
                                   constants.RBAC_POST)

        provider = pool.provider
        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(provider)

        result = driver_utils.call_provider(
            driver.name, driver.member_create,
            context.session,
            pool.id,
            member
        )

        return member_types.MemberRootResponse(member=result)

    @wsme_pecan.wsexpose(member_types.MemberRootResponse,
                         wtypes.text, body=member_types.MemberRootPUT,
                         status_code=200)
    def put(self, id, member_):
        """Updates a pool member."""
        member = member_.member
        context = pecan_request.context.get('octavia_context')

        pool = self.find_pool(context, id=self.pool_id)[0]
        orig_member = self.find_member(context, self.pool_id, id)[0]

        self._auth_validate_action(context, pool.project_id,
                                   constants.RBAC_PUT)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(pool.provider)

        member_dict = member.to_dict(render_unsets=False)

        result = driver_utils.call_provider(
            driver.name, driver.member_update,
            context.session,
            self.pool_id,
            orig_member,
            member_dict
        )

        return member_types.MemberRootResponse(member=result)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a pool member."""
        context = pecan_request.context.get('octavia_context')

        member = self.find_member(context, self.pool_id, id)[0]

        self._auth_validate_action(
            context, member.project_id,
            constants.RBAC_DELETE)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(member.provider)

        driver_utils.call_provider(
            driver.name, driver.member_delete,
            context.session,
            self.pool_id,
            member)

    def _graph_create(self, session, lb, member_dict, provider=None):
        driver = driver_factory.get_driver(provider)

        new_member_response = driver_utils.call_provider(
            driver.name, driver.member_create,
            session, self.pool_id, member_dict)
        if not new_member_response:
            context = pecan_request.context.get('octavia_context')
            driver_utils.call_provider(
                driver.name, driver.loadbalancer_delete,
                context.session,
                lb, cascade=True)
            raise Exception("Member creation failed")
        new_member_full_response = new_member_response.to_full_response()

        return new_member_full_response


class MembersController(MemberController):

    def __init__(self, pool_id):
        super().__init__(pool_id)

    @wsme_pecan.wsexpose(None, wtypes.text,
                         body=member_types.MembersRootPUT, status_code=202)
    def put(self, additive_only=False, members_=None):
        """Updates all members."""
        pecan_abort(501)
