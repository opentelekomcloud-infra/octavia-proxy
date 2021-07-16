from pecan import hooks

from oslo_log import log as logging
from oslo_config import cfg

from octavia_proxy.common import constants

from octavia_proxy.api.common import pagination
from octavia_proxy.common import context

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class ContextHook(hooks.PecanHook):
    """Configures a request context and attaches it to the request."""

    def on_route(self, state):
        context_obj = context.Context.from_environ(state.request.environ)
        token_info = state.request.environ.get('keystone.token_info')
        if token_info:
            context_obj.set_token_info(token_info)
        state.request.context['octavia_context'] = context_obj


class QueryParametersHook(hooks.PecanHook):

    def before(self, state):
        if state.request.method != 'GET':
            return

        state.request.context[
            constants.PAGINATION_HELPER] = pagination.PaginationHelper(
            state.request.params.mixed())
