import os
import ssl
import sys

from oslo_config import cfg
from oslo_log import log as logging

import openstack

from validatetoken.middleware import validatetoken

from octavia_proxy.common import constants
from octavia_proxy.common import utils
from octavia_proxy.i18n import _

from octavia_proxy import version

LOG = logging.getLogger(__name__)

EXTRA_LOG_LEVEL_DEFAULTS = []

TLS_PROTOCOL_CHOICES = [
    p[9:].replace('_', '.') for p in ssl._PROTOCOL_NAMES.values()]

core_opts = [
    cfg.HostnameOpt('host', default=utils.get_hostname(),
                    sample_default='<server-hostname.example.com>',
                    help=_("The hostname Octavia is running on")),
    cfg.StrOpt('octavia_plugins', default='hot_plug_plugin',
               help=_("Name of the controller plugin to use")),
]

api_opts = [
    cfg.IPOpt('bind_host', default='127.0.0.1',
              help=_("The host IP to bind to")),
    cfg.PortOpt('bind_port', default=9876,
                help=_("The port to bind to")),
    cfg.StrOpt('auth_strategy', default=constants.NOAUTH,
               choices=[constants.NOAUTH,
                        constants.KEYSTONE,
                        constants.KEYSTONE_EXT,
                        constants.TESTING],
               help=_("The auth strategy for API requests.")),
    cfg.BoolOpt('allow_pagination', default=True,
                help=_("Allow the usage of pagination")),
    cfg.BoolOpt('allow_sorting', default=True,
                help=_("Allow the usage of sorting")),
    cfg.BoolOpt('allow_filtering', default=True,
                help=_("Allow the usage of filtering")),
    cfg.BoolOpt('allow_field_selection', default=True,
                help=_("Allow the usage of field selection")),
    cfg.StrOpt('pagination_max_limit',
               default=str(constants.DEFAULT_PAGE_SIZE),
               help=_("The maximum number of items returned in a single "
                      "response. The string 'infinite' or a negative "
                      "integer value means 'no limit'")),
    cfg.StrOpt('api_base_uri',
               help=_("Base URI for the API for use in pagination links. "
                      "This will be autodetected from the request if not "
                      "overridden here.")),
    cfg.BoolOpt('allow_tls_terminated_listeners', default=True,
                help=_("Allow users to create TLS Terminated listeners?")),
    cfg.BoolOpt('allow_ping_health_monitors', default=True,
                help=_("Allow users to create PING type Health Monitors?")),
    cfg.DictOpt('enabled_provider_drivers',
                help=_('A comma separated list of dictionaries of the '
                       'enabled provider driver names and descriptions. '
                       'Must match the driver name in the '
                       'octavia.api.drivers entrypoint. Example: '
                       'amphora:The Octavia Amphora driver.,'
                       'octavia:Deprecated alias of the Octavia '
                       'Amphora driver.'),
                default={'elbv2': 'The ELBv2 driver.',
                         'elbv3': 'The ELBv3 driver.'}),
    cfg.StrOpt('default_provider_driver', default='elbv2',
               help=_('Default provider driver.')),
    cfg.StrOpt('region', default='eu-de',
               help=_('Service region (used to select driver endpoint).')),
]

elb_driver_opts = [
    cfg.StrOpt('endpoint_override',
               help=_('Endpoint override url with additional parameters. '
                      'Example: http://127.0.0.1:9876/vX.Y/%(project_id)s.'),
               default=''),
]
dlb_driver_opts = [
    cfg.StrOpt('endpoint_override',
               help=_('Endpoint override url with additional parameters. '
                      'Example: http://127.0.0.1:9876/vX.Y/%(project_id)s.'),
               default=''),
    cfg.StrOpt('default_az', default='eu-de-01',
               help=_("Default AZ for dedicated load balancer")),
]

networking_opts = [
    cfg.IntOpt('max_retries', default=15,
               help=_('The maximum attempts to retry an action with the '
                      'networking service.')),
    cfg.IntOpt('retry_interval', default=1,
               help=_('Seconds to wait before retrying an action with the '
                      'networking service.')),
    cfg.IntOpt('retry_backoff', default=1,
               help=_('The seconds to backoff retry attempts.')),
    cfg.IntOpt('retry_max', default=10,
               help=_('The maximum interval in seconds between retry '
                      'attempts.')),
    cfg.IntOpt('port_detach_timeout', default=300,
               help=_('Seconds to wait for a port to detach from an '
                      'amphora.')),
    cfg.BoolOpt('allow_vip_network_id', default=True,
                help=_('Can users supply a network_id for their VIP?')),
    cfg.BoolOpt('allow_vip_subnet_id', default=True,
                help=_('Can users supply a subnet_id for their VIP?')),
    cfg.BoolOpt('allow_vip_port_id', default=True,
                help=_('Can users supply a port_id for their VIP?')),
    cfg.ListOpt('valid_vip_networks',
                help=_('List of network_ids that are valid for VIP '
                       'creation. If this field is empty, no validation '
                       'is performed.')),
    cfg.ListOpt('reserved_ips',
                default=['169.254.169.254'],
                item_type=cfg.types.IPAddress(),
                help=_('List of IP addresses reserved from being used for '
                       'member addresses. IPv6 addresses should be in '
                       'expanded, uppercase form.')),
    cfg.BoolOpt('allow_invisible_resource_usage', default=False,
                help=_("When True, users can use network resources they "
                       "cannot normally see as VIP or member subnets. Making "
                       "this True may allow users to access resources on "
                       "subnets they do not normally have access to via "
                       "neutron RBAC policies.")),
]

core_cli_opts = []

# Register the configuration options
cfg.CONF.register_opts(core_opts)
cfg.CONF.register_opts(api_opts, group='api_settings')
cfg.CONF.register_opts(validatetoken._VALIDATETOKEN_OPTS,
                       group=validatetoken.VALIDATETOKEN_MIDDLEWARE_GROUP)
cfg.CONF.register_opts(networking_opts, group='networking')
cfg.CONF.register_opts(elb_driver_opts, group='elbv2_driver_settings')
cfg.CONF.register_opts(dlb_driver_opts, group='elbv3_driver_settings')


def register_cli_opts():
    cfg.CONF.register_cli_opts(core_cli_opts)
    logging.register_options(cfg.CONF)


def init(args, **kwargs):
    register_cli_opts()
    cfg.CONF(args=args, project='octavia_proxy',
             version='%%prog %s' % version.version_info.release_string(),
             **kwargs)
    setup_remote_debugger()


def setup_logging(conf):
    """Sets up the logging options for a log with supplied name.
    :param conf: a cfg.ConfOpts object
    """
    logging.set_defaults(default_log_levels=logging.get_default_log_levels() +
                         EXTRA_LOG_LEVEL_DEFAULTS)
    product_name = "octavia_proxy"
    logging.setup(conf, product_name)
    LOG.info("Logging enabled!")
    LOG.info("%(prog)s version %(version)s",
             {'prog': sys.argv[0],
              'version': version.version_info.release_string()})
    LOG.debug("command line: %s", " ".join(sys.argv))
    openstack.enable_logging(debug=LOG.isEnabledFor(logging.DEBUG))


def _enable_pydev(debugger_host, debugger_port):
    try:
        from pydev import pydevd  # pylint: disable=import-outside-toplevel
    except ImportError:
        import pydevd  # pylint: disable=import-outside-toplevel

    pydevd.settrace(debugger_host,
                    port=int(debugger_port),
                    stdoutToServer=True,
                    stderrToServer=True)


def _enable_ptvsd(debuggger_host, debugger_port):
    import ptvsd  # pylint: disable=import-outside-toplevel

    # Allow other computers to attach to ptvsd at this IP address and port.
    ptvsd.enable_attach(address=(debuggger_host, debugger_port),
                        redirect_output=True)

    # Pause the program until a remote debugger is attached
    ptvsd.wait_for_attach()


def setup_remote_debugger():
    """Required setup for remote debugging."""

    debugger_type = os.environ.get('DEBUGGER_TYPE', 'pydev')
    debugger_host = os.environ.get('DEBUGGER_HOST')
    debugger_port = os.environ.get('DEBUGGER_PORT')

    if not debugger_type or not debugger_host or not debugger_port:
        return

    try:
        LOG.warning("Connecting to remote debugger. Once connected, resume "
                    "the program on the debugger to continue with the "
                    "initialization of the service.")
        if debugger_type == 'pydev':
            _enable_pydev(debugger_host, debugger_port)
        elif debugger_type == 'ptvsd':
            _enable_ptvsd(debugger_host, debugger_port)
        else:
            LOG.exception('Debugger %(debugger)s is not supported',
                          debugger_type)
    except Exception:
        LOG.exception('Unable to join debugger, please make sure that the '
                      'debugger processes is listening on debug-host '
                      '\'%(debug-host)s\' debug-port \'%(debug-port)s\'.',
                      {'debug-host': debugger_host,
                       'debug-port': debugger_port})
        raise
