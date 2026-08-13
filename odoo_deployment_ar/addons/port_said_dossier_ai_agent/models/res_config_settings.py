# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dossier_agent_ai_enabled = fields.Boolean(
        string='تفعيل الفحص الذكي لمحتوى المرفقات',
        config_parameter='port_said_dossier_ai_agent.ai_enabled',
        default=False,
    )

    dossier_agent_ai_strict = fields.Boolean(
        string='منع الصرف عند فشل الفحص الذكي',
        config_parameter='port_said_dossier_ai_agent.ai_strict',
        default=False,
        help='إذا لم يتم تفعيل هذا الخيار، سيتم تسجيل التحذير فقط ولن يتم منع الاعتماد إلا عند نقص مستندات الإضبارة.',
    )

    dossier_agent_block_unreadable = fields.Boolean(
        string='منع الصرف إذا تعذر قراءة المرفق',
        config_parameter='port_said_dossier_ai_agent.block_unreadable',
        default=False,
        help='يستخدم فقط عند تفعيل الفحص الذكي الصارم.',
    )

    dossier_agent_reference_fields = fields.Char(
        string='حقول مرجع أمر التوريد المحتملة',
        config_parameter='port_said_dossier_ai_agent.reference_fields',
        default='purchase_order_id,name,origin,reference,po_number,supply_order_no',
        help='أسماء الحقول التي سيتم البحث فيها عن رقم أمر التوريد أو المرجع لمطابقته داخل المرفقات.',
    )
