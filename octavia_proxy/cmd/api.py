import sys
from wsgiref import simple_server

from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr

from octavia_proxy.common import constants

from octavia_proxy.api import app as api_app
from octavia_proxy import version


LOG = logging.getLogger(__name__)


def main():
    gmr.TextGuruMeditation.setup_autorun(version)

    app = api_app.setup_app(argv=sys.argv)

    host = cfg.CONF.api_settings.bind_host
    port = cfg.CONF.api_settings.bind_port
    LOG.info("Starting API server on %(host)s:%(port)s",
             {"host": host, "port": port})
    if (cfg.CONF.api_settings.auth_strategy not in [
            constants.KEYSTONE, constants.KEYSTONE_EXT]):
        LOG.warning('Octavia configuration [api_settings] auth_strategy is '
                    'not set to "keystone". This is not a normal '
                    'configuration and you may get "Missing project ID" '
                    'errors from API calls."')
    LOG.warning('You are running the Octavia API wsgi application using '
                'simple_server. We do not recommend this outside of simple '
                'testing. We recommend you run the Octavia API wsgi with '
                'a more full function server such as gunicorn or uWSGI.')
    srv = simple_server.make_server(host, port, app)

    srv.serve_forever()


if __name__ == '__main__':
    main()
