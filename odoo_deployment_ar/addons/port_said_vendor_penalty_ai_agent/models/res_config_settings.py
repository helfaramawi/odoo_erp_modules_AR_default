# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    vendor_penalty_agent_enabled = fields.Boolean(
        string='تفعيل وكيل جزاءات الموردين',
        config_parameter='port_said_vendor_penalty_ai_agent.enabled',
        default=True,
    )

    vendor_penalty_agent_first_rate = fields.Float(
        string='نسبة الجزاء للمخالفة الأولى',
        config_parameter='port_said_vendor_penalty_ai_agent.first_rate',
        default=0.05,
    )

    vendor_penalty_agent_second_rate = fields.Float(
        string='نسبة الجزاء للمخالفة الثانية',
        config_parameter='port_said_vendor_penalty_ai_agent.second_rate',
        default=0.10,
    )

    vendor_penalty_agent_third_rate = fields.Float(
        string='نسبة الجزاء للمخالفة الثالثة فأكثر',
        config_parameter='port_said_vendor_penalty_ai_agent.third_rate',
        default=0.15,
    )

    vendor_penalty_agent_auto_approve = fields.Boolean(
        string='اعتماد الجزاء تلقائياً إن كان الإجراء متاحاً',
        config_parameter='port_said_vendor_penalty_ai_agent.auto_approve',
        default=False,
    )
