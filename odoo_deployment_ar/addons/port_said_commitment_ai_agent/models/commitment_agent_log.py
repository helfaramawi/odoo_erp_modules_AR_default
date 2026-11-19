# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidCommitmentAgentLog(models.Model):
    _name = 'port_said.commitment.agent.log'
    _description = 'سجل قرارات وكيل أتمتة الارتباطات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'decision_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='رقم القرار', required=True, copy=False, default='جديد', tracking=True)
    decision_date = fields.Datetime(string='تاريخ القرار', default=fields.Datetime.now, required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='المستخدم', default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company)

    requisition_id = fields.Many2one('port_said.requisition', string='الطلب', index=True, ondelete='set null')
    commitment_id = fields.Many2one('port_said.commitment', string='الارتباط', index=True, ondelete='set null')
    vendor_id = fields.Many2one('res.partner', string='المورد', index=True)

    total_amount = fields.Float(string='إجمالي الطلب')
    available_balance = fields.Float(string='الرصيد المتاح')
    auto_commit_limit = fields.Float(string='حد الأتمتة المستخدم')

    risk_level = fields.Selection([
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
    ], string='مستوى المخاطر', default='medium', required=True, tracking=True)

    risk_score = fields.Float(string='درجة المخاطر')
    vendor_has_penalties = fields.Boolean(string='يوجد جزاءات على المورد')
    penalty_summary = fields.Text(string='ملخص الجزاءات')

    decision = fields.Selection([
        ('auto_reserved', 'تم الاعتماد والتجنيب تلقائياً'),
        ('manual_review', 'تم التحويل لمراجعة بشرية'),
        ('skipped_no_commitment', 'لم يتم العثور على ارتباط'),
        ('skipped_config', 'الأتمتة غير مفعلة'),
        ('failed', 'فشل التنفيذ'),
    ], string='القرار', required=True, default='manual_review', tracking=True, index=True)

    decision_reason = fields.Text(string='سبب القرار')
    technical_details = fields.Text(string='تفاصيل تقنية')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = seq.next_by_code('port_said.commitment.agent.log') or 'جديد'
        return super().create(vals_list)

    def action_open_requisition(self):
        self.ensure_one()
        if not self.requisition_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('الطلب'),
            'res_model': 'port_said.requisition',
            'res_id': self.requisition_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_commitment(self):
        self.ensure_one()
        if not self.commitment_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('الارتباط'),
            'res_model': 'port_said.commitment',
            'res_id': self.commitment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
