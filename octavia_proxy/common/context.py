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
        if project_id:
            kwargs['tenant'] = project_id

        super().__init__(**kwargs)

        self.is_admin = False

    def set_token_info(self, token_info):
        """Set token into to be able to recreate session

        :param dict token_info: Token structure
        """
        self.token_info = token_info

        self.token_auth = token.Token(auth_url=CONF.validatetoken.auth_url)
        self.token_auth.auth_ref = access.create(
            body=token_info,
            auth_token=self.auth_token
        )

    @property
    def session(self):
        # Establish real session only when required
        if self._session is None:
            # Initiate KS session from the existing token
            sess = session.Session(auth=self.token_auth)
            # Initiate SDK connection from the session loading the hook to
            # enable OTCE
            sdk = openstack.connection.Connection(
                session=sess,
                vendor_hook='otcextensions.sdk:load')
            self._session = sdk
        return self._session

    @property
    def project_id(self):
        return self.tenant
