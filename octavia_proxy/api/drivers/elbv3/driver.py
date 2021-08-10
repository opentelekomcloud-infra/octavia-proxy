from octavia_lib.api.drivers import provider_base as driver_base
from oslo_log import log as logging

from octavia_proxy.api.v2.types import listener as _listener
from octavia_proxy.api.v2.types import load_balancer
from octavia_proxy.api.v2.types import flavors as _flavors

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

        query_filter.pop('project_id')

        results = []
        for lsnr in session.list_elbv3_listeners(**query_filter):
            results.append(_listener.ListenerResponse.from_sdk_object(lsnr))
        return results

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
