from wsme import types as wtypes
from wsmeext import pecan as wsme_pecan

from octavia_proxy.api.v2.controllers import base
from octavia_proxy.api.v2.controllers import flavors
from octavia_proxy.api.v2.controllers import listener
from octavia_proxy.api.v2.controllers import load_balancer
from octavia_proxy.api.v2.controllers import l7policy
from octavia_proxy.api.v2.controllers import pool
from octavia_proxy.api.v2.controllers import provider
from octavia_proxy.api.v2.controllers import health_monitor
from octavia_proxy.api.v2.controllers import quotas
from octavia_proxy.api.v2.controllers import availability_zones


class BaseV2Controller(base.BaseController):
    loadbalancers = None
    listeners = None
    pools = None
    l7policies = None
    healthmonitors = None
    quotas = None

    def __init__(self):
        super().__init__()
        self.loadbalancers = load_balancer.LoadBalancersController()
        self.listeners = listener.ListenersController()
        self.pools = pool.PoolsController()
        self.l7policies = l7policy.L7PoliciesController()
        self.healthmonitors = health_monitor.HealthMonitorController()
        self.quotas = quotas.QuotasController()
        self.providers = provider.ProviderController()
        self.flavors = flavors.FlavorsController()
#        self.flavorprofiles = flavor_profiles.FlavorProfileController()
        self.availabilityzones = (
            availability_zones.AvailabilityZonesController())
#        self.availabilityzoneprofiles = (
#            availability_zone_profiles.AvailabilityZoneProfileController())

    @wsme_pecan.wsexpose(wtypes.text)
    def get(self):
        return "v2"


class OctaviaV2Controller(base.BaseController):
    amphorae = None

    def __init__(self):
        super().__init__()

    @wsme_pecan.wsexpose(wtypes.text)
    def get(self):
        return "v2"


class V2Controller(BaseV2Controller):
    lbaas = None

    def __init__(self):
        super().__init__()
        self.lbaas = BaseV2Controller()
        self.octavia = OctaviaV2Controller()
