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
from pecan import expose as pecan_expose
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base, l7rule
from octavia_proxy.api.v2.types import l7policy as l7policy_types
from octavia_proxy.api.common import types
from octavia_proxy.common import constants
from octavia_proxy.common import exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class L7PoliciesController(base.BaseController):

    RBAC_TYPE = constants.RBAC_L7POLICY

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(l7policy_types.L7PolicyRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a single l7policy's details."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)

        result = self.find_l7policy(context, id, is_parallel)[0]

        self._auth_validate_action(context, result.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            result = self._filter_fields([result], fields)[0]
        return l7policy_types.L7PolicyRootResponse(l7policy=result)

    @wsme_pecan.wsexpose(l7policy_types.L7PoliciesRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all l7policies of a listener."""
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
            context, 'l7policies', is_parallel, query_filter
        )

        if allow_pagination:
            result_to_dict = [l7pol_obj.to_dict() for l7pol_obj in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, l7policy_types.L7PolicyFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)

        return l7policy_types.L7PoliciesRootResponse(
            l7policies=result, l7policies_links=links
        )

    @wsme_pecan.wsexpose(l7policy_types.L7PolicyRootResponse,
                         body=l7policy_types.L7PolicyRootPOST, status_code=201)
    def post(self, l7policy_):
        """Creates a l7policy on a listener."""
        l7policy = l7policy_.l7policy
        context = pecan_request.context.get('octavia_context')
        listener = None

        if not l7policy.project_id and context.project_id:
            l7policy.project_id = context.project_id

        self._auth_validate_action(
            context, l7policy.project_id, constants.RBAC_POST
        )

        if l7policy.listener_id:
            listener = self.find_listener(context, id=l7policy.listener_id)[0]
        else:
            msg = "Must provide listener_id"
            raise exceptions.ValidationException(detail=msg)

        driver = driver_factory.get_driver(listener.provider)
        result = driver_utils.call_provider(
            driver.name, driver.l7policy_create,
            context.session,
            l7policy
        )
        return l7policy_types.L7PolicyRootResponse(l7policy=result)

    @wsme_pecan.wsexpose(l7policy_types.L7PolicyRootResponse,
                         wtypes.text, body=l7policy_types.L7PolicyRootPUT,
                         status_code=200)
    def put(self, id, l7policy_):
        """Updates a l7policy."""
        l7policy = l7policy_.l7policy
        context = pecan_request.context.get('octavia_context')

        orig_l7policy = self.find_l7policy(context, id)[0]

        self._auth_validate_action(
            context, orig_l7policy.project_id,
            constants.RBAC_PUT)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(orig_l7policy.provider)

        # Prepare the data for the driver data model
        l7policy_dict = l7policy.to_dict(render_unsets=False)

        result = driver_utils.call_provider(
            driver.name, driver.l7policy_update,
            context.session,
            orig_l7policy, l7policy_dict)

        return l7policy_types.L7PolicyRootResponse(l7policy=result)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a l7policy."""
        context = pecan_request.context.get('octavia_context')

        l7policy = self.find_l7policy(context, id)[0]

        self._auth_validate_action(
            context, l7policy.project_id,
            constants.RBAC_DELETE)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(l7policy.provider)

        driver_utils.call_provider(
            driver.name, driver.l7policy_delete,
            context.session,
            l7policy)

    @pecan_expose()
    def _lookup(self, l7policy_id, *remainder):
        """Overridden pecan _lookup method for custom routing.

        Verifies that the l7policy passed in the url exists, and if so decides
        which controller, if any, should control be passed.
        """
        context = pecan_request.context.get('octavia_context')
        if l7policy_id and remainder and remainder[0] == 'rules':
            remainder = remainder[1:]
            l7policy = self.find_l7policy(context, l7policy_id)[0]
            if not l7policy:
                LOG.info("L7Policy %s not found.", l7policy_id)
                raise exceptions.NotFound(
                    resource='L7Policy', id=l7policy_id)
            return l7rule.L7RuleController(
                l7policy_id=l7policy.id), remainder
        return None

    def _graph_create(self, session, lb, policy, rules=None, provider=None):
        driver = driver_factory.get_driver(provider)
        policy_response = driver_utils.call_provider(
            driver.name, driver.l7policy_create, session, policy)
        if not policy_response:
            context = pecan_request.context.get('octavia_context')
            driver_utils.call_provider(
                driver.name, driver.loadbalancer_delete,
                context.session,
                lb, cascade=True)
            raise Exception("Policy creation failed")
        new_rules = []
        if not rules:
            rules = policy.rules
        if rules:
            for r in rules:
                rule_post = r.to_l7rule_post(
                    project_id=policy_response.project_id)
                new_rule = l7rule.L7RuleController(policy_response.id).\
                    _graph_create(session, lb, rule_post, provider=provider)
                new_rules.append(new_rule)
        policy_full_response = policy_response.to_full_response(
            rules=new_rules)
        return policy_full_response
