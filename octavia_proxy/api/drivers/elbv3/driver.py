from oslo_log import log as logging

from octavia_lib.api.drivers import provider_base as driver_base

from octavia_proxy.api.v2.types import load_balancer
from octavia_proxy.api.v2.types import listener as _listener


LOG = logging.getLogger(__name__)


class ELBv3Driver(driver_base.ProviderDriver):
    def __init__(self):
        super().__init__()

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

        query_filter.pop('project_id')

        result = []

        for lb in session.list_elbv3_load_balancers(**query_filter):
            lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                self._normalize_lb(lb))
            lb_data.provider = 'elbv3'
            result.append(lb_data)

        return result

    def loadbalancer_get(self, session, project_id, lb_id):
        LOG.debug('Searching loadbalancer')

        lb = session.find_elbv2_load_balancer(
            name_or_id=lb_id, ignore_missing=True)
        if lb:
            lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                self._normalize_lb(lb))
            lb_data.provider = 'elbv2'
            return lb_data

    def listeners(self, session, project_id, query_filter=None):
        LOG.debug('Fetching listeners')

        if not query_filter:
            query_filter = {}

        query_filter.pop('project_id')

        results = []
        for lsnr in session.list_elbv3_listeners(**query_filter):
            results.append(_listener.ListenerResponse.from_sdk_object(lsnr))
        return results
