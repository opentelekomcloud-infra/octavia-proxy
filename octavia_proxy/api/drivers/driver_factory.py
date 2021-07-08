from oslo_config import cfg
from oslo_log import log as logging
from stevedore import driver as stevedore_driver

from octavia_proxy.common import exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def get_driver(provider):
    if provider not in CONF.api_settings.enabled_provider_drivers:
        LOG.warning("Requested provider driver '%s' was not enabled in the "
                    "configuration file.", provider)
        raise exceptions.ProviderNotEnabled(prov=provider)

    try:
        driver = stevedore_driver.DriverManager(
            namespace='octavia_proxy.api.drivers',
            name=provider,
            invoke_on_load=True).driver
        driver.name = provider
    except Exception as e:
        LOG.error('Unable to load provider driver %s due to: %s',
                  provider, str(e))
        raise exceptions.ProviderNotFound(prov=provider)
    return driver
