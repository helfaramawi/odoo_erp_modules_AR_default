# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidVendorPenaltyAgentLog(models.Model):
    _name = 'port_said.vendor.penalty.agent.log'
    _description = 'سجل وكيل جزاءات الموردين'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='رقم السجل', required=True, copy=False, default='جديد', tracking=True)
    inspection_id = fields.Many2one('port_said.inspection.committee', string='محضر لجنة الفحص', index=True, ondelete='cascade')
    purchase_order_id = fields.Many2one('purchase.order', string='أمر التوريد', index=True)
    vendor_id = fields.Many2one('res.partner', string='المورد', index=True)
    penalty_id = fields.Many2one('port_said.penalty', string='الجزاء الناتج', index=True)
    user_id = fields.Many2one('res.users', string='المستخدم', default=lambda self: self.env.user)
    decision = fields.Selection([
        ('created', 'تم إنشاء الجزاء'),
        ('skipped', 'لم يتم الإنشاء'),
        ('duplicate', 'جزاء موجود مسبقاً'),
        ('error', 'خطأ أثناء الإنشاء'),
    ], string='قرار الوكيل', required=True, default='skipped', tracking=True)

    result = fields.Char(string='نتيجة الفحص')
    specs_conformity = fields.Char(string='مطابقة المواصفات')
    quantity_rejected = fields.Float(string='الكمية المرفوضة')
    offense_count = fields.Integer(string='عدد المخالفات السابقة')
    penalty_rate = fields.Float(string='نسبة الجزاء')
    rejected_value = fields.Float(string='قيمة الجزء المرفوض')
    penalty_amount = fields.Float(string='قيمة الجزاء')
    notification_text = fields.Text(string='نص الإخطار الرسمي')
    decision_reason = fields.Text(string='سبب القرار')
    technical_details = fields.Text(string='تفاصيل تقنية')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = seq.next_by_code('port_said.vendor.penalty.agent.log') or 'جديد'
        return super().create(vals_list)

    def action_open_inspection(self):
        self.ensure_one()
        if not self.inspection_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('محضر لجنة الفحص'),
            'res_model': 'port_said.inspection.committee',
            'res_id': self.inspection_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_penalty(self):
        self.ensure_one()
        if not self.penalty_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('الجزاء'),
            'res_model': 'port_said.penalty',
            'res_id': self.penalty_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
