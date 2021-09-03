from octavia_lib.api.drivers import provider_base as driver_base
from oslo_log import log as logging

from octavia_proxy.api.v2.types import flavors as _flavors
from octavia_proxy.api.v2.types import health_monitor as _hm
from octavia_proxy.api.v2.types import listener as _listener
from octavia_proxy.api.v2.types import load_balancer
from octavia_proxy.api.v2.types import member as _member
from octavia_proxy.api.v2.types import pool as _pool
from octavia_proxy.common.utils import elbv3_backmapping, elbv3_foremapping

LOG = logging.getLogger(__name__)
PROVIDER = 'elbv3'


class ELBv3Driver(driver_base.ProviderDriver):
    def __init__(self):
        super().__init__()

    # API functions
    def get_supported_flavor_metadata(self):
        LOG.debug('Provider %s elbv3, get_supported_flavor_metadata',
                  self.__class__.__name__)

        return {"elbv3": "Plain ELBv3 (New one)"}

    # Availability Zone
    def get_supported_availability_zone_metadata(self):
        LOG.debug(
            'Provider %s elbv3, get_supported_availability_zone_metadata',
            self.__class__.__name__)

        return {"eu-nl-01": "The compute availability zone to use for "
                            "this loadbalancer."}

    def _normalize_lb(self, lb):
        return self._normalize_tags(lb)

    def _normalize_tags(self, lb):
        tags = []
        otc_tags = lb.tags
        if otc_tags:
            tags = []
            for k, v in otc_tags:
                tags.append('%s=%s' % (k, v))
            lb.tags = tags
        return lb

    def loadbalancers(self, session, project_id, query_filter=None):
        LOG.debug('Fetching loadbalancers')

        if not query_filter:
            query_filter = {}

        query_filter.pop('project_id', None)

        result = []

        if 'id' in query_filter:
            lb_data = self.loadbalancer_get(
                project_id=project_id, session=session,
                lb_id=query_filter['id'])
            result.append(lb_data)
        else:
            for lb in session.vlb.load_balancers(**query_filter):
                lb = elbv3_backmapping(lb)
                lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                    self._normalize_lb(lb))
                lb_data.provider = PROVIDER
                result.append(lb_data)

        return result

    def loadbalancer_get(self, session, project_id, lb_id):
        LOG.debug('Searching loadbalancer')

        lb = session.vlb.find_load_balancer(
            name_or_id=lb_id, ignore_missing=True)
        if lb:
            lb = elbv3_backmapping(lb)
            lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                self._normalize_lb(lb))
            lb_data.provider = PROVIDER
            return lb_data

    def loadbalancer_create(self, session, loadbalancer):
        LOG.debug('Creating loadbalancer %s' % loadbalancer.to_dict())

        lb_attrs = loadbalancer.to_dict()

        lb_attrs.pop('loadbalancer_id', None)
        lb_attrs = elbv3_foremapping(lb_attrs)

        lb = session.vlb.create_load_balancer(**lb_attrs)
        lb = elbv3_backmapping(lb)
        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            lb)

        lb_data.provider = PROVIDER
        LOG.debug('Created LB according to API is %s' % lb_data)
        return lb_data

    def loadbalancer_update(self, session, original_load_balancer,
                            new_attrs):
        LOG.debug('Updating loadbalancer')

        lb = session.vlb.update_load_balancer(
            original_load_balancer.id,
            **new_attrs)
        lb = elbv3_backmapping(lb)
        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            lb)
        lb_data.provider = PROVIDER
        return lb_data

    def loadbalancer_cascade_delete(self, session, loadbalancer):
        listeners = []
        pools = []
        members = []
        healthmonitors = []
        l7policies = []
        l7rules = []
        lb = session.vlb.find_load_balancer(
            name_or_id=loadbalancer.id, ignore_missing=True)
        if lb:
            if lb.listeners:
                listeners = [ls['id'] for ls in lb.listeners]
            # for ls in listeners:
            #     l = session.vlb.find_listener(
            #         name_or_id=ls, ignore_missing=True)
            #     if l:
            #         l7policies.append(l.l7policies)
            if lb.pools:
                pools = [pl['id'] for pl in lb.pools]
            for pool in pools:
                pl = session.vlb.find_pool(
                    name_or_id=pool, ignore_missing=True)
                if pl and pl.healthmonitor_id:
                    healthmonitors.append(pl.healthmonitor_id)
                if pl and pl.members:
                    members.append([mem['id'] for mem in pl.members])


    def loadbalancer_delete(self, session, loadbalancer, cascade=False):
        """Delete a load balancer

        :param cascade: here for backward compatibility,
               not used in elbv3

        :returns: ``None``
        """
        LOG.debug('Deleting loadbalancer %s' % loadbalancer.to_dict())
        if cascade:
            self.loadbalancer_cascade_delete(session, loadbalancer)
        else:
            session.vlb.delete_load_balancer(loadbalancer.id)

    def listeners(self, session, project_id, query_filter=None):
        LOG.debug('Fetching listeners')
        result = []

        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)

        if 'id' in query_filter:
            lsnr_data = self.listener_get(
                project_id=project_id, session=session,
                lsnr_id=query_filter['id'])
            result.append(lsnr_data)
        else:
            for lsnr in session.vlb.listeners(**query_filter):
                lsnr_data = _listener.ListenerResponse.from_sdk_object(lsnr)
                lsnr_data.provider = PROVIDER
                result.append(lsnr_data)

        return result

    def listener_get(self, session, project_id, lsnr_id):
        LOG.debug('Searching listener')

        lsnr = session.vlb.find_listener(
            name_or_id=lsnr_id, ignore_missing=True)
        if lsnr:
            lsnr_data = _listener.ListenerResponse.from_sdk_object(lsnr)
            lsnr_data.provider = PROVIDER
            return lsnr_data

    def listener_create(self, session, listener):
        LOG.debug('Creating listener %s' % listener.to_dict())

        lattrs = listener.to_dict()
        lattrs.pop('connection_limit')
        lattrs.pop('l7policies', None)

        if 'timeout_client_data' in lattrs:
            lattrs['client_timeout'] = lattrs.pop('timeout_client_data')
        if 'timeout_member_data' in lattrs:
            lattrs['member_timeout'] = lattrs.pop('timeout_member_data')
        if 'timeout_member_connect' in lattrs:
            lattrs['keepalive_timeout'] = \
                lattrs.pop('timeout_member_connect')

        lsnr = session.vlb.create_listener(**lattrs)

        lsnr_data = _listener.ListenerResponse.from_sdk_object(
            lsnr)

        lsnr_data.provider = PROVIDER
        LOG.debug('Created LB according to API is %s' % lsnr_data)
        return lsnr_data

    def listener_update(self, session, original_listener,
                        new_attrs):
        LOG.debug('Updating listener')

        if 'timeout_client_data' in new_attrs:
            new_attrs['client_timeout'] = new_attrs.pop('timeout_client_data')
        if 'timeout_member_data' in new_attrs:
            new_attrs['member_timeout'] = new_attrs.pop('timeout_member_data')
        if 'timeout_member_connect' in new_attrs:
            new_attrs['keepalive_timeout'] = \
                new_attrs.pop('timeout_member_connect')

        lsnr = session.vlb.update_listener(
            original_listener.id,
            **new_attrs)

        lsnr_data = _listener.ListenerResponse.from_sdk_object(lsnr)
        lsnr_data.provider = PROVIDER
        return lsnr_data

    def listener_delete(self, session, listener):
        LOG.debug('Deleting listener %s' % listener.to_dict())

        session.vlb.delete_listener(listener.id)

    def pools(self, session, project_id, query_filter=None):
        LOG.debug('Fetching pools')
        result = []

        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)

        if 'id' in query_filter:
            pool_data = self.pool_get(
                project_id=project_id, session=session,
                pool_id=query_filter['id'])
            result.append(pool_data)
        else:
            for pool in session.vlb.pools(**query_filter):
                pool_data = _pool.PoolResponse.from_sdk_object(pool)
                pool_data.provider = PROVIDER
                result.append(pool_data)

        return result

    def pool_get(self, session, project_id, pool_id):
        LOG.debug('Searching pool')

        pool = session.vlb.find_pool(
            name_or_id=pool_id, ignore_missing=True)
        if pool:
            pool_data = _pool.PoolResponse.from_sdk_object(pool)
            pool_data.provider = PROVIDER
            return pool_data

    def pool_create(self, session, pool):
        LOG.debug('Creating pool %s' % pool.to_dict())
        attrs = pool.to_dict()

        res = session.vlb.create_pool(**attrs)
        result_data = _pool.PoolResponse.from_sdk_object(
            res)
        setattr(result_data, 'provider', PROVIDER)
        return result_data

    def pool_update(self, session, original, new_attrs):
        LOG.debug('Updating pool')

        res = session.vlb.update_pool(
            original.id,
            **new_attrs)
        result_data = _pool.PoolResponse.from_sdk_object(
            res)
        result_data.provider = PROVIDER
        return result_data

    def pool_delete(self, session, pool):
        LOG.debug('Deleting pool %s' % pool.to_dict())
        session.vlb.delete_pool(pool.id)

    def members(self, session, project_id, pool_id, query_filter=None):
        LOG.debug('Fetching pools')
        result = []
        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)

        for member in session.vlb.members(pool_id, **query_filter):
            member_data = _member.MemberResponse.from_sdk_object(member)
            member_data.provider = PROVIDER
            result.append(member_data)

        return result

    def member_get(self, session, project_id, pool_id, member_id):
        LOG.debug('Searching pool')

        member = session.vlb.find_member(
            name_or_id=member_id, pool=pool_id, ignore_missing=True)
        if member:
            member_data = _member.MemberResponse.from_sdk_object(member)
            member_data.provider = PROVIDER
            return member_data

    def member_create(self, session, pool_id, member):
        LOG.debug('Creating member %s' % member.to_dict())
        attrs = member.to_dict()

        attrs['address'] = attrs.pop('ip_address', None)
        attrs['subnet_cidr_id'] = attrs.pop('subnet_id', None)

        res = session.vlb.create_member(pool_id, **attrs)
        result_data = _member.MemberResponse.from_sdk_object(res)
        setattr(result_data, 'provider', PROVIDER)
        return result_data

    def member_update(self, session, pool_id, original, new_attrs):
        LOG.debug('Updating member')

        res = session.vlb.update_member(
            original.id,
            pool_id,
            **new_attrs)
        result_data = _member.MemberResponse.from_sdk_object(
            res)
        result_data.provider = PROVIDER
        return result_data

    def member_delete(self, session, pool_id, member):
        LOG.debug('Deleting member %s' % member.to_dict())
        session.vlb.delete_member(member.id, pool_id)

    def health_monitors(
            self, session, project_id,
            query_filter=None):
        LOG.debug('Fetching health monitor')
        result = []
        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)
        for healthmonitor in session.vlb.health_monitors(**query_filter):
            healthmonitor_data = _hm.HealthMonitorResponse.from_sdk_object(
                healthmonitor
            )
            healthmonitor_data.provider = PROVIDER
            result.append(healthmonitor_data)

        return result

    def health_monitor_get(self, session, project_id, healthmonitor_id):
        LOG.debug('Searching health monitor')
        healthmonitor = session.vlb.find_health_monitor(
            name_or_id=healthmonitor_id, ignore_missing=True)
        if healthmonitor:
            healthmonitor_data = _hm.HealthMonitorResponse.from_sdk_object(
                healthmonitor
            )
            healthmonitor_data.provider = PROVIDER
            return healthmonitor_data

    def health_monitor_create(self, session, healthmonitor):
        LOG.debug('Creating health monitor %s' % healthmonitor.to_dict())
        attrs = healthmonitor.to_dict()
        if 'UDP-CONNECT' in attrs['type']:
            attrs['type'] = 'UDP_CONNECT'
        res = session.vlb.create_health_monitor(**attrs)
        result_data = _hm.HealthMonitorResponse.from_sdk_object(
            res)

        setattr(result_data, 'provider', PROVIDER)
        return result_data

    def health_monitor_update(self, session, original, new_attrs):
        LOG.debug('Updating health monitor')
        res = session.vlb.update_health_monitor(
            original.id,
            **new_attrs)
        result_data = _hm.HealthMonitorResponse.from_sdk_object(
            res)
        result_data.provider = PROVIDER
        return result_data

    def health_monitor_delete(self, session, healthmonitor):
        LOG.debug('Deleting health monitor %s' % healthmonitor.to_dict())
        session.vlb.delete_health_monitor(healthmonitor.id)

    def flavors(self, session, project_id, query_filter=None):
        LOG.debug('Fetching flavors')
        if not query_filter:
            query_filter = {}

        query_filter.pop('project_id', None)

        result = []

        for fl in session.vlb.flavors(**query_filter):
            fl_data = _flavors.FlavorResponse.from_sdk_object(fl)
            fl_data.provider = PROVIDER
            result.append(fl_data)

        return result

    def flavor_get(self, session, fl_id):
        LOG.debug('Searching flavor')

        fl = session.vlb.find_flavor(
            name_or_id=fl_id, ignore_missing=True)
        if fl:
            fl_data = _flavors.FlavorResponse.from_sdk_object(fl)
            fl_data.provider = PROVIDER
            return fl_data
