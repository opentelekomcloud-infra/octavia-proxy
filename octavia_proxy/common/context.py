from oslo_config import cfg
from oslo_context import context as common_context
from oslo_log import log as logging

import openstack
from keystoneauth1.identity.generic import token
from keystoneauth1 import access
from keystoneauth1 import session

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class Context(common_context.RequestContext):
    _session = None

    def __init__(self, user_id=None, project_id=None, **kwargs):
        super().__init__(**kwargs)

    def set_token_info(self, token_info):
        """Set token into to be able to recreate session

        :param dict token_info: Token structure
        """
        self.project_id = token_info['token']['project']['id']
        self.token_info = token_info

        self.token_auth = token.Token(
            auth_url=CONF.validatetoken.www_authenticate_uri)
        self.token_auth.auth_ref = access.create(
            body=token_info,
            auth_token=self.auth_token
        )

    @property
    def session(self):
        driver_opts = self.additional_driver_settings()
        # Establish real session only when required
        if self._session is None:
            # Initiate KS session from the existing token
            sess = session.Session(auth=self.token_auth)
            # Initiate SDK connection from the session loading the hook to
            # enable OTCE
            sdk = openstack.connection.Connection(
                session=sess,
                vendor_hook='otcextensions.sdk:load',
                region_name=CONF.api_settings.region,
                **driver_opts
            )
            self._session = sdk
        return self._session

    def additional_driver_settings(self):
        opts = {}
        for k, v in CONF.api_settings.enabled_provider_drivers.items():
            drv = getattr(CONF, f'{k}_driver_settings', None)
            if hasattr(drv, 'endpoint_override'):
                if drv.endpoint_override:
                    if k == 'elbv2':
                        opts['elb_endpoint_override'] = drv.endpoint_override
                    else:
                        opts['elbv3_endpoint_override'] = drv.endpoint_override
        return opts
