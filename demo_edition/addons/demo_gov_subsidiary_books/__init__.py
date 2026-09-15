from . import models
from . import wizard


def post_init_hook(env):
    """Grant the demo Administrator group_subsidiary_manager.

    A plain XML <record id="base.user_admin"> data record silently fails
    to persist this - verified live against a real Odoo 17 instance: the
    exact same (4, ref(...)) command works and survives every future
    upgrade when run through the ORM (env['res.users'].write(...)), but
    never takes effect when loaded from a module's non-noupdate XML data.
    See docs/demo/KNOWN_LIMITATIONS.md for the full investigation.
    """
    env.ref('base.user_admin').write({
        'groups_id': [(4, env.ref('demo_gov_subsidiary_books.group_subsidiary_manager').id)],
    })
