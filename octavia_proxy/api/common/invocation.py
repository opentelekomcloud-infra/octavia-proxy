import concurrent.futures

from oslo_config import cfg
from oslo_log import log as logging

from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.common import exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def driver_call(provider, context=None, function=None, *params):
    result = []
    driver = driver_factory.get_driver(provider)
    method_to_call = getattr(driver, function)
    try:
        resource = driver_utils.call_provider(
            driver.name,
            method_to_call,
            context.session,
            context.project_id,
            *params)
        if resource:
            LOG.debug(f'Received {resource} from {driver.name}')
            try:
                result.extend(resource)
            except TypeError:
                result.append(resource)
    except exceptions.ProviderNotImplementedError:
        LOG.exception('Driver is not supporting this')
    return result


def driver_invocation(context=None, function=None, is_parallel=True, *params):
    LOG.debug(f'Called function: {function}')
    LOG.debug(f'Received params: {params}')

    enabled_providers = CONF.api_settings.enabled_provider_drivers

    result = []
    if is_parallel:
        LOG.debug('Create and start threads.')
        with concurrent.futures.ThreadPoolExecutor() as executor:
            calls = {
                executor.submit(
                    driver_call, provider, context, function, *params
                ): provider for provider in enabled_providers
            }
            for future in concurrent.futures.as_completed(calls):
                result.extend(future.result())
    else:
        for provider in enabled_providers:
            result.extend(driver_call(provider, context, function, *params))
        LOG.debug(f'{function}, result: {result}')
    return result
