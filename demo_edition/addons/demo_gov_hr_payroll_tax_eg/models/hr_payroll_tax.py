# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrPayrollTaxCategory(models.Model):
    _name = 'demo_gov.hr.payroll.tax.category'
    _description = 'فئة ضريبة الدخل التصاعدية — المتطلب الوظيفي 3-2 (6 فئات)'
    _order = 'income_from'

    name = fields.Char(string='اسم الفئة', required=True)
    income_from = fields.Float(string='الدخل السنوي أكبر من')
    income_to = fields.Float(string='الدخل السنوي إلى')
    bracket_ids = fields.One2many('demo_gov.hr.payroll.tax.bracket', 'category_id',
                                   string='الشرائح الضريبية للفئة')

    def compute_tax(self, annual_taxable_income):
        """تطبيق شرائح الفئة تصاعدياً على الدخل السنوي الخاضع للضريبة."""
        self.ensure_one()
        tax = 0.0
        for bracket in self.bracket_ids.sorted('income_from'):
            if annual_taxable_income <= bracket.income_from:
                continue
            upper = bracket.income_to if bracket.income_to else annual_taxable_income
            slice_amount = min(annual_taxable_income, upper) - bracket.income_from
            if slice_amount > 0:
                tax += slice_amount * bracket.rate
        return tax

    @api.model
    def find_category_for_income(self, annual_taxable_income):
        return self.search([
            ('income_from', '<=', annual_taxable_income),
            '|', ('income_to', '>=', annual_taxable_income), ('income_to', '=', 0),
        ], limit=1, order='income_from desc')


class HrPayrollTaxBracket(models.Model):
    _name = 'demo_gov.hr.payroll.tax.bracket'
    _description = 'شريحة ضريبية داخل فئة دخل'
    _order = 'income_from'

    category_id = fields.Many2one('demo_gov.hr.payroll.tax.category', string='الفئة',
                                   required=True, ondelete='cascade')
    income_from = fields.Float(string='أكبر من')
    income_to = fields.Float(string='إلى (0 = بلا حد أقصى)')
    rate = fields.Float(string='النسبة')


class HrPayrollStampBracket(models.Model):
    _name = 'demo_gov.hr.payroll.stamp.bracket'
    _description = 'شريحة ضريبة الدمغة النسبية — المتطلب الوظيفي 2-2'
    _order = 'income_from'

    income_from = fields.Float(string='أكبر من')
    income_to = fields.Float(string='إلى (0 = بلا حد أقصى)')
    rate = fields.Float(string='النسبة')

    @api.model
    def compute_stamp_duty(self, amount, exemption=0.0):
        taxable = max(0.0, amount - exemption)
        if not taxable:
            return 0.0
        bracket = self.search([
            ('income_from', '<=', taxable),
            '|', ('income_to', '>=', taxable), ('income_to', '=', 0),
        ], limit=1, order='income_from desc')
        return taxable * bracket.rate if bracket else 0.0


class HrPayrollTaxSettings(models.Model):
    _name = 'demo_gov.hr.payroll.tax.settings'
    _description = 'إعدادات ضرائب الرواتب العامة — المتطلب الوظيفي 3-2/4-2/5-2'

    name = fields.Char(string='الاسم', default='الإعدادات الضريبية العامة', readonly=True)
    income_tax_exemption = fields.Float(string='مبلغ الإعفاء من ضريبة الدخل (سنوي)')
    disability_additional_exemption = fields.Float(string='إعفاء إضافي لأصحاب الهمم')
    stamp_duty_exemption = fields.Float(string='مبلغ الإعفاء من ضريبة الدمغة النسبية')
    flat_tax_rate_non_employees = fields.Float(
        string='نسبة الضريبة المقطوعة على مكافآت غير العاملين')
    non_commercial_professions_tax_rate = fields.Float(
        string='نسبة ضريبة المهن غير التجارية (أتعاب خبرة)')

    @api.model
    def get_settings(self):
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({})
        return settings
