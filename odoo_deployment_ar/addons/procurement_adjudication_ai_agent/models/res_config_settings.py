# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    adjudication_agent_enabled = fields.Boolean(
        string='تفعيل وكيل تحليل العروض',
        config_parameter='procurement_adjudication_ai_agent.enabled',
        default=True,
    )

    adjudication_agent_min_technical_score = fields.Float(
        string='الحد الأدنى للمطابقة الفنية %',
        config_parameter='procurement_adjudication_ai_agent.min_technical_score',
        default=70.0,
    )

    adjudication_agent_dumping_threshold = fields.Float(
        string='حد التحذير من الانخفاض عن القيمة التقديرية %',
        config_parameter='procurement_adjudication_ai_agent.dumping_threshold',
        default=-15.0,
        help='القيمة -15 تعني إصدار تحذير إذا كان العرض أقل من القيمة التقديرية بأكثر من 15%.',
    )

    adjudication_agent_auto_write_pass = fields.Boolean(
        string='تحديث نتيجة الاستيفاء الفني تلقائياً إن وجد الحقل',
        config_parameter='procurement_adjudication_ai_agent.auto_write_pass',
        default=False,
    )
