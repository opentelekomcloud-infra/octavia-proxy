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
from operator import itemgetter

from dateutil.tz import tzlocal
from oslo_log import log as logging
from pecan import request

from octavia_proxy.common import constants
from octavia_proxy.common import exceptions
from octavia_proxy.common.config import cfg

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PaginationHelper(object):
    """Class helping to interact with pagination functionality
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
        self.sort_dir = self._validate_sort_dir(sort_dir)
        self.sort_key = params.get('sort_key')
        self.sort = params.get('sort')
        self.limit = self._parse_limit(params)
        self.marker = params.get('marker')
        self.sort_keys_dirs = self._parse_sort_keys(params)
        self.params = params
        self.filters = None
        self.page_reverse = params.get('page_reverse', 'False')

    @staticmethod
    def _parse_limit(params):
        """Method for limit parsing.
        :param params: Query params.
        :return: Limit value
        :rtype: int
        """
        if not str(CONF.api_settings.pagination_max_limit).isdigit():
            page_max_limit = None
        else:
            page_max_limit = int(CONF.api_settings.pagination_max_limit)
        limit = params.get('limit', page_max_limit)
        try:
            # Deal with limit being a string or int meaning 'Unlimited'
            if not str(limit).isdigit():
                limit = None
            # If we don't have a max, just use whatever limit is specified
            elif page_max_limit is None:
                limit = int(limit)
            # Otherwise, we need to compare against the max
            else:
                limit = min(int(limit), page_max_limit)
        except ValueError as e:
            raise exceptions.InvalidLimit(key=limit) from e
        return limit

    @staticmethod
    def _validate_sort_dir(sort_dir):
        sort_dir = sort_dir.lower()
        if sort_dir not in constants.ALLOWED_SORT_DIR:
            raise exceptions.InvalidSortDirection(key=sort_dir)
        return sort_dir

    def _parse_sort_keys(self, params):
        sort_keys_dirs = []
        sort = params.get('sort')
        sort_keys = params.get('sort_key')
        if sort:
            for sort_dir_key in sort.split(","):
                comps = sort_dir_key.split(":")
                if len(comps) == 1:  # Use default sort order
                    sort_keys_dirs.append((comps[0], self.sort_dir))
                elif len(comps) == 2:
                    sort_keys_dirs.append(
                        (comps[0], self._validate_sort_dir(comps[1])))
                else:
                    raise exceptions.InvalidSortKey(key=comps)
        elif sort_keys:
            sort_keys = sort_keys.split(',')
            sort_dirs = params.get('sort_dir')
            if not sort_dirs:
                sort_dirs = [self.sort_dir] * len(sort_keys)
            else:
                sort_dirs = sort_dirs.split(',')

            if len(sort_dirs) < len(sort_keys):
                sort_dirs += [self.sort_dir] * (len(sort_keys) -
                                                len(sort_dirs))
            for sk, sd in zip(sort_keys, sort_dirs):
                sort_keys_dirs.append((sk, self._validate_sort_dir(sd)))

        return sort_keys_dirs

    def _marker_index(self, entities_list):
        entity = [entity for entity in entities_list if entity['id'] ==
                  self.marker]
        if entity:
            return list.index(entities_list, entity[0])

    def _make_link(self, entities_list, rel, limit=None, marker=None):
        """Create links.

        :param entities_list: List of resources for pagination
        :param rel: Prompt of the previous or next page. Value can be "next" or
                    "previous".
        :return: Link on previous or next page.
        :rtype: dict
        """
        link_attr = []
        link = {}
        if CONF.api_settings.api_base_uri:
            path_url = "{api_base_uri}{path}".format(
                api_base_uri=CONF.apisettings.api_base_uri.rstrip('/'),
                path=request.path
            )
        else:
            path_url = request.path_url
        if entities_list:
            if limit:
                link_attr = ["limit={}".format(limit)]
            if marker:
                link_attr.append("marker={}".format(marker))
            if self.page_reverse:
                link_attr.append("page_reverse={}".format(self.page_reverse))
            if self.sort:
                link_attr.append("sort={}".format(self.sort))
            if self.sort_key:
                link_attr.append("sort_key={}".format(self.sort_key))
            link = {
                "rel": "{rel}".format(rel=rel),
                "href": "{url}?{params}".format(
                    url=path_url,
                    params="&".join(link_attr)
                )
            }
        return link

    def _multikeysort(self, entities_list, sort_keys_dirs):
        """Sort a list of dictionary objects or objects by multiple keys.

        :param entities_list: A list of dictionary objects or objects
        :param sort_keys_dirs: A list of entities fields and directions
                               to sort by.
        :return: Sorted list of entities.
        :rtype: list
        """

        def is_reversed(current_sort_dir):
            return current_sort_dir.lower() == 'desc'

        for key, direction in reversed(sort_keys_dirs):
            entities_list.sort(
                key=itemgetter(key), reverse=is_reversed(direction)
            )
        return entities_list

    def _make_filtering(self):
        pass

    def _make_sorting(self, entities_list, sort_keys_dirs,
                      sort_dir=constants.DEFAULT_SORT_DIR):
        """Sorting

        :param entities_list: List of resources for sorting
        :param sort_keys_dirs: List of tuples of sort keys and directions
        :param sort_dir: Sort direction for default sorting keys
        :return: Sorting list of entities
        :rtype: list
        """
        if entities_list:
            keys_only = [k[0] for k in sort_keys_dirs]
            for key in constants.DEFAULT_SORT_KEYS:
                if key not in keys_only and key in entities_list[0]:
                    sort_keys_dirs.append((key, sort_dir))
            return self._multikeysort(entities_list, sort_keys_dirs)

    def _make_pagination(self, entities_list):
        """ Pagination

        :param entities_list: List of resources for pagination
        :return: Pagination page with links.
        :rtype: tuple
        """
        result = []
        links = []

        if entities_list:
            list_len = len(entities_list)
            local_limit = self.limit if self.limit else list_len
            if self.page_reverse:
                entities_list.reverse()

            if self.marker:
                marker_i = self._marker_index(entities_list=entities_list)
                if marker_i is None and self.limit is None:
                    result.extend(entities_list)
                elif marker_i is None and self.limit < list_len:
                    result.extend(entities_list[0: local_limit])
                    links.append(self._make_link(
                        entities_list=entities_list,
                        rel="next",
                        limit=self.limit,
                        marker=entities_list[local_limit].get('id')
                    ))
                elif marker_i == list_len - 1:
                    result.extend(entities_list[marker_i: list_len])
                    links.append(self._make_link(
                        entities_list=entities_list,
                        rel="previous",
                        limit=self.limit,
                        marker=self.marker
                    ))
                elif marker_i + local_limit < list_len - 1:
                    result.extend(entities_list[
                                  marker_i + 1: marker_i + 1 + local_limit])
                    links.append(self._make_link(
                        entities_list=entities_list,
                        rel="previous",
                        limit=self.limit,
                        marker=self.marker
                    )),
                    links.append(self._make_link(
                        entities_list=entities_list,
                        rel="next",
                        limit=self.limit,
                        marker=entities_list[marker_i + 1 +
                                             local_limit].get('id')
                    ))
                else:
                    result.extend(entities_list[marker_i + 1: list_len])
                    links.append(self._make_link(
                        entities_list=entities_list,
                        rel="previous",
                        limit=self.limit,
                        marker=self.marker
                    ))
            elif self.limit and self.limit < list_len:
                result.extend(entities_list[0: local_limit])
                links.append(self._make_link(
                    entities_list=entities_list,
                    rel="next",
                    limit=self.limit,
                    marker=entities_list[local_limit].get('id')
                ))
            else:
                result.extend(entities_list)
        # links = [types.PageType(**link) for link in links]
        return result, links

    def apply(self, entities_list):
        # Filtering values
        # Sorting values
        entities_list = self.apply_tz(entities_list)
        if CONF.api_settings.allow_sorting:
            self._make_sorting(
                entities_list=entities_list,
                sort_keys_dirs=self.sort_keys_dirs,
                sort_dir=self.sort_dir
            )
        # Paginating values
        if CONF.api_settings.allow_pagination:
            return self._make_pagination(entities_list=entities_list)
        else:
            return entities_list

    def apply_tz(self, entities_list, date_keys=None):
        if date_keys is None:
            date_keys = ['updated_at', 'created_at']
        for entity in entities_list:
            for dk in date_keys:
                if dk in entity:
                    entity.update(
                        {dk: entity.get(dk).replace(tzinfo=tzlocal())}
                    )
        return entities_list
