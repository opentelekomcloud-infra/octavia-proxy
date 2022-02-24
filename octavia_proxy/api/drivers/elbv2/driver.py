from octavia_lib.api.drivers import provider_base as driver_base
from oslo_log import log as logging

from octavia_proxy.api.v2.types import (
    health_monitor as _hm, listener as _listener, load_balancer,
    pool as _pool, member as _member, l7policy as _l7policy,
    l7rule as _l7rule, quotas as _quotas,
    availability_zones as _az
)

LOG = logging.getLogger(__name__)

PROVIDER = 'elbv2'


class ELBv2Driver(driver_base.ProviderDriver):
    def __init__(self):
        super().__init__()

    def _normalize_lb(self, res):
        return self._normalize_tags(res)

    def _normalize_tags(self, resource):
        otc_tags = resource.tags
        if otc_tags:
            tags = []
            for tag in otc_tags:
                tl = tag.split('=')
                try:
                    if tl[1]:
                        tags.append(tag)
                    else:
                        tags.append(tl[0])
                except IndexError:
                    tags.append(tl[0])
            resource.tags = tags
        return resource

    def _normalize_tag(self, tag):
        return "=".join(str(val) for val in tag.values())

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
            for lb in session.elb.load_balancers(**query_filter):
                lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                    self._normalize_lb(lb))
                lb_data.provider = PROVIDER
                result.append(lb_data)
        return result

    def loadbalancer_get(self, session, project_id, lb_id):
        LOG.debug('Searching for loadbalancer')

        lb = session.elb.find_load_balancer(
            name_or_id=lb_id, ignore_missing=True)
        LOG.debug('lb is %s' % lb)

        if lb:
            lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
                self._normalize_lb(lb))
            lb_data.provider = PROVIDER
            return lb_data

    def loadbalancer_create(self, session, loadbalancer):
        LOG.debug('Creating loadbalancer %s' % loadbalancer.to_dict())

        lb_attrs = loadbalancer.to_dict()
        if 'pools' in lb_attrs:
            lb_attrs.pop('pools')
        if 'listeners' in lb_attrs:
            lb_attrs.pop('listeners')
        lb_attrs.pop('loadbalancer_id', None)
        lb_attrs.pop('vip_network_id', None)

        tags = []
        if 'tags' in lb_attrs:
            tags = self._resource_tags(lb_attrs.pop('tags'))
        lb = session.elb.create_load_balancer(**lb_attrs)

        for tag in tags:
            LOG.debug('Create tag %s for load balancer %s' % (tag, lb.id))
            try:
                session.elb.create_load_balancer_tag(lb.id, **tag)
                lb.tags.append(self._normalize_tag(tag))
            except Exception as ex:
                LOG.exception('Tag cannot be created: %s' % ex)

        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            self._normalize_lb(lb))
        lb_data.provider = PROVIDER
        LOG.debug('Created LB according to API is %s' % lb_data)
        return lb_data

    def loadbalancer_update(self, session, original_load_balancer, new_attrs):
        LOG.debug('Updating loadbalancer')

        lb = session.elb.update_load_balancer(
            original_load_balancer.id,
            **new_attrs)

        lb_data = load_balancer.LoadBalancerResponse.from_sdk_object(
            lb)
        lb_data.provider = PROVIDER
        return lb_data

    def loadbalancer_delete(self, session, loadbalancer, cascade=False):
        LOG.debug('Deleting loadbalancer %s' % loadbalancer.to_dict())

        session.elb.delete_load_balancer(loadbalancer.id, cascade=cascade)

    def listeners(self, session, project_id, query_filter=None):
        LOG.debug('Fetching listeners')

        if not query_filter:
            query_filter = {}

        result = []
        if 'id' in query_filter:
            lsnr_data = self.listener_get(
                project_id=project_id, session=session,
                listener_id=query_filter['id'])
            if lsnr_data:
                result.append(lsnr_data)
        else:
            for lsnr in session.elb.listeners(**query_filter):
                lsnr_data = _listener.ListenerResponse.from_sdk_object(
                    self._normalize_lb(lsnr))
                lsnr_data.provider = PROVIDER
                result.append(lsnr_data)
        return result

    def listener_get(self, session, project_id, listener_id):
        LOG.debug('Searching loadbalancer')

        lsnr = session.elb.find_listener(
            name_or_id=listener_id, ignore_missing=True)

        if lsnr:
            lsnr_data = _listener.ListenerResponse.from_sdk_object(
                self._normalize_lb(lsnr))
            lsnr_data.provider = PROVIDER
            return lsnr_data

    def listener_create(self, session, listener):
        LOG.debug('Creating listener %s' % listener.to_dict())

        attrs = listener.to_dict()
        attrs.pop('l7policies', None)

        tags = []
        if 'tags' in attrs:
            tags = self._resource_tags(attrs.pop('tags'))

        ls = session.elb.create_listener(**attrs)

        for tag in tags:
            LOG.debug('Create tag %s for listener %s' % (tag, ls.id))
            try:
                session.elb.create_listener_tag(ls.id, **tag)
                ls.tags.append(self._normalize_tag(tag))
            except Exception as ex:
                LOG.exception('Tag cannot be created: %s' % ex)

        result_data = _listener.ListenerResponse.from_sdk_object(
            self._normalize_lb(ls))
        result_data.provider = PROVIDER
        return result_data

    def listener_update(self, session, original, new_attrs):
        LOG.debug('Updating listener')

        res = session.elb.update_listener(
            original.id,
            **new_attrs)

        result_data = _listener.ListenerResponse.from_sdk_object(
            res)
        result_data.provider = PROVIDER
        return result_data

    def listener_delete(self, session, listener):
        LOG.debug('Deleting listener %s' % listener.to_dict())

        session.elb.delete_listener(listener.id)

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
            for healthmonitor in session.elb.health_monitors(**query_filter):
                hm_data = _hm.HealthMonitorResponse.from_sdk_object(
                    healthmonitor
                )
                hm_data.provider = PROVIDER
                result.append(hm_data)

        return result

    def health_monitor_get(self, session, project_id, healthmonitor_id):
        LOG.debug('Searching health monitor')

        healthmonitor = session.elb.find_health_monitor(
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

        res = session.elb.create_health_monitor(**attrs)
        result_data = _hm.HealthMonitorResponse.from_sdk_object(
            res)
        setattr(result_data, 'provider', PROVIDER)
        return result_data

    def health_monitor_update(self, session, original, new_attrs):
        LOG.debug('Updating health monitor')

        res = session.elb.update_health_monitor(
            original.id,
            **new_attrs)
        result_data = _hm.HealthMonitorResponse.from_sdk_object(
            res)
        result_data.provider = PROVIDER
        return result_data

    def health_monitor_delete(self, session, healthmonitor):
        LOG.debug('Deleting health monitor %s' % healthmonitor.to_dict())

        session.elb.delete_health_monitor(healthmonitor.id)

    def pools(self, session, project_id, query_filter=None):
        LOG.debug('Fetching pools')

        if not query_filter:
            query_filter = {}

        result = []

        if 'id' in query_filter:
            pool_data = self.pool_get(
                project_id=project_id, session=session,
                pool_id=query_filter['id'])
            if pool_data:
                result.append(pool_data)
        else:
            for pl in session.elb.pools(**query_filter):
                pool_data = _pool.PoolResponse.from_sdk_object(pl)
                pool_data.provider = PROVIDER
                result.append(pool_data)
        return result

    def pool_get(self, session, project_id, pool_id):
        LOG.debug('Searching pool')

        pool = session.elb.find_pool(
            name_or_id=pool_id, ignore_missing=True)
        if pool:
            pool_data = _pool.PoolResponse.from_sdk_object(pool)
            pool_data.provider = PROVIDER
            return pool_data

    def pool_create(self, session, pool):
        LOG.debug('Creating pool %s' % pool.to_dict())

        attrs = pool.to_dict()
        if 'tls_enabled' in attrs:
            attrs.pop('tls_enabled')

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
        result_data.provider = PROVIDER
        return result_data

    def pool_delete(self, session, pool):
        LOG.debug('Deleting pool %s' % pool.to_dict())

        session.elb.delete_pool(pool.id)

    def members(self, session, project_id, pool_id, query_filter=None):
        LOG.debug('Fetching pools')

        if not query_filter:
            query_filter = {}
        query_filter.pop('project_id', None)

        result = []

        if 'id' in query_filter:
            member_data = self.member_get(
                project_id=project_id, session=session,
                pool_id=pool_id,
                member_id=query_filter['id']
            )
            if member_data:
                result.append(member_data)
        else:
            for member in session.elb.members(pool_id, **query_filter):
                member_data = _member.MemberResponse.from_sdk_object(member)
                member_data.provider = PROVIDER
                result.append(member_data)

        return result

    def member_get(self, session, project_id, pool_id, member_id):
        LOG.debug('Searching pool')

        member = session.elb.find_member(
            name_or_id=member_id, pool=pool_id, ignore_missing=True)
        if member:
            member_data = _member.MemberResponse.from_sdk_object(member)
            member_data.provider = PROVIDER
            return member_data

    def member_create(self, session, pool_id, member):
        LOG.debug('Creating member %s' % member.to_dict())

        attrs = member.to_dict()
        if 'subnet_id' not in attrs:
            lb_id = session.elb.get_pool(pool_id)['loadbalancers'][0]['id']
            attrs['subnet_id'] = session.elb.get_load_balancer(
                lb_id)['vip_subnet_id']

        attrs['address'] = attrs.pop('ip_address', None)
        attrs.pop('backup', None)
        attrs.pop('monitor_port', None)
        attrs.pop('monitor_address', None)

        res = session.elb.create_member(pool_id, **attrs)
        result_data = _member.MemberResponse.from_sdk_object(res)
        setattr(result_data, 'provider', PROVIDER)
        return result_data

    def member_update(self, session, pool_id, original, new_attrs):
        LOG.debug('Updating member')

        res = session.elb.update_member(
            original.id,
            pool_id,
            **new_attrs)
        result_data = _member.MemberResponse.from_sdk_object(
            res)
        result_data.provider = PROVIDER
        return result_data

    def member_delete(self, session, pool_id, member):
        LOG.debug('Deleting pool %s' % member.to_dict())

        session.elb.delete_member(member.id, pool_id)

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
            for l7_policy in session.elb.l7_policies(**query_filter):
                l7policy_data = _l7policy.L7PolicyResponse.from_sdk_object(
                    l7_policy
                )
                l7policy_data.provider = PROVIDER
                result.append(l7policy_data)
        return result

    def l7policy_get(self, session, project_id, l7_policy):
        LOG.debug('Searching for L7 Policy')

        l7policy = session.elb.find_l7_policy(
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

        l7_policy = session.elb.create_l7_policy(**l7policy_attrs)
        l7_policy_data = _l7policy.L7PolicyResponse.from_sdk_object(l7_policy)
        l7_policy_data.provider = PROVIDER
        LOG.debug('Created L7 Policy according to API is %s' % l7_policy_data)
        return l7_policy_data

    def l7policy_update(self, session, original_l7policy, new_attrs):
        LOG.debug('Updating L7 Policy')

        l7_policy = session.elb.update_l7_policy(
            l7_policy=original_l7policy.id,
            **new_attrs
        )

        l7_policy_data = _l7policy.L7PolicyResponse.from_sdk_object(l7_policy)
        l7_policy_data.provider = PROVIDER
        return l7_policy_data

    def l7policy_delete(self, session, l7policy, ignore_missing=True):
        LOG.debug('Deleting L7 Policy %s' % l7policy.to_dict())

        session.elb.delete_l7_policy(
            l7_policy=l7policy.id,
            ignore_missing=ignore_missing
        )

    def l7rules(self, session, project_id, l7policy_id, query_filter=None):
        LOG.debug('Fetching l7 rules')

        result = []

        if not query_filter:
            query_filter = {}

        if 'id' in query_filter:
            l7rule_data = self.l7rule_get(
                project_id=project_id, session=session,
                l7policy_id=l7policy_id,
                l7rule_id=query_filter['id'],
            )
            if l7rule_data:
                result.append(l7rule_data)
        else:
            for l7rule in session.elb.l7_rules(l7policy_id, **query_filter):
                l7rule_data = _l7rule.L7RuleResponse.from_sdk_object(l7rule)
                l7rule_data.provider = PROVIDER
                result.append(l7rule_data)

        return result

    def l7rule_get(self, session, project_id, l7policy_id, l7rule_id):
        LOG.debug('Searching l7 rule')

        l7rule = session.elb.find_l7_rule(
            name_or_id=l7rule_id, l7_policy=l7policy_id, ignore_missing=True)
        if l7rule:
            l7rule_data = _l7rule.L7RuleResponse.from_sdk_object(l7rule)
            l7rule_data.provider = PROVIDER
            return l7rule_data

    def l7rule_create(self, session, l7policy_id, l7rule):
        LOG.debug('Creating l7 rule %s' % l7rule.to_dict())

        attrs = l7rule.to_dict()

        res = session.elb.create_l7_rule(l7_policy=l7policy_id, **attrs)
        result_data = _l7rule.L7RuleResponse.from_sdk_object(res)
        setattr(result_data, 'provider', PROVIDER)
        return result_data

    def l7rule_update(self, session, l7policy_id, original, new_attrs):
        LOG.debug('Updating l7 rule')

        res = session.elb.update_l7_rule(
            original.id,
            l7policy_id,
            **new_attrs)
        result_data = _l7rule.L7RuleResponse.from_sdk_object(
            res)
        result_data.provider = PROVIDER
        return result_data

    def l7rule_delete(self, session, l7policy_id, l7rule):
        LOG.debug('Deleting l7 rule %s' % l7rule.to_dict())

        session.elb.delete_l7_rule(l7rule.id, l7policy_id)

    def flavors(self, session, project_id, query_filter=None):
        LOG.debug('Fetching flavors')

        result = []
        return result

    def flavor_get(self, session, project_id, fl_id):
        LOG.debug('Searching flavor')

    def availability_zones(self, session, project_id, query_filter=None):
        LOG.debug('Fetching availability zones')

        if not query_filter:
            query_filter = {}

        result = []

        for az in session.elb.availability_zones(**query_filter):
            az.enabled = az.is_enabled
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
        quota = session.elb.quotas(**query_filter)
        if quota:
            quota_data = _quotas.QuotaResponse.from_sdk_object(
                quota
            )
            quota_data.provider = PROVIDER
            result.append(quota_data)
        return result

    def quota_get(self, session, project_id, quota_id):
        LOG.debug('Searching for quotas')

        quota = session.elb.get_quota(quota_id)
        LOG.debug('quotas is %s' % quota)

        if quota:
            quota_data = _quotas.QuotaResponse.from_sdk_object(
                quota
            )
            quota_data.provider = PROVIDER
            return quota_data
