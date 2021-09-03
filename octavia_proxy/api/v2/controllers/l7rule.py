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

from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import l7rule as l7rule_types
from octavia_proxy.common import constants

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class L7RuleController(base.BaseController):
    RBAC_TYPE = constants.RBAC_L7RULE

    def __init__(self, l7policy_id):
        super().__init__()
        self.l7policy_id = l7policy_id

    @wsme_pecan.wsexpose(l7rule_types.L7RuleRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get(self, id, fields=None):
        """Gets a single l7rule's details."""
        context = pecan_request.context.get('octavia_context')
        l7rule = self.find_l7rule(context, self.l7policy_id, id)

        self._auth_validate_action(context, l7rule.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            l7rule = self._filter_fields([l7rule], fields)[0]
        return l7rule_types.L7RuleRootResponse(l7rule=l7rule)

    @wsme_pecan.wsexpose(l7rule_types.L7RulesRootResponse, [wtypes.text],
                         ignore_extra_args=True)
    def get_all(self, project_id, fields=None):
        """Lists all l7rules of a l7policy."""
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

    @wsme_pecan.wsexpose(l7rule_types.L7RuleRootResponse,
                         body=l7rule_types.L7RuleRootPOST, status_code=201)
    def post(self, rule_):
        """Creates a l7rule on an l7policy."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(l7rule_types.L7RuleRootResponse,
                         wtypes.text, body=l7rule_types.L7RuleRootPUT,
                         status_code=200)
    def put(self, id, l7rule_):
        """Updates a l7rule."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a l7rule."""
        pecan_abort(501)
