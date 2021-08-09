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

from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.types import flavors as flavor_types
from octavia_proxy.common import constants
from octavia_proxy.common import exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class FlavorsController(base.BaseController):
    RBAC_TYPE = constants.RBAC_FLAVOR

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(flavor_types.FlavorRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_one(self, id, fields=None):
        """Gets a flavor's detail."""
        pecan_abort(501)

    @wsme_pecan.wsexpose(flavor_types.FlavorRootResponse, wtypes.text,
                         [wtypes.text], ignore_extra_args=True)
    def get_all(self, project_id=None, fields=None):
        """Lists all flavors."""
        pcontext = pecan_request.context
        context = pcontext.get('octavia_context')
        query_filter = self._auth_get_all(context, project_id)
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        result = []
        links = []
        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                fl = driver_utils.call_provider(
                    driver.name, driver.flavors,
                    context.session,
                    context.project_id,
                    query_filter)
                if fl:
                    LOG.debug('Received %s from %s' % (fl, driver.name))
                    result.extend(fl)
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

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
