# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import itertools
import operator

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg

import octavia_proxy.common.config
from octavia_proxy.common import constants


def list_opts():
    return [
        ('DEFAULT',
         itertools.chain(octavia_proxy.common.config.core_opts)),
        ('api_settings', octavia_proxy.common.config.api_opts),
        add_auth_opts(),
    ]


def add_auth_opts():
    opts = ks_loading.register_session_conf_options(
        cfg.CONF, constants.SERVICE_AUTH)
    opt_list = copy.deepcopy(opts)
    opt_list.insert(0, ks_loading.get_auth_common_conf_options()[0])
    # NOTE(mhickey): There are a lot of auth plugins, we just generate
    # the config options for a few common ones
    plugins = ['password', 'v2password', 'v3password']
    for name in plugins:
        for plugin_option in ks_loading.get_auth_plugin_conf_options(name):
            if all(option.name != plugin_option.name for option in opt_list):
                opt_list.append(plugin_option)
    opt_list.sort(key=operator.attrgetter('name'))
    return (constants.SERVICE_AUTH, opt_list)
