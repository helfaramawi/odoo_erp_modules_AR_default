# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPayrollTaxSettlement(models.Model):
    _name = 'demo_gov.hr.payroll.tax.settlement'
    _description = 'التسوية الضريبية السنوية للموظف — المتطلب الوظيفي 16'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fiscal_year desc'

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    fiscal_year = fields.Char(string='السنة', required=True,
                               default=lambda s: str(fields.Date.today().year))

    total_tax_withheld = fields.Float(string='إجمالي الضريبة المحصَّلة خلال العام', readonly=True)
    annual_gross_income = fields.Float(string='إجمالي الدخل السنوي', readonly=True)
    total_tax_due = fields.Float(string='الضريبة المستحقة الفعلية عن العام', readonly=True)
    adjustment_amount = fields.Float(string='فرق التسوية (موجب = مستحق على الموظف)',
                                      readonly=True)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('computed', 'محسوبة'),
        ('finalized', 'معتمَدة نهائياً'),
    ], default='draft', string='الحالة', tracking=True)

    _sql_constraints = [
        ('unique_settlement_per_year', 'unique(employee_id, fiscal_year)',
         'يوجد تسوية ضريبية مسجَّلة بالفعل لهذا الموظف عن نفس السنة.'),
    ]

    def action_compute(self):
        payslip_model = self.env['demo_gov.hr.payroll.payslip']
        category_model = self.env['demo_gov.hr.payroll.tax.category']
        for rec in self:
            payslips = payslip_model.search([
                ('employee_id', '=', rec.employee_id.id),
                ('year', '=', rec.fiscal_year),
            ])
            total_withheld = sum(payslips.mapped('income_tax_monthly'))
            annual_gross = sum(payslips.mapped('gross_earnings'))
            category = category_model.find_category_for_income(annual_gross)
            total_due = category.compute_tax(annual_gross) if category else 0.0
            rec.write({
                'total_tax_withheld': total_withheld,
                'annual_gross_income': annual_gross,
                'total_tax_due': total_due,
                'adjustment_amount': total_due - total_withheld,
                'state': 'computed',
            })

    def action_finalize(self):
        for rec in self:
            if rec.state != 'computed':
                raise UserError(_('لازم تحسب التسوية أولاً قبل الاعتماد النهائي.'))
        self.write({'state': 'finalized'})
