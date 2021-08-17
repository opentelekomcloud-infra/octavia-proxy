from octavia_lib.api.drivers import provider_base as driver_base
from oslo_log import log as logging

from octavia_proxy.api.v2.types import flavors as _flavors
from octavia_proxy.api.v2.types import listener as _listener
from octavia_proxy.api.v2.types import load_balancer
from octavia_proxy.api.v2.types import pool as _pool

LOG = logging.getLogger(__name__)


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

        for lb in session.vlb.load_balancers(**query_filter):
            lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                self._normalize_lb(lb))
            lb_data.provider = 'elbv3'
            result.append(lb_data)

        return result

    def loadbalancer_get(self, session, project_id, lb_id):
        LOG.debug('Searching loadbalancer')

        lb = session.vlb.find_load_balancer(
            name_or_id=lb_id, ignore_missing=True)
        if lb:
            lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                self._normalize_lb(lb))
            lb_data.provider = 'elbv3'
            return lb_data

    def loadbalancer_create(self, session, loadbalancer):
        LOG.debug('Creating loadbalancer %s' % loadbalancer.to_dict())

        lb_attrs = loadbalancer.to_dict()

        lb_attrs.pop('loadbalancer_id', None)
        if 'vip_subnet_id' in lb_attrs:
            lb_attrs['vip_subnet_cidr_id'] = lb_attrs['vip_subnet_id']
        if 'vip_network_id' in lb_attrs:
            lb_attrs['elb_virsubnet_ids'] = [lb_attrs.pop('vip_network_id')]
        lb_attrs['availability_zone_list'] = [
            lb_attrs.pop('availability_zone', 'eu-nl-01')
        ]

        lb = session.vlb.create_load_balancer(**lb_attrs)

        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            lb)

        lb_data.provider = 'elbv3'
        LOG.debug('Created LB according to API is %s' % lb_data)
        return lb_data

    def loadbalancer_update(self, session, original_load_balancer,
                            new_attrs):
        LOG.debug('Updating loadbalancer')

        lb = session.vlb.update_load_balancer(
            original_load_balancer.id,
            **new_attrs)

        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            lb)
        lb_data.provider = 'elbv3'
        return lb_data

    def loadbalancer_delete(self, session, loadbalancer, cascade=False):
        """Delete a load balancer

        :param cascade: here for backward compatibility,
               not used in elbv3

        :returns: ``None``
        """
        LOG.debug('Deleting loadbalancer %s' % loadbalancer.to_dict())

        session.vlb.delete_load_balancer(loadbalancer.id)

    def listeners(self, session, project_id, query_filter=None):
        LOG.debug('Fetching listeners')

        if not query_filter:
            query_filter = {}

        query_filter.pop('project_id', None)

        result = []

        for lsnr in session.vlb.listeners(**query_filter):
            lsnr_data = _listener.ListenerResponse.from_sdk_object(lsnr)
            lsnr_data.provider = 'elbv3'
            result.append(lsnr_data)

        return result

    def listener_get(self, session, project_id, lsnr_id):
        LOG.debug('Searching listener')

        lsnr = session.vlb.find_listener(
            name_or_id=lsnr_id, ignore_missing=True)
        if lsnr:
            lsnr_data = _listener.ListenerResponse.from_sdk_object(lsnr)
            lsnr_data.provider = 'elbv3'
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

        lsnr_data.provider = 'elbv3'
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
        lsnr_data.provider = 'elbv3'
        return lsnr_data

    def listener_delete(self, session, listener):
        LOG.debug('Deleting listener %s' % listener.to_dict())

        session.vlb.delete_listener(listener.id)

    def pools(self, session, project_id, query_filter=None):
        LOG.debug('Fetching pools')

        if not query_filter:
            query_filter = {}

        query_filter.pop('project_id', None)

        result = []

        for pool in session.vlb.pools(**query_filter):
            pool_data = _pool.PoolResponse.from_sdk_object(pool)
            pool_data.provider = 'elbv3'
            result.append(pool_data)

        return result

    def pool_get(self, session, project_id, pool_id):
        LOG.debug('Searching pool')

        pool = session.vlb.find_pool(
            name_or_id=pool_id, ignore_missing=True)
        if pool:
            pool_data = _pool.PoolResponse.from_sdk_object(pool)
            pool_data.provider = 'elbv3'
            return pool_data

    def pool_create(self, session, pool):
        LOG.debug('Creating pool %s' % pool.to_dict())

        attrs = pool.to_dict()

        res = session.elb.create_pool(**attrs)
        result_data = _pool.PoolResponse.from_sdk_object(
            res)
        setattr(result_data, 'provider', 'elbv2')
        return result_data

    def pool_update(self, session, original, new_attrs):
        LOG.debug('Updating pool')

        res = session.elb.update_pool(
            original.id,
            **new_attrs)
        result_data = _pool.PoolResponse.from_sdk_object(
            res)
        result_data.provider = 'elbv2'
        return result_data

    def pool_delete(self, session, pool):
        LOG.debug('Deleting pool %s' % pool.to_dict())
        session.vlb.delete_pool(pool.id)

    def flavors(self, session, project_id, query_filter=None):
        LOG.debug('Fetching flavors')
        if not query_filter:
            query_filter = {}

        query_filter.pop('project_id', None)

        result = []

        for fl in session.vlb.flavors(**query_filter):
            fl_data = _flavors.FlavorResponse.from_sdk_object(fl)
            fl_data.provider = 'elbv3'
            result.append(fl_data)

        return result

    def flavor_get(self, session, fl_id):
        LOG.debug('Searching flavor')

        fl = session.vlb.find_flavor(
            name_or_id=fl_id, ignore_missing=True)
        if fl:
            fl_data = _flavors.FlavorResponse.from_sdk_object(fl)
            fl_data.provider = 'elbv3'
            return fl_data
