import sys

from oslo_config import cfg
from oslo_log import log as logging
from oslo_middleware import cors
from oslo_middleware import http_proxy_to_wsgi
from oslo_middleware import request_id
from pecan import configuration as pecan_configuration
from pecan import make_app as pecan_make_app

# TODO(gtema) this should actually become configurable whether we want
# validatetoken or keystonemiddleware
import validatetoken.middleware.validatetoken as validatetoken_middleware

from octavia_proxy.api import config as app_config
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.common import service as octavia_service
from octavia_proxy.common import constants


LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def get_pecan_config():
    """Returns the pecan config."""
    filename = app_config.__file__.replace('.pyc', '.py')
    return pecan_configuration.conf_from_file(filename)


def _init_drivers():
    """Initialize provider drivers."""
    for provider in CONF.api_settings.enabled_provider_drivers:
        driver_factory.get_driver(provider)


def setup_app(pecan_config=None, debug=False, argv=None):
    """Creates and returns a pecan wsgi app."""
    if argv is None:
        argv = sys.argv
    octavia_service.prepare_service(argv)
    cfg.CONF.log_opt_values(LOG, logging.DEBUG)

    _init_drivers()

    if not pecan_config:
        pecan_config = get_pecan_config()
    pecan_configuration.set_config(dict(pecan_config), overwrite=True)

    return pecan_make_app(
        pecan_config.app.root,
        wrap_app=_wrap_app,
        debug=debug,
        hooks=pecan_config.app.hooks,
        wsme=pecan_config.wsme
    )


def _wrap_app(app):
    """Wraps wsgi app with additional middlewares."""
    app = request_id.RequestId(app)

    if cfg.CONF.api_settings.auth_strategy == constants.KEYSTONE_EXT:
        app = validatetoken_middleware.ValidateToken(
            app, cfg.CONF)

    app = http_proxy_to_wsgi.HTTPProxyToWSGI(app)

    # This should be the last middleware in the list (which results in
    # it being the first in the middleware chain). This is to ensure
    # that any errors thrown by other middleware, such as an auth
    # middleware - are annotated with CORS headers, and thus accessible
    # by the browser.
    app = cors.CORS(app, cfg.CONF)
    cors.set_defaults(
        allow_headers=['X-Auth-Token', 'X-Openstack-Request-Id'],
        allow_methods=['GET', 'PUT', 'POST', 'DELETE'],
        expose_headers=['X-Auth-Token', 'X-Openstack-Request-Id']
    )

    return app
