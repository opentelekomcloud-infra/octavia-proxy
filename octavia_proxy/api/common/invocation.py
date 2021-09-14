from oslo_config import cfg
from oslo_log import log as logging
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.common import exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

ENABLED_PROVIDERS = CONF.api_settings.enabled_provider_drivers


def driver_invocation(context=None, function=None, params=None, is_parallel=False):
    result = []
    if is_parallel:
        pass
    for provider in ENABLED_PROVIDERS:
        driver = driver_factory.get_driver(provider)
        if function == 'loadbalancers':
            function = driver.loadbalancers
        try:
            resource = driver_utils.call_provider(
                driver.name,
                function,
                context.session,
                context.project_id,
                params)
            if resource:
                LOG.debug('Received %s from %s' % (resource, driver.name))
                result.extend(resource)
        except exceptions.ProviderNotImplementedError:
            LOG.exception('Driver %s is not supporting this')
    return result
