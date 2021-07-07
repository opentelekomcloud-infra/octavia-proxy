#    Copyright 2018 Rackspace
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

from wsme import types as wtypes

from octavia.api.common import types


class ProviderResponse(types.BaseType):
    name = wtypes.wsattr(wtypes.StringType())
    description = wtypes.wsattr(wtypes.StringType())


class ProvidersRootResponse(types.BaseType):
    providers = wtypes.wsattr([ProviderResponse])


class FlavorCapabilitiesResponse(types.BaseType):
    flavor_capabilities = wtypes.wsattr([ProviderResponse])


class AvailabilityZoneCapabilitiesResponse(types.BaseType):
    availability_zone_capabilities = wtypes.wsattr([ProviderResponse])
