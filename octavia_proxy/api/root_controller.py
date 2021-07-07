from oslo_config import cfg
from oslo_log import log as logging

from pecan import abort as pecan_abort
from pecan import expose as pecan_expose
from pecan import request as pecan_request
from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.v2 import controllers as v2_controller

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class RootController(object):
    """The controller with which the pecan wsgi app should be created."""

    def __init__(self):
        super().__init__()
        setattr(self, 'v2.0', v2_controller.V2Controller())
        setattr(self, 'v2', v2_controller.V2Controller())

    # Run the oslo middleware healthcheck for /healthcheck
    @pecan_expose('json')
    @pecan_expose(content_type='plain/text')
    @pecan_expose(content_type='text/html')
    def healthcheck(self):  # pylint: disable=inconsistent-return-statements
        if CONF.api_settings.healthcheck_enabled:
            if pecan_request.method not in ['GET', 'HEAD']:
                pecan_abort(405)
            return self.healthcheck_obj.process_request(pecan_request)
        pecan_abort(404)

    def _add_a_version(self, versions, version, url_version, status,
                       timestamp, base_url):
        versions.append({
            'id': version,
            'status': status,
            'updated': timestamp,
            'links': [{
                'href': base_url + url_version,
                'rel': 'self'
            }]
        })

    @wsme_pecan.wsexpose(wtypes.text)
    def index(self):
        host_url = pecan_request.path_url

        if not host_url.endswith('/'):
            host_url = '{}/'.format(host_url)

        versions = []
        self._add_a_version(versions, 'v2.0', 'v2', 'SUPPORTED',
                            '2021-03-01T00:00:00Z', host_url)

        return {'versions': versions}
