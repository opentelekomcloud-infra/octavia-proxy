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


import itertools

from octavia_proxy.policies import availability_zone
from octavia_proxy.policies import base
from octavia_proxy.policies import flavor
from octavia_proxy.policies import healthmonitor
from octavia_proxy.policies import l7policy
from octavia_proxy.policies import l7rule
from octavia_proxy.policies import listener
from octavia_proxy.policies import loadbalancer
from octavia_proxy.policies import member
from octavia_proxy.policies import pool
from octavia_proxy.policies import provider
from octavia_proxy.policies import provider_availability_zone
from octavia_proxy.policies import provider_flavor
from octavia_proxy.policies import quota


def list_rules():
    return itertools.chain(
        base.list_rules(),
        flavor.list_rules(),
        availability_zone.list_rules(),
        healthmonitor.list_rules(),
        l7policy.list_rules(),
        l7rule.list_rules(),
        listener.list_rules(),
        loadbalancer.list_rules(),
        member.list_rules(),
        pool.list_rules(),
        provider.list_rules(),
        quota.list_rules(),
        provider_flavor.list_rules(),
        provider_availability_zone.list_rules(),
    )
