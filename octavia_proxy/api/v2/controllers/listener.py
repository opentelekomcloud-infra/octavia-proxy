#  Copyright 2021 Open Telekom Cloud, T-Systems International
#  Copyright 2014 Rackspace
#  Copyright 2016 Blue Box, an IBM Company
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
from oslo_config import cfg
from oslo_log import log as logging
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.common import constants

from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.drivers import driver_factory

from octavia_proxy.api.v2.types import listener as listener_types
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.common import types


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ListenersController(base.BaseController):
    RBAC_TYPE = constants.RBAC_LISTENER

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(listener_types.ListenerRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a single listener's details."""
        pcontext = pecan_request.context
        context = pecan_request.context.get('octavia_context')
        query_params = pcontext.get(constants.PAGINATION_HELPER).params
        is_parallel = query_params.pop('is_parallel', True)

        result = self.find_listener(context, id, is_parallel)[0]

        self._auth_validate_action(context, result.project_id,
                                   constants.RBAC_GET_ONE)

        if fields is not None:
            result = self._filter_fields([result], fields)[0]
        return listener_types.ListenerRootResponse(
            listener=result)

    @wsme_pecan.wsexpose(listener_types.ListenersRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all listeners."""
        pcontext = pecan_request.context
        context = pcontext.get('octavia_context')

        query_filter = self._auth_get_all(context, project_id)
        pagination_helper = pcontext.get(constants.PAGINATION_HELPER)
        # query_params = pagination_helper.params
        # TODO: fix filtering and sorting, especially for multiple providers
        # query_filter.update(query_params)
        is_parallel = query_filter.pop('is_parallel', True)

        links = []
        result = driver_invocation(
            context, 'listeners', is_parallel, query_filter
        )

        if pagination_helper:
            result_to_dict = [lstnr_obj.to_dict() for lstnr_obj in result]
            temp_result, temp_links = pagination_helper.apply(result_to_dict)
            links = [types.PageType(**link) for link in temp_links]
            result = self._convert_sdk_to_type(
                temp_result, listener_types.ListenerFullResponse
            )

        if fields is not None:
            result = self._filter_fields(result, fields)
        return listener_types.ListenersRootResponse(
            listeners=result, listeners_links=links)

    @wsme_pecan.wsexpose(listener_types.ListenerRootResponse,
                         body=listener_types.ListenerRootPOST, status_code=201)
    def post(self, listener_):
        """Creates a listener on a load balancer."""
        listener = listener_.listener
        context = pecan_request.context.get('octavia_context')

        if not listener.project_id and context.project_id:
            listener.project_id = context.project_id

        self._auth_validate_action(
            context, listener.project_id, constants.RBAC_POST)

        load_balancer = self.find_load_balancer(
            context, listener.loadbalancer_id)[0]

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(load_balancer.provider)

        obj_dict = listener.to_dict(render_unsets=False)
        obj_dict['id'] = None

        # Dispatch to the driver
        result = driver_utils.call_provider(
            driver.name, driver.listener_create,
            context.session,
            listener)

        return listener_types.ListenerRootResponse(listener=result)

    @wsme_pecan.wsexpose(listener_types.ListenerRootResponse,
                         wtypes.text, status_code=200,
                         body=listener_types.ListenerRootPUT)
    def put(self, id, listener_):
        """Updates a listener."""
        listener = listener_.listener
        context = pecan_request.context.get('octavia_context')

        orig_listener = self.find_listener(context, id)[0]

        self._auth_validate_action(
            context, orig_listener.project_id,
            constants.RBAC_PUT)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(orig_listener.provider)

        # Prepare the data for the driver data model
        lsnr_dict = listener.to_dict(render_unsets=False)

        result = driver_utils.call_provider(
            driver.name, driver.listener_update,
            context.session,
            orig_listener, lsnr_dict)

        return listener_types.ListenerRootResponse(listener=result)

    @wsme_pecan.wsexpose(None, wtypes.text, status_code=204)
    def delete(self, id):
        """Deletes a listener from a load balancer."""
        context = pecan_request.context.get('octavia_context')

        listener = self.find_listener(context, id)[0]

        self._auth_validate_action(
            context, listener.project_id,
            constants.RBAC_DELETE)

        # Load the driver early as it also provides validation
        driver = driver_factory.get_driver(listener.provider)

        driver_utils.call_provider(
            driver.name, driver.listener_delete,
            context.session,
            listener)
