# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# بند الراتب — قائمة أسباب حركة التأثيرات الاستثنائية (المتطلب الوظيفي 10)
PAYROLL_TRANSACTION_REASONS = [
    ('transfer_to_entity', 'النقل إلى جهة'),
    ('appointment_start', 'بداية التعيين'),
    ('service_end', 'إنهاء الخدمة'),
    ('penalty', 'جزاء'),
    ('special_leave', 'إجازة خاصة'),
    ('childcare_leave', 'إجازة رعاية الطفل'),
    ('absence', 'انقطاع'),
    ('part_time_65', 'جزء من الوقت 65%'),
    ('chronic_illness', 'أمراض مزمنة'),
    ('sick_excess_75', 'تجاوز مرضى 75%'),
    ('sick_excess_50', 'تجاوز مرضى 50%'),
    ('leave_with_deduction', 'إجازات بالخصم'),
    ('return_from_leave', 'استلام العمل من إجازة'),
    ('suspension_50', 'إيقاف عن العمل صرف 50%'),
]


class HrPayrollTransaction(models.Model):
    _name = 'demo_gov.hr.payroll.transaction'
    _description = 'حركة تأثيرات استثنائية على الراتب — المتطلب الوظيفي 10'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transaction_date desc, id desc'

    name = fields.Char(string='رقم الحركة', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    reason = fields.Selection(PAYROLL_TRANSACTION_REASONS, string='بند الراتب', required=True)
    amount = fields.Float(string='المبلغ')
    days = fields.Integer(string='الأيام')
    month_days = fields.Integer(string='عدد أيام الشهر', default=30)
    transaction_date = fields.Date(string='التاريخ', default=fields.Date.today)
    decision_date = fields.Date(string='تاريخ تنفيذ القرار')
    notes = fields.Text(string='ملاحظات')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('executed', 'منفَّذة'),
    ], default='draft', string='الحالة', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.payroll.transaction') or '/'
        return super().create(vals_list)

    def action_execute(self):
        for rec in self:
            if not rec.decision_date:
                raise UserError(_('لازم تحدد تاريخ تنفيذ القرار قبل تنفيذ العملية.'))
        self.write({'state': 'executed'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
