# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def post_init_hook(env):
    # Odoo 17 passes env in newer signatures in many deployments.
    try:
        env['port_said.ai.agents.menu.manager'].sudo().action_refresh_ai_agents_menu()
    except Exception:
        pass


def post_init_hook_cr(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['port_said.ai.agents.menu.manager'].sudo().action_refresh_ai_agents_menu()
