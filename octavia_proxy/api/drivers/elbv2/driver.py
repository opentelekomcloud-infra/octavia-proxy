# from dateutil import parser
from oslo_log import log as logging

# from octavia_lib.api.drivers import data_models
from octavia_lib.api.drivers import provider_base as driver_base

# from octavia.api.common import types
# from wsme import types as wtypes

from octavia_proxy.api.v2.types import load_balancer
from octavia_proxy.api.v2.types import listener as _listener
from octavia_proxy.api.v2.types import member as _member

LOG = logging.getLogger(__name__)


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
        lb_attrs.pop('loadbalancer_id')

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

    def members(self, session, project_id, query_filter=None):
        LOG.debug('Fetching members')

        if not query_filter:
            query_filter = {}

        results = []
        for member in session.elb.members(**query_filter):
            results.append(_member.MemberResponse.from_sdk_object(member))
        return results

    def member_get(self, session, project_id, member_id):
        LOG.debug('Searching member')

        member = session.elb.find_member(
            name_or_id=member_id, ignore_missing=True)

        if member:
            return _member.MemberResponse.from_sdk_object(member)

    def member_create(self, session, member):
        LOG.debug('Creating member %s' % member.to_dict())

        attrs = member.to_dict()
        # TODO: do this differently
        attrs.pop('l7policies')

        res = session.elb.create_member(**attrs)

        result_data = _member.MemberResponse.from_sdk_object(
            res)
        result_data.provider = 'elbv2'
        return result_data

    def member_update(self, session, original, new_attrs):
        LOG.debug('Updating member')

        res = session.elb.update_member(
            original.id,
            **new_attrs)

        result_data = _member.MemberResponse.from_sdk_object(
            res)
        result_data.provider = 'elbv2'
        return result_data

    def member_delete(self, session, member):
        LOG.debug('Deleting member %s' % member.to_dict())

        session.elb.delete_member(member.id)
