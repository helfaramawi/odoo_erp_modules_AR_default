# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPayrollReward(models.Model):
    _name = 'demo_gov.hr.payroll.reward'
    _description = 'حساب مكافآت الموظفين — المتطلب الوظيفي 12، ترحيلها لدفتر 129 سايرة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string='رقم المكافأة', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    reward_reason = fields.Char(string='سبب المكافأة')
    date = fields.Date(string='تاريخ الصرف', default=fields.Date.today, required=True)
    amount = fields.Float(string='قيمة المكافأة', required=True)
    insurance_deduction = fields.Float(string='خصم التأمينات')
    tax_deduction = fields.Float(string='خصم الضرائب')
    net_amount = fields.Float(compute='_compute_net_amount', store=True, string='صافي المكافأة')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('posted', 'مرحَّلة لدفتر 129 سايرة'),
    ], default='draft', string='الحالة', tracking=True)

    @api.depends('amount', 'insurance_deduction', 'tax_deduction')
    def _compute_net_amount(self):
        for rec in self:
            rec.net_amount = rec.amount - rec.insurance_deduction - rec.tax_deduction

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.payroll.reward') or '/'
        return super().create(vals_list)

    def action_post(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_('المكافأة مُرحَّلة بالفعل.'))
            self.env['demo_gov.hr.payroll.disbursement.line'].create({
                'employee_id': rec.employee_id.id,
                'month': rec.date.month,
                'year': str(rec.date.year),
                'disbursement_type': 'reward',
                'gross_amount': rec.amount,
                'net_amount': rec.net_amount,
                'source_reference': rec.name,
            })
        self.write({'state': 'posted'})
