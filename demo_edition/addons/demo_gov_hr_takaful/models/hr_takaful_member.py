# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrTakafulMember(models.Model):
    _name = 'demo_gov.hr.takaful.member'
    _description = 'عضو صندوق التكافل — TakafulMember'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True,
                                     string='الإدارة')
    member_status = fields.Selection([
        ('active', 'نشط'),
        ('suspended', 'موقف'),
        ('ended', 'منتهٍ'),
    ], default='active', string='حالة العضوية', tracking=True)
    enrollment_date = fields.Date(string='تاريخ الاشتراك', default=fields.Date.today, required=True)
    end_date = fields.Date(string='تاريخ انتهاء العضوية')

    monthly_contribution = fields.Float(string='الاشتراك الشهري', required=True)
    total_contributions = fields.Float(string='إجمالي الاشتراكات المدفوعة', readonly=True)
    total_payouts = fields.Float(string='إجمالي المصروف للعضو', readonly=True)
    fund_balance = fields.Float(compute='_compute_fund_balance', string='رصيد العضو')

    contribution_ids = fields.One2many('demo_gov.hr.takaful.contribution', 'member_id',
                                        string='الاشتراكات')
    payout_ids = fields.One2many('demo_gov.hr.takaful.payout', 'member_id', string='المصروفات')

    _sql_constraints = [
        ('unique_employee', 'unique(employee_id)',
         'هذا الموظف مسجَّل بالفعل كعضو في صندوق التكافل.'),
    ]

    @api.depends('total_contributions', 'total_payouts')
    def _compute_fund_balance(self):
        for rec in self:
            rec.fund_balance = rec.total_contributions - rec.total_payouts

    def years_of_membership(self):
        self.ensure_one()
        if not self.enrollment_date:
            return 0
        delta = fields.Date.today() - self.enrollment_date
        return delta.days // 365
