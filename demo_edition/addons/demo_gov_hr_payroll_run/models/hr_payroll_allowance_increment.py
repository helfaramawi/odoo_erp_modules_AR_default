# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

ALLOWANCE_TYPES = [
    ('periodic', 'علاوة دورية'),
    ('incentive', 'علاوة تشجيعية'),
    ('promotion', 'علاوة ترقية'),
]


class HrPayrollAllowanceIncrement(models.Model):
    _name = 'demo_gov.hr.payroll.allowance.increment'
    _description = 'حساب العلاوات والحوافز على الأجر الوظيفي — المتطلب الوظيفي 14'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='رقم الحركة', readonly=True, copy=False)
    salary_id = fields.Many2one('demo_gov.hr.employee.salary', string='ملف مرتب الموظف',
                                 required=True)
    employee_id = fields.Many2one(related='salary_id.employee_id', store=True, string='الموظف')
    allowance_type = fields.Selection(ALLOWANCE_TYPES, string='نوع العلاوة', required=True)
    percentage = fields.Float(string='النسبة %', required=True)

    wage_before = fields.Float(string='الأجر الوظيفي قبل العلاوة', readonly=True)
    computed_amount = fields.Float(string='مبلغ العلاوة', readonly=True)
    wage_after = fields.Float(string='الأجر الوظيفي بعد العلاوة', readonly=True)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('computed', 'محسوبة'),
        ('posted', 'مرحَّلة'),
    ], default='draft', string='الحالة', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.payroll.allowance.increment') or '/'
        return super().create(vals_list)

    def action_recompute(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_('لا يمكن إعادة حساب حركة مُرحَّلة بالفعل.'))
            wage_before = rec.salary_id.job_wage
            computed_amount = wage_before * rec.percentage / 100.0
            rec.write({
                'wage_before': wage_before,
                'computed_amount': computed_amount,
                'wage_after': wage_before + computed_amount,
                'state': 'computed',
            })

    def action_post(self):
        for rec in self:
            if rec.state != 'computed':
                raise UserError(_('لازم تحسب العلاوة أولاً قبل الترحيل.'))
            rec.salary_id.job_wage = rec.wage_after
        self.write({'state': 'posted'})
