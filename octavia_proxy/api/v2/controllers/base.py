from oslo_config import cfg
from oslo_log import log as logging
from pecan import rest as pecan_rest
from wsme import types as wtypes

from octavia_proxy.api.common.invocation import driver_invocation
from octavia_proxy.api.drivers import driver_factory
from octavia_proxy.api.drivers import utils as driver_utils
from octavia_proxy.common import constants
from octavia_proxy.common import exceptions
from octavia_proxy.common import policy
from octavia_proxy.i18n import _

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class BaseController(pecan_rest.RestController):
    RBAC_TYPE = None

    def __init__(self):
        super().__init__()

    @staticmethod
    def _convert_sdk_to_type(sdk_entity, to_type, children=False):
        """Converts a data model into an Octavia WSME type
        :param db_entity: data model to convert
        :param to_type: converts db_entity to this type
        """
        LOG.debug('Converting %s' % sdk_entity)
        if isinstance(to_type, list):
            to_type = to_type[0]

        def _convert(db_obj):
            return to_type.from_data_model(db_obj, children=children)

        if isinstance(sdk_entity, list):
            converted = [_convert(sdk_obj) for sdk_obj in sdk_entity]
        else:
            converted = _convert(sdk_entity)
        return converted

    def find_load_balancer(self, context, id, is_parallel=False):
        load_balancer = driver_invocation(
            context, 'loadbalancer_get', id, is_parallel
        )

        if not load_balancer:
            raise exceptions.NotFound(
                resource='LoadBalancer',
                id=id)

        return load_balancer

    def find_listener(self, context, id, is_parallel=False):
        listener = driver_invocation(
            context, 'listener_get', id, is_parallel
        )

        if not listener:
            raise exceptions.NotFound(
                resource='Listener',
                id=id)

        return listener

    def find_pool(self, context, id, is_parallel=False):
        pool = driver_invocation(
            context, 'pool_get', id, is_parallel
        )

        if not pool:
            raise exceptions.NotFound(
                resource='Pool',
                id=id)

        return pool

    def find_member(self, context, pool_id, id):
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        # TODO: perhaps memcached
        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                member = driver_utils.call_provider(
                    driver.name, driver.member_get,
                    context.session,
                    context.project_id,
                    pool_id,
                    id)
                if member:
                    setattr(member, 'provider', provider)
                    break
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

        if not member:
            raise exceptions.NotFound(
                resource='Member',
                id=id)

        return member

    def find_health_monitor(self, context, id):
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        # TODO: perhaps memcached
        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                hm = driver_utils.call_provider(
                    driver.name, driver.health_monitor_get,
                    context.session,
                    context.project_id,
                    id)
                if hm:
                    setattr(hm, 'provider', provider)
                    break
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

        if not hm:
            raise exceptions.NotFound(
                resource='Healthmonitor',
                id=id)

        return hm

    def find_l7policy(self, context, id):
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        # TODO: perhaps memcached
        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                l7policy = driver_utils.call_provider(
                    driver.name, driver.l7policy_get,
                    context.session,
                    context.project_id,
                    id)
                if l7policy:
                    setattr(l7policy, 'provider', provider)
                    break
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

        if not l7policy:
            raise exceptions.NotFound(
                resource='L7Policy',
                id=id)

        return l7policy

    def find_l7rule(self, context, l7policy_id, id):
        enabled_providers = CONF.api_settings.enabled_provider_drivers
        # TODO: perhaps memcached
        l7rule = None
        for provider in enabled_providers:
            driver = driver_factory.get_driver(provider)

            try:
                l7rule = driver_utils.call_provider(
                    driver.name, driver.l7rule_get,
                    context.session,
                    context.project_id,
                    l7policy_id,
                    id)
                if l7rule:
                    setattr(l7rule, 'provider', provider)
                    break
            except exceptions.ProviderNotImplementedError:
                LOG.exception('Driver %s is not supporting this')

        if not l7rule:
            raise exceptions.NotFound(
                resource='L7 rule',
                id=id)

        return l7rule

    @staticmethod
    def _validate_protocol(listener_protocol, pool_protocol):
        proto_map = constants.VALID_LISTENER_POOL_PROTOCOL_MAP
        for valid_pool_proto in proto_map[listener_protocol]:
            if pool_protocol == valid_pool_proto:
                return
        detail = _("The pool protocol '%(pool_protocol)s' is invalid while "
                   "the listener protocol is '%(listener_protocol)s'.") % {
                     "pool_protocol": pool_protocol,
                     "listener_protocol": listener_protocol}
        raise exceptions.ValidationException(detail=detail)

    def _is_only_specified_in_request(self, request, **kwargs):
        request_attrs = []
        check_attrs = kwargs['check_exist_attrs']
        escaped_attrs = ['from_data_model', 'translate_key_to_data_model',
                         'translate_dict_keys_to_data_model', 'to_dict']

        for attr in dir(request):
            if attr.startswith('_') or attr in escaped_attrs:
                continue
            request_attrs.append(attr)

        for req_attr in request_attrs:
            if (getattr(request, req_attr) and req_attr not in check_attrs):
                return False
        return True

    def _validate_pool_request_for_tcp_udp(self, request):
        sp_type = [constants.SESSION_PERSISTENCE_HTTP_COOKIE,
                   constants.SESSION_PERSISTENCE_APP_COOKIE]
        if request.session_persistence:
            if (request.session_persistence.type ==
                    constants.SESSION_PERSISTENCE_SOURCE_IP and
                    not self._is_only_specified_in_request(
                        request=request.session_persistence,
                        check_exist_attrs=['type', 'persistence_timeout'])):
                raise exceptions.ValidationException(
                    detail=_(
                        "session_persistence %s type for TCP and UDP protocol "
                        "only accepts: type, persistence_timeout."
                        "") % constants.SESSION_PERSISTENCE_SOURCE_IP)
            if request.session_persistence.cookie_name:
                raise exceptions.ValidationException(
                    detail=_("Cookie names are not supported"
                             " for %s pools.") % "/".join(
                        (constants.PROTOCOL_UDP,
                         constants.PROTOCOL_TCP)))
            if request.session_persistence.type in sp_type:
                raise exceptions.ValidationException(
                    detail=_(
                        "Session persistence of type %(type)s is not supported"
                        " for %(protocol)s protocol pools.") % {
                               'type': request.session_persistence.type,
                               'protocol': "/".join((constants.PROTOCOL_UDP,
                                                     constants.PROTOCOL_TCP))})

    def _validate_healthmonitor_request_for_udp(self, request,
                                                pool_protocol):
        if request.type not in (
                constants.HEALTH_MONITOR_UDP_CONNECT,
                constants.HEALTH_MONITOR_TCP,
                constants.HEALTH_MONITOR_HTTP,
                constants.HEALTH_MONITOR_HTTPS,
                constants.HEALTH_MONITOR_PING):
            raise exceptions.ValidationException(detail=_(
                "The associated pool protocol is %(pool_protocol)s, so only "
                "a %(types)s health monitor is supported.") % {
                'pool_protocol': pool_protocol,
                'types': '/'.join((constants.HEALTH_MONITOR_UDP_CONNECT,
                                   constants.HEALTH_MONITOR_TCP,
                                   constants.HEALTH_MONITOR_HTTP,
                                   constants.HEALTH_MONITOR_HTTPS,
                                   constants.HEALTH_MONITOR_PING))})
        # check the delay value if the HM type is UDP-CONNECT
        if request.type == constants.HEALTH_MONITOR_UDP_CONNECT:
            hm_is_type_udp = request.type
        conf_min_delay = (
            CONF.api_settings.udp_connect_min_interval_health_monitor)
        if hm_is_type_udp and request.delay < conf_min_delay:
            raise exceptions.ValidationException(detail=_(
                "The request delay value %(delay)s should be larger than "
                "%(conf_min_delay)s for %(type)s health monitor type.") % {
                'delay': request.delay,
                'conf_min_delay': conf_min_delay,
                'type': constants.HEALTH_MONITOR_UDP_CONNECT})

    def _auth_get_all(self, context, project_id):
        # Check authorization to list objects under all projects
        action = '{rbac_obj}{action}'.format(
            rbac_obj=self.RBAC_TYPE, action=constants.RBAC_GET_ALL_GLOBAL)
        target = {'project_id': project_id}
        if not policy.get_enforcer().authorize(action, target,
                                               context, do_raise=False):
            # Not a global observer or admin
            if project_id is None:
                project_id = context.project_id

            # If we still don't know who it is, reject it.
            if project_id is None:
                raise exceptions.PolicyForbidden()

            # Check authorization to list objects under this project
            self._auth_validate_action(context, project_id,
                                       constants.RBAC_GET_ALL)
        if project_id is None:
            query_filter = {}
        else:
            query_filter = {'project_id': project_id}
        return query_filter

    def _auth_validate_action(self, context, project_id, action):
        # Check that the user is authorized to do an action in this object
        action = '{rbac_obj}{action}'.format(
            rbac_obj=self.RBAC_TYPE, action=action)
        target = {'project_id': project_id}
        policy.get_enforcer().authorize(action, target, context)

    def _filter_fields(self, object_list, fields):
        if CONF.api_settings.allow_field_selection:
            for index, obj in enumerate(object_list):
                members = self._get_attrs(obj)
                for member in members:
                    if member not in fields:
                        setattr(obj, member, wtypes.Unset)
        return object_list

    @staticmethod
    def _get_attrs(obj):
        attrs = [attr for attr in dir(obj) if not callable(
            getattr(obj, attr)) and not attr.startswith("_")]
        return attrs
