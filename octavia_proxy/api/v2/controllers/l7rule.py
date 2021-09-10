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
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import l7rule as l7rule_types
from octavia_proxy.common import constants
from octavia_proxy.common import exceptions

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
        context = pecan_request.context.get('octavia_context')
        l7rule = self.find_l7rule(context, self.l7policy_id, id)

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
        query_params = pcontext.get(constants.PAGINATION_HELPER).params

        query_filter.update(query_params)

        enabled_providers = CONF.api_settings.enabled_provider_drivers
        result = []
        links = []

        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                l7rules = driver_utils.call_provider(
                    driver.name, driver.l7rules,
                    context.session,
                    context.project_id,
                    self.l7policy_id,
                    query_filter)
                if l7rules:
                    LOG.debug('Received %s from %s' % (l7rules, driver.name))
                    result.extend(l7rules)
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

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
        l7policy = self.find_l7policy(context, id=self.l7policy_id)

        if not l7rule.project_id and context.project_id:
            l7rule.project_id = context.project_id

        self._auth_validate_action(context, l7rule.project_id,
                                   constants.RBAC_POST)

        listener = self.find_listener(
            context, l7policy.listener_id)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(listener.provider)

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

        l7policy = self.find_l7policy(context, id=self.l7policy_id)
        orig_l7rule = self.find_l7rule(context, self.l7policy_id, id)

        listener = self.find_listener(
            context, l7policy.listener_id)

        self._auth_validate_action(context, l7policy.project_id,
                                   constants.RBAC_PUT)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(listener.provider)

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
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        l7rule = None

        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                l7rule = driver_utils.call_provider(
                    driver.name, driver.l7rule_get,
                    context.session,
                    context.project_id,
                    self.l7policy_id,
                    id)
                if l7rule:
                    setattr(l7rule, 'provider', provider)
                    break
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')
        if not l7rule:
            raise exceptions.NotFound(
                resource='l7 rule',
                id=id)

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
