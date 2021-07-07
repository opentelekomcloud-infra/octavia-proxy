#    Copyright 2016 Intel Corporation
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
from oslo_log import log as logging

from octavia.common import constants

from octavia_proxy.common.config import cfg

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PaginationHelper(object):
    """Class helping to interact with pagination functionality

    Pass this class to `db.repositories` to apply it on query
    """
    _auxiliary_arguments = ('limit', 'marker',
                            'sort', 'sort_key', 'sort_dir',
                            'fields', 'page_reverse',
                            )

    def __init__(self, params, sort_dir=constants.DEFAULT_SORT_DIR):
        """Pagination Helper takes params and a default sort direction

        :param params: Contains the following:
                       limit: maximum number of items to return
                       marker: the last item of the previous page; we return
                               the next results after this value.
                       sort: array of attr by which results should be sorted
        :param sort_dir: default direction to sort (asc, desc)
        """
        self.marker = params.get('marker')
        # self.sort_dir = self._validate_sort_dir(sort_dir)
        # self.limit = self._parse_limit(params)
        # self.sort_keys = self._parse_sort_keys(params)
        self.params = params
        self.filters = None
        self.page_reverse = params.get('page_reverse', 'False')
