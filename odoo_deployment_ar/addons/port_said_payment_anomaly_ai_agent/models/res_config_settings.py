# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_anomaly_agent_enabled = fields.Boolean(
        string='تفعيل وكيل كشف شذوذ المدفوعات',
        config_parameter='port_said_payment_anomaly_ai_agent.enabled',
        default=True,
    )
    payment_anomaly_zscore_threshold = fields.Float(
        string='حد Z-Score',
        config_parameter='port_said_payment_anomaly_ai_agent.zscore_threshold',
        default=2.0,
    )
    payment_anomaly_min_history = fields.Integer(
        string='أقل عدد معاملات تاريخية للتحليل الإحصائي',
        config_parameter='port_said_payment_anomaly_ai_agent.min_history',
        default=5,
    )
    payment_anomaly_duplicate_days = fields.Integer(
        string='مدة كشف تكرار نفس المبلغ بالأيام',
        config_parameter='port_said_payment_anomaly_ai_agent.duplicate_days',
        default=30,
    )
    payment_anomaly_large_new_vendor_amount = fields.Float(
        string='حد المورد الجديد بمبلغ كبير',
        config_parameter='port_said_payment_anomaly_ai_agent.large_new_vendor_amount',
        default=100000.0,
    )
    payment_anomaly_fy_end_days = fields.Integer(
        string='عدد أيام نهاية السنة المالية للمراقبة',
        config_parameter='port_said_payment_anomaly_ai_agent.fy_end_days',
        default=30,
    )
    payment_anomaly_block_high_risk = fields.Boolean(
        string='إيقاف المعاملة عالية المخاطر للمراجعة',
        config_parameter='port_said_payment_anomaly_ai_agent.block_high_risk',
        default=False,
    )
