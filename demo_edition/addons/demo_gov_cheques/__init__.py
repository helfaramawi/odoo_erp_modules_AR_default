from . import models
from . import wizard


def post_init_hook(env):
    """Grant the demo Administrator group_cheques_manager - see
    demo_gov_subsidiary_books/__init__.py for why this can't be a plain
    XML <record id="base.user_admin"> data record."""
    env.ref('base.user_admin').write({
        'groups_id': [(4, env.ref('demo_gov_cheques.group_cheques_manager').id)],
    })
