# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPayrollNonEmployeeReward(models.Model):
    _name = 'demo_gov.hr.payroll.non.employee.reward'
    _description = 'مكافآت غير العاملين (أتعاب خبرة) — المتطلب الوظيفي 13'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string='رقم المكافأة', readonly=True, copy=False)
    beneficiary_name = fields.Char(string='اسم المستفيد', required=True)
    national_id = fields.Char(string='الرقم القومي', size=14)
    reward_code = fields.Char(string='كود المكافأة')
    date = fields.Date(string='تاريخ الصرف', default=fields.Date.today, required=True)
    amount = fields.Float(string='قيمة المكافأة', required=True)

    tax_deduction = fields.Float(compute='_compute_deductions', store=True,
                                  string='خصم الضريبة المقطوعة')
    net_amount = fields.Float(compute='_compute_deductions', store=True,
                               string='صافي المكافأة')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('confirmed', 'معتمَدة'),
    ], default='draft', string='الحالة', tracking=True)

    @api.depends('amount')
    def _compute_deductions(self):
        settings = self.env['demo_gov.hr.payroll.tax.settings'].get_settings()
        for rec in self:
            rec.tax_deduction = rec.amount * settings.flat_tax_rate_non_employees / 100.0
            rec.net_amount = rec.amount - rec.tax_deduction

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.payroll.non.employee.reward') or '/'
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            if rec.state == 'confirmed':
                raise UserError(_('المكافأة معتمَدة بالفعل.'))
        self.write({'state': 'confirmed'})
