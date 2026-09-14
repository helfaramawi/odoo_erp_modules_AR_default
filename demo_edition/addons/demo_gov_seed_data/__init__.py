import os
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Apply DEMO_USERS_PASSWORD (if set) to every seeded demo.* account.

    Keeps the shipped XML data free of any environment-specific secret
    while still giving each demo deployment its own password.
    """
    password = os.environ.get('DEMO_USERS_PASSWORD')
    if not password:
        _logger.info(
            "DEMO_USERS_PASSWORD not set — demo.* accounts keep the "
            "default demo-only password shipped in demo_users.xml."
        )
        return
    demo_users = env['res.users'].sudo().search([('login', 'like', 'demo.%')])
    demo_users.write({'password': password})
    _logger.info("Applied DEMO_USERS_PASSWORD to %d demo accounts.", len(demo_users))
