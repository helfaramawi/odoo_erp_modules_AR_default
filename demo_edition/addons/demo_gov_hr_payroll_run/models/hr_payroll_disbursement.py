# -*- coding: utf-8 -*-
from odoo import models, fields


class HrPayrollDisbursementLine(models.Model):
    _name = 'demo_gov.hr.payroll.disbursement.line'
    _description = 'دفتر 129 سايرة — سجل صرف المرتب أو المكافأة لكل موظف في كل شهر (المتطلب الوظيفي 15)'
    _order = 'year desc, month desc'

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, index=True)
    month = fields.Integer(string='الشهر', required=True)
    year = fields.Char(string='السنة', required=True)
    disbursement_type = fields.Selection([
        ('salary', 'مرتب'),
        ('reward', 'مكافأة'),
    ], string='النوع', required=True)
    gross_amount = fields.Float(string='المبلغ الإجمالي')
    net_amount = fields.Float(string='الصافي')
    source_reference = fields.Char(string='المرجع')
