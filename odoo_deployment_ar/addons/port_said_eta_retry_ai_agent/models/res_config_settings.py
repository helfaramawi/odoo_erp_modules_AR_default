# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    eta_retry_agent_enabled = fields.Boolean(
        string='تفعيل وكيل ETA لإعادة المحاولة',
        config_parameter='port_said_eta_retry_ai_agent.enabled',
        default=True,
    )
    eta_retry_agent_max_attempts = fields.Integer(
        string='أقصى عدد محاولات إعادة إرسال',
        config_parameter='port_said_eta_retry_ai_agent.max_attempts',
        default=5,
    )
    eta_retry_agent_auto_retry_network = fields.Boolean(
        string='إعادة المحاولة تلقائياً لأخطاء الشبكة',
        config_parameter='port_said_eta_retry_ai_agent.auto_retry_network',
        default=True,
    )
    eta_retry_agent_backoff_base_hours = fields.Integer(
        string='أساس الانتظار بالساعات Backoff',
        config_parameter='port_said_eta_retry_ai_agent.backoff_base_hours',
        default=2,
    )
