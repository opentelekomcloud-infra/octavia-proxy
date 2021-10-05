import threading

from oslo_config import cfg
from oslo_log import log as logging

from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.common import exceptions

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

ENABLED_PROVIDERS = CONF.api_settings.enabled_provider_drivers


class DriverThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, Verbose=None):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        if kwargs is None:
            kwargs = {}
        self._return = None

    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        threading.Thread.join(self, *args)
        return self._return


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
    result = []
    LOG.debug(f'Called function: {function}')
    LOG.debug(f'Received params: {params}')
    threads = []
    for provider in ENABLED_PROVIDERS:
        if is_parallel:
            LOG.debug(f'Create and start thread {provider}.')
            dt = DriverThread(
                target=driver_call,
                args=(provider, context, function, *params)
            )
            threads.append(dt)
            dt.start()
        else:
            result.extend(driver_call(provider, context, function, *params))
        LOG.debug(f'{function}, result: {result}')
    for index, thread in enumerate(threads):
        result.extend(thread.join())
        LOG.debug(f'Thread {index} done')
    return result
