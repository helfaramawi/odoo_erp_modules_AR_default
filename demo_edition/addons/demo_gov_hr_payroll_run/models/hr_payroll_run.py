# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

MONTHS = [(str(i), str(i)) for i in range(1, 13)]


class HrPayrollRun(models.Model):
    _name = 'demo_gov.hr.payroll.run'
    _description = 'دورة الرواتب الشهرية — المتطلب الوظيفي 11'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, month desc'

    name = fields.Char(string='اسم الدورة', compute='_compute_name', store=True)
    month = fields.Selection(MONTHS, string='الشهر', required=True,
                              default=lambda s: str(fields.Date.today().month))
    year = fields.Char(string='السنة', required=True,
                        default=lambda s: str(fields.Date.today().year))
    disbursement_entity = fields.Selection([
        ('diwan', 'ديوان محافظة بورسعيد'),
        ('funds', 'الصناديق'),
    ], string='جهة الصرف', default='diwan', required=True)

    payslip_ids = fields.One2many('demo_gov.hr.payroll.payslip', 'run_id', string='كشوف المرتبات')
    payslip_count = fields.Integer(compute='_compute_payslip_count')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('computed', 'محسوبة'),
        ('under_review', 'تحت المراجعة'),
        ('approved', 'معتمَدة'),
        ('posted', 'مرحَّلة'),
    ], default='draft', string='الحالة', tracking=True)

    _sql_constraints = [
        ('unique_run_per_month', 'unique(month, year, disbursement_entity)',
         'يوجد دورة رواتب مسجَّلة بالفعل لنفس الشهر والسنة وجهة الصرف.'),
    ]

    @api.depends('month', 'year', 'disbursement_entity')
    def _compute_name(self):
        labels = dict(self._fields['disbursement_entity'].selection)
        for rec in self:
            rec.name = '%s/%s - %s' % (rec.month, rec.year, labels.get(rec.disbursement_entity, ''))

    @api.depends('payslip_ids')
    def _compute_payslip_count(self):
        for rec in self:
            rec.payslip_count = len(rec.payslip_ids)

    def action_compute_payslips(self):
        salary_model = self.env['demo_gov.hr.employee.salary']
        for rec in self:
            if rec.state not in ('draft', 'computed'):
                raise UserError(_('لا يمكن إعادة الحساب بعد اعتماد الدورة.'))
            salaries = salary_model.search([('disbursement_entity', '=', rec.disbursement_entity)])
            existing = {p.employee_id.id: p for p in rec.payslip_ids}
            for salary in salaries:
                payslip = existing.get(salary.employee_id.id)
                if not payslip:
                    payslip = self.env['demo_gov.hr.payroll.payslip'].create({
                        'run_id': rec.id,
                        'employee_id': salary.employee_id.id,
                        'salary_id': salary.id,
                    })
                payslip.action_compute()
            rec.state = 'computed'

    def action_submit_for_review(self):
        for rec in self:
            if rec.state != 'computed':
                raise UserError(_('لازم تحسب كشوف المرتبات أولاً قبل الإرسال للمراجعة.'))
        self.write({'state': 'under_review'})

    def action_approve(self):
        for rec in self:
            if rec.payslip_ids.filtered(lambda p: p.state != 'completed'):
                raise UserError(_('لا يمكن اعتماد الدورة وبها كشوف "غير مكتملة" لم تُراجَع.'))
        self.write({'state': 'approved'})

    def action_post(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('لازم تعتمد الدورة أولاً قبل الترحيل.'))
            for payslip in rec.payslip_ids:
                self.env['demo_gov.hr.payroll.disbursement.line'].create({
                    'employee_id': payslip.employee_id.id,
                    'month': int(rec.month),
                    'year': rec.year,
                    'disbursement_type': 'salary',
                    'gross_amount': payslip.gross_earnings,
                    'net_amount': payslip.net_salary,
                    'source_reference': rec.name,
                })
        self.write({'state': 'posted'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})


class HrPayrollPayslip(models.Model):
    _name = 'demo_gov.hr.payroll.payslip'
    _description = 'كشف مرتب موظف ضمن دورة شهرية — استمارة 132 ع.ح'
    _order = 'employee_id'

    run_id = fields.Many2one('demo_gov.hr.payroll.run', string='الدورة', required=True,
                              ondelete='cascade')
    month = fields.Selection(related='run_id.month', store=True, string='الشهر')
    year = fields.Char(related='run_id.year', store=True, string='السنة')
    disbursement_entity = fields.Selection(related='run_id.disbursement_entity', store=True,
                                            string='جهة الصرف')

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True)
    salary_id = fields.Many2one('demo_gov.hr.employee.salary', string='ملف المرتب', required=True)

    gross_earnings = fields.Float(string='إجمالي الاستحقاقات', readonly=True)
    manual_deductions = fields.Float(string='إجمالي الاستقطاعات اليدوية', readonly=True)
    transaction_adjustment = fields.Float(string='صافي التأثيرات الاستثنائية هذا الشهر',
                                           readonly=True)

    insurance_wage = fields.Float(string='أجر الاشتراك التأميني', readonly=True)
    employee_insurance_share = fields.Float(string='حصة الموظف - تأمينات', readonly=True)
    employer_insurance_share = fields.Float(string='حصة الجهة - تأمينات', readonly=True)

    annual_taxable_income = fields.Float(string='صافي الدخل السنوي الخاضع للضريبة', readonly=True)
    income_tax_monthly = fields.Float(string='ضريبة الدخل الشهرية', readonly=True)
    stamp_duty = fields.Float(string='ضريبة الدمغة النسبية', readonly=True)

    net_salary = fields.Float(string='صافي المرتب', readonly=True)
    previous_net_salary = fields.Float(string='المرتب الصافي عن الشهر السابق', readonly=True)

    reviewer_notes = fields.Text(string='ملاحظات المراجع')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('completed', 'مكتمل'),
        ('rejected', 'غير مكتمل'),
    ], default='draft', string='حالة المراجعة')

    def _find_previous_payslip(self):
        self.ensure_one()
        previous_period = date(int(self.year), int(self.month), 1) - relativedelta(months=1)
        return self.search([
            ('employee_id', '=', self.employee_id.id),
            ('month', '=', str(previous_period.month)),
            ('year', '=', str(previous_period.year)),
        ], limit=1)

    def action_compute(self):
        insurance_model = self.env['demo_gov.hr.payroll.insurance.bracket']
        tax_category_model = self.env['demo_gov.hr.payroll.tax.category']
        stamp_model = self.env['demo_gov.hr.payroll.stamp.bracket']
        tax_settings = self.env['demo_gov.hr.payroll.tax.settings'].get_settings()

        for rec in self:
            salary = rec.salary_id
            gross = salary.job_wage + salary.total_earnings
            manual_deductions = salary.total_deductions

            period_start = date(int(rec.year), int(rec.month), 1)
            period_end = period_start + relativedelta(months=1)
            transactions = self.env['demo_gov.hr.payroll.transaction'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'executed'),
                ('transaction_date', '>=', period_start),
                ('transaction_date', '<', period_end),
            ])
            transaction_adjustment = sum(transactions.mapped('amount'))

            insurance_wage = employee_share = employer_share = 0.0
            if salary.is_insurable:
                bracket = insurance_model.get_bracket_for_year(rec.year)
                if bracket:
                    result = bracket.compute_contributions(gross)
                    insurance_wage = result['insurable_wage']
                    employee_share = result['employee_share']
                    employer_share = result['employer_share']

            income_tax_monthly = 0.0
            annual_taxable_income = 0.0
            if salary.is_taxable:
                monthly_taxable = gross - employee_share
                annual_taxable_income = max(
                    0.0, (monthly_taxable * 12) - tax_settings.income_tax_exemption)
                category = tax_category_model.find_category_for_income(annual_taxable_income)
                if category:
                    income_tax_monthly = category.compute_tax(annual_taxable_income) / 12.0

            stamp_duty = stamp_model.compute_stamp_duty(gross, tax_settings.stamp_duty_exemption)

            net_salary = (gross - employee_share - income_tax_monthly - stamp_duty
                          - manual_deductions + transaction_adjustment)

            previous = rec._find_previous_payslip()

            rec.write({
                'gross_earnings': gross,
                'manual_deductions': manual_deductions,
                'transaction_adjustment': transaction_adjustment,
                'insurance_wage': insurance_wage,
                'employee_insurance_share': employee_share,
                'employer_insurance_share': employer_share,
                'annual_taxable_income': annual_taxable_income,
                'income_tax_monthly': income_tax_monthly,
                'stamp_duty': stamp_duty,
                'net_salary': net_salary,
                'previous_net_salary': previous.net_salary if previous else 0.0,
            })

    def action_mark_completed(self):
        self.write({'state': 'completed'})

    def action_mark_rejected(self):
        for rec in self:
            if not rec.reviewer_notes:
                raise UserError(_('لازم تسجّل ملاحظة المراجع عند رفض الكشف.'))
        self.write({'state': 'rejected'})
