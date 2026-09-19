# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrEmployeeSalaryLine(models.Model):
    _name = 'demo_gov.hr.employee.salary.line'
    _description = 'بند استحقاق أو استقطاع في ملف مرتب الموظف'

    salary_id = fields.Many2one('demo_gov.hr.employee.salary', string='ملف المرتب',
                                 required=True, ondelete='cascade')
    component_id = fields.Many2one('demo_gov.hr.payroll.component', string='البند', required=True)
    component_type = fields.Selection(related='component_id.component_type', store=True,
                                       string='النوع')
    amount = fields.Float(string='المبلغ')
    # تُملأ فقط لبنود الاستقطاعات الخاصة بالأقساط والنفقة
    installment_start_date = fields.Date(string='تاريخ بداية القسط')
    installment_end_date = fields.Date(string='تاريخ نهاية القسط')
    alimony_beneficiary_name = fields.Char(string='اسم المستفيد (نفقة)')
    alimony_beneficiary_address = fields.Char(string='عنوان المستفيد (نفقة)')


class HrEmployeeSalary(models.Model):
    _name = 'demo_gov.hr.employee.salary'
    _description = 'ملف مرتب الموظف — المتطلب الوظيفي 8'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True,
                                     string='الإدارة')
    spouse_works = fields.Boolean(related='employee_id.spouse_works', string='الزوج/الزوجة يعمل')
    num_dependents = fields.Integer(related='employee_id.num_dependents', string='عدد المعولين')
    fund_subscription_amount = fields.Float(related='employee_id.fund_subscription_amount',
                                             string='قيمة اشتراك الصندوق')

    is_taxable = fields.Boolean(string='خاضع للضريبة', default=True)
    is_insurable = fields.Boolean(string='خاضع للتأمينات', default=True)
    employee_category = fields.Char(string='فئة الموظف')
    employee_status = fields.Char(string='حالة الموظف')
    disbursement_number = fields.Char(string='رقم الصرف')
    salary_30_6_2015 = fields.Float(string='المرتب في 2015/6/30')
    special_allowances_pre_law = fields.Float(string='العلاوات الخاصة قبل العمل بالقانون')
    disbursement_entity = fields.Selection([
        ('diwan', 'الديوان العام للمحافظة التجريبية'),
        ('funds', 'الصناديق'),
    ], string='جهة الصرف', default='diwan', required=True, tracking=True)

    job_wage = fields.Float(string='الأجر الوظيفي', tracking=True)

    # تفاصيل جهة الصرف (البنك)
    bank_id = fields.Many2one('res.bank', string='اسم البنك')
    bank_branch = fields.Char(string='اسم الفرع')
    bank_address = fields.Char(string='عنوان البنك')
    disbursement_method = fields.Selection([
        ('atm', 'بطاقة ATM'),
        ('transfer', 'تحويل بنكي'),
    ], string='طريقة الصرف')
    bank_account_number = fields.Char(string='رقم الحساب البنكي')

    salary_line_ids = fields.One2many('demo_gov.hr.employee.salary.line', 'salary_id',
                                       string='الاستحقاقات والاستقطاعات')
    total_earnings = fields.Float(compute='_compute_totals', string='إجمالي الاستحقاقات')
    total_deductions = fields.Float(compute='_compute_totals', string='إجمالي الاستقطاعات')

    insurance_subscription_wage = fields.Float(string='أجر الاشتراك التأميني', readonly=True,
                                                tracking=True)

    active = fields.Boolean(string='نشط', default=True)

    _sql_constraints = [
        ('unique_employee', 'unique(employee_id)',
         'يوجد ملف مرتب مسجَّل بالفعل لهذا الموظف.'),
    ]

    @api.depends('salary_line_ids.amount', 'salary_line_ids.component_type')
    def _compute_totals(self):
        for rec in self:
            rec.total_earnings = sum(
                rec.salary_line_ids.filtered(lambda l: l.component_type == 'earning').mapped('amount'))
            rec.total_deductions = sum(
                rec.salary_line_ids.filtered(lambda l: l.component_type == 'deduction').mapped('amount'))

    def action_compute_insurance_wage(self):
        insurance_model = self.env['demo_gov.hr.payroll.insurance.bracket']
        for rec in self:
            if not rec.is_insurable:
                rec.insurance_subscription_wage = 0.0
                continue
            bracket = insurance_model.get_bracket_for_year(fields.Date.today().year)
            gross = rec.job_wage + rec.total_earnings
            if bracket:
                rec.insurance_subscription_wage = bracket.compute_contributions(gross)['insurable_wage']
            else:
                rec.insurance_subscription_wage = gross
