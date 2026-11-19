# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# نسبة الاستبدال القصوى (80% بعد 40 سنة اشتراك) رقم توضيحي فقط لمحاكاة
# منطق قانون التأمينات الاجتماعية والمعاشات الموحد — يحتاج اعتماد الإدارة
# المالية/الشؤون القانونية على آخر تعديل تشريعي قبل أي استخدام فعلي.
MAX_REPLACEMENT_RATIO = 0.8
FULL_SERVICE_YEARS = 40


class HrPensionSettlement(models.Model):
    _name = 'demo_gov.hr.pension.settlement'
    _description = 'تسوية المعاش عند سن 60 — FDD-HR-08'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'settlement_date desc'

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    years_of_service = fields.Integer(related='employee_id.years_of_service', store=True,
                                       string='سنوات الخدمة')
    termination_type = fields.Selection(related='employee_id.gov_termination_type', store=True,
                                         string='نوع إنهاء الخدمة')
    settlement_date = fields.Date(string='تاريخ التسوية', default=fields.Date.today, required=True)
    final_pensionable_salary = fields.Float(string='الأجر التقاعدي الأخير', required=True)
    pension_amount = fields.Float(string='قيمة المعاش الشهري المستحق', readonly=True)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('computed', 'محسوبة'),
        ('approved', 'معتمَدة'),
        ('form15_issued', 'صدرت استمارة 15'),
    ], default='draft', string='الحالة', tracking=True)

    _sql_constraints = [
        ('unique_settlement_per_employee', 'unique(employee_id)',
         'يوجد تسوية معاش مسجَّلة بالفعل لهذا الموظف.'),
    ]

    def action_compute(self):
        for rec in self:
            ratio = min(rec.years_of_service / FULL_SERVICE_YEARS, 1.0) * MAX_REPLACEMENT_RATIO
            rec.write({
                'pension_amount': rec.final_pensionable_salary * ratio,
                'state': 'computed',
            })

    def action_approve(self):
        for rec in self:
            if rec.state != 'computed':
                raise UserError(_('لازم تحسب قيمة المعاش أولاً.'))
        self.write({'state': 'approved'})

    def action_mark_form15_issued(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('لازم تعتمد التسوية أولاً قبل إصدار استمارة 15.'))
        self.write({'state': 'form15_issued'})
