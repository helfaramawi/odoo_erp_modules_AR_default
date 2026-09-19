# -*- coding: utf-8 -*-
from odoo import models, fields


class HrPayrollComponent(models.Model):
    _name = 'demo_gov.hr.payroll.component'
    _description = 'بند من بنود الراتب — استحقاق أو استقطاع'
    _order = 'sequence, id'

    name = fields.Char(string='اسم البند', required=True)
    code = fields.Char(string='الكود', required=True)
    sequence = fields.Integer(string='الترتيب', default=10)
    component_type = fields.Selection([
        ('earning', 'استحقاق'),
        ('deduction', 'استقطاع'),
    ], string='النوع', required=True)
    computation_method = fields.Selection([
        ('fixed', 'مبلغ ثابت'),
        ('pct_basic', 'نسبة من الأجر الأساسي'),
        ('pct_job_wage', 'نسبة من الأجر الوظيفي'),
    ], string='طريقة الاحتساب', default='fixed', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'هذا الكود مستخدم بالفعل لبند آخر.'),
    ]
