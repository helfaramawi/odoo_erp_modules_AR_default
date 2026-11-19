# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    commitment_agent_enabled = fields.Boolean(
        string='تفعيل أتمتة الارتباطات الصغيرة',
        config_parameter='port_said_commitment_ai_agent.enabled',
        default=True,
    )

    commitment_agent_auto_limit = fields.Float(
        string='حد الأتمتة التلقائية',
        config_parameter='port_said_commitment_ai_agent.auto_limit',
        default=50000.0,
    )

    commitment_agent_require_available_balance = fields.Boolean(
        string='اشتراط كفاية الرصيد المتاح',
        config_parameter='port_said_commitment_ai_agent.require_available_balance',
        default=True,
    )

    commitment_agent_strict_vendor_penalties = fields.Boolean(
        string='منع الأتمتة عند وجود جزاءات للمورد',
        config_parameter='port_said_commitment_ai_agent.strict_vendor_penalties',
        default=True,
    )

    commitment_agent_notify_user_id = fields.Many2one(
        'res.users',
        string='المستخدم المسؤول عن المراجعة البشرية',
        config_parameter='port_said_commitment_ai_agent.notify_user_id',
    )
