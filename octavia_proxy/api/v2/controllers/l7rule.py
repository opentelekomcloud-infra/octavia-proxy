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
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import l7rule as l7rule_types
from octavia_proxy.api.common import types
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
    def get_one(self, id, fields=None):
        """Gets a single l7rule's details."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)

        l7rule = self.find_l7rule(
            context, self.l7policy_id, id, is_parallel)[0]

        self._auth_validate_action(context, l7rule.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            l7rule = self._filter_fields([l7rule], fields)[0]
        return l7rule_types.L7RuleRootResponse(rule=l7rule)

    @wsme_pecan.wsexpose(l7rule_types.L7RulesRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all l7rules of a l7policy."""
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
            context, 'l7rules', is_parallel, self.l7policy_id, query_filter
        )

        if allow_pagination:
            result_to_dict = [l7rule_obj.to_dict() for l7rule_obj in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, l7rule_types.L7RuleFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)
        return l7rule_types.L7RulesRootResponse(
            rules=result, rules_links=links)

    @wsme_pecan.wsexpose(l7rule_types.L7RuleRootResponse,
                         body=l7rule_types.L7RuleRootPOST, status_code=201)
    def post(self, rule_):
        """Creates a l7rule on an l7policy."""

        l7rule = rule_.rule
        context = pecan_request.context.get('octavia_context')
        l7policy = self.find_l7policy(context, id=self.l7policy_id)[0]

        if not l7rule.project_id and context.project_id:
            l7rule.project_id = context.project_id

        self._auth_validate_action(context, l7rule.project_id,
                                   constants.RBAC_POST)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(l7policy.provider)

        result = driver_utils.call_provider(
            driver.name, driver.l7rule_create,
            context.session,
            l7policy.id,
            l7rule
        )

        return l7rule_types.L7RuleRootResponse(rule=result)

    @wsme_pecan.wsexpose(l7rule_types.L7RuleRootResponse,
                         wtypes.text, body=l7rule_types.L7RuleRootPUT,
                         status_code=200)
    def put(self, id, l7rule_):
        """Updates a l7rule."""
        l7rule = l7rule_.rule
        context = pecan_request.context.get('octavia_context')

        l7policy = self.find_l7policy(context, id=self.l7policy_id)[0]
        orig_l7rule = self.find_l7rule(context, self.l7policy_id, id)[0]

        self._auth_validate_action(context, l7policy.project_id,
                                   constants.RBAC_PUT)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(l7policy.provider)

        l7rule_dict = l7rule.to_dict(render_unsets=False)

        result = driver_utils.call_provider(
            driver.name, driver.l7rule_update,
            context.session,
            self.l7policy_id,
            orig_l7rule,
            l7rule_dict
        )

        return l7rule_types.L7RuleRootResponse(rule=result)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a l7rule."""
        context = pecan_request.context.get('octavia_context')

        l7rule = self.find_l7rule(context, self.l7policy_id, id)[0]

        self._auth_validate_action(
            context, l7rule.project_id,
            constants.RBAC_DELETE)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(l7rule.provider)

        driver_utils.call_provider(
            driver.name, driver.l7rule_delete,
            context.session,
            self.l7policy_id,
            l7rule)

    def _graph_create(self, session, lb, rule, provider=None):
        driver = driver_factory.get_driver(provider)
        rule_response = driver_utils.call_provider(
            driver.name, driver.l7rule_create, session,
            self.l7policy_id, rule)
        if not rule_response:
            context = pecan_request.context.get('octavia_context')
            driver_utils.call_provider(
                driver.name, driver.loadbalancer_delete,
                context.session,
                lb, cascade=True)
            raise Exception("Rule creation failed")
        rule_full_response = rule_response.to_full_response()
        return rule_full_response
