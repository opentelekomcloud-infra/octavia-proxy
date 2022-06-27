from octavia_lib.api.drivers import provider_base as driver_base
from oslo_config import cfg
from oslo_log import log as logging

from octavia_proxy.api.v2.types import (
    flavors as _flavors,
    health_monitor as _hm,
    l7policy as _l7policy,
    l7rule as _l7rule,
    listener as _listener,
    load_balancer,
    member as _member,
    pool as _pool,
    quotas as _quotas,
    availability_zones as _az
)
from octavia_proxy.common.utils import (
    elbv3_backmapping, loadbalancer_cascade_delete
)

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
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

    def _normalize_lb(self, res):
        return self._normalize_tags(res)

    def _normalize_tags(self, resource):
        otc_tags = resource.tags
        if otc_tags:
            tags = []
            for tag in otc_tags:
                if tag['value']:
                    tags.append('%s=%s' % (tag['key'], tag['value']))
                else:
                    tags.append('%s' % tag['key'])
            resource.tags = tags
        return resource

    def _resource_tags(self, tags):
        result = []
        for tag in tags:
            try:
                tag = tag.split('=')
                result.append({
                    'key': tag[0],
                    'value': tag[1]
                })
            except IndexError:
                result.append({'key': tag[0], 'value': ''})
        return result

    def loadbalancers(self, session, project_id, query_filter=None):
        LOG.debug('Fetching loadbalancers')

        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)

        result = []
        # OSC tries to call firstly this function even if
        # requested one resource by id, but filter by id is not
        # supported in SDK, here we check this and call another
        # function
        if 'id' in query_filter:
            lb_data = self.loadbalancer_get(
                project_id=project_id, session=session,
                lb_id=query_filter['id'])
            if lb_data:
                result.append(lb_data)
        else:
            for lb in session.vlb.load_balancers(**query_filter):
                lb = elbv3_backmapping(lb)
                lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                    self._normalize_lb(lb)
                )
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

        if 'pools' in lb_attrs:
            lb_attrs.pop('pools')
        if 'listeners' in lb_attrs:
            lb_attrs.pop('listeners')
        if 'provider' in lb_attrs:
            lb_attrs.pop('provider')
        if 'vip_subnet_id' in lb_attrs:
            lb_attrs['vip_subnet_cidr_id'] = lb_attrs['vip_subnet_id']
        if 'vip_network_id' in lb_attrs:
            lb_attrs['elb_virsubnet_ids'] = [lb_attrs.pop('vip_network_id')]
        azs = lb_attrs.pop(
            'availability_zone',
            CONF.elbv3_driver_settings.default_az
        )
        lb_attrs['availability_zone_list'] = azs.replace(' ', '').split(',')

        if 'tags' in lb_attrs:
            lb_attrs['tags'] = self._resource_tags(lb_attrs['tags'])

        # According to our decision to show only L7 flavors
        # here we assign same type of L4 flavor for load balancer instance
        if 'flavor_id' in lb_attrs:
            l7_flavor = session.vlb.get_flavor(
                lb_attrs['flavor_id'])
            lb_attrs['l7_flavor_id'] = l7_flavor.id
            lb_attrs['l4_flavor_id'] = session.vlb.find_flavor(
                name_or_id=l7_flavor.name.replace('L7', 'L4')
            ).id
            lb_attrs.pop('flavor_id')
        lb = session.vlb.create_load_balancer(**lb_attrs)
        lb = elbv3_backmapping(lb)
        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            self._normalize_lb(lb))
        lb_data.provider = PROVIDER
        LOG.debug('Created LB according to API is %s' % lb_data)
        return lb_data

    def loadbalancer_update(self, session, original_load_balancer, new_attrs):
        LOG.debug('Updating loadbalancer')

        lb = session.vlb.update_load_balancer(
            original_load_balancer.id,
            **new_attrs)
        lb = elbv3_backmapping(lb)
        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            self._normalize_lb(lb))
        lb_data.provider = PROVIDER
        return lb_data

    def loadbalancer_delete(self, session, loadbalancer, cascade=False):
        LOG.debug('Deleting loadbalancer %s' % loadbalancer.to_dict())

        if cascade:
            loadbalancer_cascade_delete(session.vlb, loadbalancer)
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
            if lsnr_data:
                result.append(lsnr_data)
        else:
            for lsnr in session.vlb.listeners(**query_filter):
                lsnr_data = _listener.ListenerResponse.from_sdk_object(
                    self._normalize_lb(lsnr)
                )
                lsnr_data.provider = PROVIDER
                result.append(lsnr_data)

        return result

    def listener_get(self, session, project_id, lsnr_id):
        LOG.debug('Searching listener')

        lsnr = session.vlb.find_listener(
            name_or_id=lsnr_id, ignore_missing=True)
        if lsnr:
            lsnr_data = _listener.ListenerResponse.from_sdk_object(
                self._normalize_lb(lsnr)
            )
            lsnr_data.provider = PROVIDER
            return lsnr_data

    def listener_create(self, session, listener):
        LOG.debug('Creating listener %s' % listener.to_dict())

        attrs = listener.to_dict()
        attrs.pop('connection_limit')
        attrs.pop('l7policies', None)

        if 'timeout_client_data' in attrs:
            attrs['client_timeout'] = attrs.pop('timeout_client_data')
        if 'timeout_member_data' in attrs:
            attrs['member_timeout'] = attrs.pop('timeout_member_data')
        if 'timeout_member_connect' in attrs:
            attrs['keepalive_timeout'] = \
                attrs.pop('timeout_member_connect')
        if 'tags' in attrs:
            attrs['tags'] = self._resource_tags(attrs['tags'])

        lsnr = session.vlb.create_listener(**attrs)

        lsnr_data = _listener.ListenerResponse.from_sdk_object(
            self._normalize_lb(lsnr)
        )

        lsnr_data.provider = PROVIDER
        LOG.debug('Created LB according to API is %s' % lsnr_data)
        return lsnr_data

    def listener_update(self, session, original_listener, new_attrs):
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

        lsnr_data = _listener.ListenerResponse.from_sdk_object(
            self._normalize_lb(lsnr))
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
            if pool_data:
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

        if 'id' in query_filter:
            member_data = self.member_get(
                project_id=project_id, session=session,
                pool_id=pool_id,
                member_id=query_filter['id']
            )
            if member_data:
                result.append(member_data)
        else:
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
        if 'subnet_id' in attrs:
            attrs['subnet_cidr_id'] = attrs.pop('subnet_id')
        else:
            lb_id = session.vlb.get_pool(pool_id)['loadbalancers'][0]['id']
            attrs['subnet_cidr_id'] = session.vlb.get_load_balancer(
                lb_id)['vip_subnet_id']

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

    def health_monitors(self, session, project_id, query_filter=None):
        LOG.debug('Fetching health monitor')

        result = []

        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)

        if 'id' in query_filter:
            hm_data = self.health_monitor_get(
                project_id=project_id, session=session,
                healthmonitor_id=query_filter['id'])
            if hm_data:
                result.append(hm_data)
        else:
            for healthmonitor in session.vlb.health_monitors(**query_filter):
                hm_data = _hm.HealthMonitorResponse.from_sdk_object(
                    healthmonitor
                )
                hm_data.provider = PROVIDER
                result.append(hm_data)
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

    def l7policies(self, session, project_id, query_filter=None):
        LOG.debug('Fetching L7 policies')

        if not query_filter:
            query_filter = {}

        result = []

        if 'id' in query_filter:
            policy_data = self.l7policy_get(
                project_id=project_id, session=session,
                l7_policy=query_filter['id']
            )
            if policy_data:
                result.append(policy_data)
        else:
            for l7_policy in session.vlb.l7_policies(**query_filter):
                l7policy_data = _l7policy.L7PolicyResponse.from_sdk_object(
                    l7_policy
                )
                l7policy_data.provider = PROVIDER
                result.append(l7policy_data)
        return result

    def l7policy_get(self, session, project_id, l7_policy):
        LOG.debug('Searching for L7 Policy')

        l7policy = session.vlb.find_l7_policy(
            name_or_id=l7_policy,
            ignore_missing=True
        )
        LOG.debug('l7policy is %s' % l7policy)

        if l7policy:
            l7policy_data = _l7policy.L7PolicyResponse.from_sdk_object(
                l7policy
            )
            l7policy_data.provider = PROVIDER
            return l7policy_data

    def l7policy_create(self, session, policy_l7):
        l7policy_attrs = policy_l7.to_dict()
        LOG.debug('Creating L7 Policy %s' % l7policy_attrs)

        l7_policy = session.vlb.create_l7_policy(**l7policy_attrs)
        l7_policy_data = _l7policy.L7PolicyResponse.from_sdk_object(l7_policy)
        l7_policy_data.provider = PROVIDER
        LOG.debug('Created L7 Policy according to API is %s' % l7_policy_data)
        return l7_policy_data

    def l7policy_update(self, session, original_l7policy, new_attrs):
        LOG.debug('Updating L7 Policy')

        l7_policy = session.vlb.update_l7_policy(
            l7_policy=original_l7policy.id,
            **new_attrs
        )

        l7_policy_data = _l7policy.L7PolicyResponse.from_sdk_object(l7_policy)
        l7_policy_data.provider = PROVIDER
        return l7_policy_data

    def l7policy_delete(self, session, l7policy, ignore_missing=True):
        LOG.debug('Deleting L7 Policy %s' % l7policy.to_dict())

        session.vlb.delete_l7_policy(
            l7_policy=l7policy.id,
            ignore_missing=ignore_missing
        )

    def l7rules(self, session, project_id, l7policy_id, query_filter=None):
        LOG.debug('Fetching l7 rules')

        result = []

        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)

        if 'id' in query_filter:
            l7rule_data = self.l7rule_get(
                project_id=project_id, session=session,
                l7policy_id=l7policy_id,
                l7rule_id=query_filter['id']
            )
            if l7rule_data:
                result.append(l7rule_data)
        else:
            for l7rule in session.vlb.l7_rules(l7policy_id, **query_filter):
                l7rule_data = _l7rule.L7RuleResponse.from_sdk_object(l7rule)
                l7rule_data.provider = PROVIDER
                result.append(l7rule_data)

        return result

    def l7rule_get(self, session, project_id, l7policy_id, l7rule_id):
        LOG.debug('Searching l7 rule')

        l7rule = session.vlb.find_l7_rule(
            name_or_id=l7rule_id, l7_policy=l7policy_id, ignore_missing=True)
        if l7rule:
            l7rule_data = _l7rule.L7RuleResponse.from_sdk_object(l7rule)
            l7rule_data.provider = PROVIDER
            return l7rule_data

    def l7rule_create(self, session, l7policy_id, l7rule):
        LOG.debug('Creating l7 rule %s' % l7rule.to_dict())

        attrs = l7rule.to_dict()

        res = session.vlb.create_l7_rule(l7_policy=l7policy_id, **attrs)
        result_data = _l7rule.L7RuleResponse.from_sdk_object(res)
        setattr(result_data, 'provider', PROVIDER)
        return result_data

    def l7rule_update(self, session, l7policy_id, original, new_attrs):
        LOG.debug('Updating l7 rule')

        res = session.vlb.update_l7_rule(
            original.id,
            l7policy_id,
            **new_attrs)
        result_data = _l7rule.L7RuleResponse.from_sdk_object(
            res)
        result_data.provider = PROVIDER
        return result_data

    def l7rule_delete(self, session, l7policy_id, l7rule):
        LOG.debug('Deleting l7 rule %s' % l7rule.to_dict())

        session.vlb.delete_l7_rule(l7rule.id, l7policy_id)

    def flavors(self, session, project_id, query_filter=None):
        LOG.debug('Fetching flavors')

        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)

        # Shows only L7 flavors in output to not confuse users,
        # because `create` only support one parameter for flavor
        result = []
        if 'name' in query_filter:
            query_filter['name'] = f'L7_flavor.elb.{query_filter["name"]}'
        if 'id' in query_filter:
            fl_data = self.flavor_get(
                project_id=project_id, session=session,
                fl_id=query_filter['id']
            )
            if fl_data:
                result.append(fl_data)
        else:
            for fl in session.vlb.flavors(**query_filter):
                if not fl['name'].startswith('L4_flavor.elb'):
                    fl['name'] = fl['name'][14:]
                    fl_data = _flavors.FlavorResponse.from_sdk_object(fl)
                    fl_data.provider = PROVIDER
                    result.append(fl_data)
        return result

    def flavor_get(self, session, project_id, fl_id):
        LOG.debug('Searching flavor')

        fl = session.vlb.get_flavor(fl_id)

        # Shows only L7 flavors in output to not confuse users,
        # because `create` only support one parameter for flavor
        if fl and not fl['name'].startswith('L4_flavor.elb'):
            fl['name'] = fl['name'][14:]
            fl_data = _flavors.FlavorResponse.from_sdk_object(fl)
            fl_data.provider = PROVIDER
            return fl_data

    def availability_zones(self, session, project_id, query_filter=None):
        LOG.debug('Fetching availability zones')

        if not query_filter:
            query_filter = {}

        result = []

        for az in session.vlb.availability_zones(**query_filter):
            az.name = az.pop('code')
            # availability_zones not filtering in SDK by region
            # to not shown wrong info in eu-de
            # simply pop the az's from nl
            if session.config.region_name == 'eu-de' and 'eu-nl' in az.name:
                continue
            az.enabled = False
            if az.state == 'ACTIVE':
                az.enabled = True
            az_data = _az.AvailabilityZoneResponse.from_sdk_object(
                az
            )
            az_data.provider = PROVIDER
            result.append(az_data)
        return result

    def quotas(self, session, project_id, query_filter=None):
        LOG.debug('Fetching quotas')
        if not query_filter:
            query_filter = {}

        result = []
        quota = session.vlb.get_quotas()
        if quota:
            quota_data = _quotas.QuotaResponse.from_sdk_object(
                quota
            )
            quota_data.provider = PROVIDER
            result.append(quota_data)
        return result

    def quota_get(self, session, project_id, quota_id):
        LOG.debug('Searching for quotas')

        quota = session.vlb.get_quotas()
        LOG.debug('quotas is %s' % quota)
        if quota:
            quota_data = _quotas.QuotaResponse.from_sdk_object(
                quota
            )
            quota_data.provider = PROVIDER
            return quota_data
