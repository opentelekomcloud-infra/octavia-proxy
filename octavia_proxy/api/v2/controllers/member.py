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

from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import member as member_types
from octavia_proxy.common import constants
from octavia_proxy.common import exceptions

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
        context = pecan_request.context.get('octavia_context')
        member = self.find_member(context, self.pool_id, id)

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
        query_params = pcontext.get(constants.PAGINATION_HELPER).params

        query_filter.update(query_params)

        enabled_providers = CONF.api_settings.enabled_provider_drivers
        result = []
        links = []

        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                members = driver_utils.call_provider(
                    driver.name, driver.members,
                    context.session,
                    context.project_id,
                    self.pool_id,
                    query_filter)
                if members:
                    LOG.debug('Received %s from %s' % (members, driver.name))
                    result.extend(members)
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

        if fields is not None:
            result = self._filter_fields(result, fields)
        return member_types.MembersRootResponse(
            members=result, members_links=links)

    @wsme_pecan.wsexpose(member_types.MemberRootResponse,
                         body=member_types.MemberRootPOST, status_code=201)
    def post(self, member_):
        """Creates a pool member on a pool."""

        pool_provider = None
        member = member_.member
        context = pecan_request.context.get('octavia_context')
        pool = self.find_pool(context, id=self.pool_id)

        if not member.project_id and context.project_id:
            member.project_id = context.project_id

        self._auth_validate_action(context, member.project_id,
                                   constants.RBAC_POST)

        if pool.loadbalancers:
            pool_provider = self.find_load_balancer(
                context, pool.loadbalancers[0].id)
        elif pool.listeners:
            pool_provider = self.find_listener(
                context, pool.listeners[0].id)

        provider = pool_provider.provider
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
        provider = None
        member = member_.member
        context = pecan_request.context.get('octavia_context')

        pool = self.find_pool(context, id=self.pool_id)
        orig_member = self.find_member(context, self.pool_id, id)

        if pool.loadbalancers:
            provider = self.find_load_balancer(
                context, pool.loadbalancers[0].id).provider
        elif pool.listeners:
            provider = self.find_listener(
                context, pool.listeners[0].id).provider

        self._auth_validate_action(context, pool.project_id,
                                   constants.RBAC_PUT)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(provider)

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
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        member = None

        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                member = driver_utils.call_provider(
                    driver.name, driver.member_get,
                    context.session,
                    context.project_id,
                    self.pool_id,
                    id)
                if member:
                    setattr(member, 'provider', provider)
                    break
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')
        if not member:
            raise exceptions.NotFound(
                resource='member',
                id=id)

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


class MembersController(MemberController):

    def __init__(self, pool_id):
        super().__init__(pool_id)

    @wsme_pecan.wsexpose(None, wtypes.text,
                         body=member_types.MembersRootPUT, status_code=202)
    def put(self, additive_only=False, members_=None):
        """Updates all members."""
        pecan_abort(501)
