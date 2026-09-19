# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrPayrollInsuranceBracket(models.Model):
    _name = 'demo_gov.hr.payroll.insurance.bracket'
    _description = 'حد أجر الاشتراك التأميني ونسب التوزيع لسنة محددة — المتطلب الوظيفي 1-2'
    _order = 'year desc'

    # الحد الأدنى/الأقصى ونسب الاشتراك يتغيرون كل عام في 1/1 وفقاً لقانون
    # التأمينات الاجتماعية — لازم الإدارة المالية تراجع وتحدّث هذه القيم
    # سنوياً قبل الاعتماد عليها في صرف فعلي.
    year = fields.Char(string='السنة', required=True)
    min_insurable_wage = fields.Float(string='الحد الأدنى لأجر الاشتراك')
    max_insurable_wage = fields.Float(string='الحد الأقصى لأجر الاشتراك')
    employee_contribution_pct = fields.Float(string='نسبة اشتراك المؤمَّن عليه %')
    employer_contribution_pct = fields.Float(string='نسبة اشتراك الجهة %')
    employee_debit_account_id = fields.Many2one('account.account',
                                                  string='حساب مدين - حصة الموظف')
    employee_credit_account_id = fields.Many2one('account.account',
                                                   string='حساب دائن - حصة الموظف')
    employer_debit_account_id = fields.Many2one('account.account',
                                                  string='حساب مدين - حصة الجهة')
    employer_credit_account_id = fields.Many2one('account.account',
                                                   string='حساب دائن - حصة الجهة')

    _sql_constraints = [
        ('unique_year', 'unique(year)', 'يوجد إعداد تأمينات مسجَّل بالفعل لهذه السنة.'),
    ]

    @api.model
    def get_bracket_for_year(self, year):
        return self.search([('year', '=', str(year))], limit=1)

    def compute_contributions(self, gross_wage):
        """يحسب أجر الاشتراك التأميني (بعد تطبيق الحد الأدنى/الأقصى) ثم حصتي
        الموظف والجهة عليه."""
        self.ensure_one()
        insurable_wage = gross_wage
        if self.min_insurable_wage:
            insurable_wage = max(insurable_wage, self.min_insurable_wage)
        if self.max_insurable_wage:
            insurable_wage = min(insurable_wage, self.max_insurable_wage)
        employee_share = insurable_wage * self.employee_contribution_pct / 100.0
        employer_share = insurable_wage * self.employer_contribution_pct / 100.0
        return {
            'insurable_wage': insurable_wage,
            'employee_share': employee_share,
            'employer_share': employer_share,
        }
