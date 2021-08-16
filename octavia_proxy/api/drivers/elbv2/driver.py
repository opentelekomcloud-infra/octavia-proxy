# from dateutil import parser
# from octavia_lib.api.drivers import data_models
from octavia_lib.api.drivers import provider_base as driver_base
from oslo_log import log as logging
from wsme import types as wtypes

from octavia_proxy.api.v2.types import (
    health_monitor as _monitor, listener as _listener, load_balancer
)

LOG = logging.getLogger(__name__)

ELBv2 = 'elbv2'


class ELBv2Driver(driver_base.ProviderDriver):
    def __init__(self):
        super().__init__()

    def get_supported_flavor_metadata(self):
        LOG.debug('Provider %s elbv2, get_supported_flavor_metadata',
                  self.__class__.__name__)

        return {"elbv2": "Plain ELBv2 (Neutron-like)"}

    # Availability Zone
    def get_supported_availability_zone_metadata(self):
        LOG.debug(
            'Provider %s elbv2, get_supported_availability_zone_metadata',
            self.__class__.__name__)

        return {"compute_zone": "The compute availability zone to use for "
                                "this loadbalancer."}

    def loadbalancers(self, session, project_id, query_filter=None):
        LOG.debug('Fetching loadbalancers')

        if not query_filter:
            query_filter = {}

        results = []
        for lb in session.elb.load_balancers(**query_filter):
            lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                lb)
            lb_data.provider = 'elbv2'
            results.append(lb_data)
        return results

    def loadbalancer_get(self, session, project_id, lb_id):
        LOG.debug('Searching loadbalancer')

        lb = session.elb.find_load_balancer(
            name_or_id=lb_id, ignore_missing=True)
        LOG.debug('lb is %s' % lb)

        if lb:
            lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(lb)
            lb_data.provider = 'elbv2'
            return lb_data

    def loadbalancer_create(self, session, loadbalancer):
        LOG.debug('Creating loadbalancer %s' % loadbalancer.to_dict())

        lb_attrs = loadbalancer.to_dict()
        lb_attrs.pop('loadbalancer_id', None)

        lb = session.elb.create_load_balancer(**lb_attrs)

        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            lb)
        lb_data.provider = 'elbv2'
        LOG.debug('Created LB according to API is %s' % lb_data)
        return lb_data

    def loadbalancer_update(self, session, original_load_balancer,
                            new_attrs):
        LOG.debug('Updating loadbalancer')

        lb = session.elb.update_load_balancer(
            original_load_balancer.id,
            **new_attrs)

        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            lb)
        lb_data.provider = 'elbv2'
        return lb_data

    def loadbalancer_delete(self, session, loadbalancer, cascade=False):
        LOG.debug('Deleting loadbalancer %s' % loadbalancer.to_dict())

        session.elb.delete_load_balancer(loadbalancer.id, cascade=cascade)

    def listeners(self, session, project_id, query_filter=None):
        LOG.debug('Fetching listeners')

        if not query_filter:
            query_filter = {}

        results = []
        for lsnr in session.elb.listeners(**query_filter):
            results.append(_listener.ListenerResponse.from_sdk_object(lsnr))
        return results

    def listener_get(self, session, project_id, listener_id):
        LOG.debug('Searching loadbalancer')

        lsnr = session.elb.find_listener(
            name_or_id=listener_id, ignore_missing=True)

        if lsnr:
            return _listener.ListenerResponse.from_sdk_object(lsnr)

    def listener_create(self, session, listener):
        LOG.debug('Creating listener %s' % listener.to_dict())

        attrs = listener.to_dict()
        # TODO: do this differently
        attrs.pop('l7policies')

        res = session.elb.create_listener(**attrs)

        result_data = _listener.ListenerResponse.from_sdk_object(
            res)
        result_data.provider = 'elbv2'
        return result_data

    def listener_update(self, session, original, new_attrs):
        LOG.debug('Updating listener')

        res = session.elb.update_listener(
            original.id,
            **new_attrs)

        result_data = _listener.ListenerResponse.from_sdk_object(
            res)
        result_data.provider = 'elbv2'
        return result_data

    def listener_delete(self, session, listener):
        LOG.debug('Deleting listener %s' % listener.to_dict())

        session.elb.delete_listener(listener.id)

    def health_monitors(self, session, query_filter=None):
        LOG.debug('Fetching health monitors')

        query_filter = query_filter or {}

        results = []
        raw_results = session.elb.health_monitors(**query_filter)
        for lb in raw_results:
            result_data = _monitor.HealthMonitorResponse.from_sdk_object(lb)
            result_data.provider = ELBv2
            results.append(result_data)
        return results

    _hm_type = wtypes.Enum(str, 'TCP', 'UDP_CONNECT', 'HTTP')

    def health_monitor_create(self, session, healthmonitor):
        # validate values for ELBv2
        wtypes.validate_value(self._hm_type, healthmonitor['type'])
        return session.elb.create_health_monitor(**healthmonitor)

    def health_monitor_update(self, session, old_healthmonitor,
                              new_healthmonitor):
        # validate values for ELBv2
        # type is optional in the update
        wtypes.validate_value(self._hm_type, new_healthmonitor.pop('type', None))
        LOG.debug('Updating  monitor')

        res = session.elb.update_health_monitor(
            old_healthmonitor.id, **new_healthmonitor)
        result_data = _monitor.HealthMonitorResponse.from_sdk_object(res)
        result_data.provider = ELBv2
        return result_data

    def health_monitor_delete(self, session, healthmonitor):
        return session.elb.delete_health_monitor(healthmonitor)

    def health_monitor_get(self, session, name_or_id):
        hm = session.elb.find_health_monitor(name_or_id=name_or_id, ignore_missing=True)
        if hm:
            hm_data = _monitor.HealthMonitorResponse.from_sdk_object(hm)
            hm_data.provider = ELBv2
            return hm_data
