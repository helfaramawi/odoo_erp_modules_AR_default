# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

PAYOUT_REASONS = [
    ('marriage', 'زواج'),
    ('birth', 'مولود'),
    ('death', 'وفاة العضو'),
    ('retirement', 'التقاعد'),
]


class HrTakafulPayout(models.Model):
    _name = 'demo_gov.hr.takaful.payout'
    _description = 'طلب صرف مستحقات من صندوق التكافل — TakafulPayoutForm'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc'

    name = fields.Char(string='رقم الطلب', readonly=True, copy=False)
    member_id = fields.Many2one('demo_gov.hr.takaful.member', string='العضو', required=True,
                                 ondelete='cascade')
    payout_reason = fields.Selection(PAYOUT_REASONS, string='سبب الصرف', required=True)
    request_date = fields.Date(string='تاريخ الطلب', default=fields.Date.today, required=True)
    amount = fields.Float(string='المبلغ المستحق', readonly=True)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('approved', 'معتمَد من مسؤول التكافل'),
        ('paid', 'مصروف'),
    ], default='draft', string='الحالة', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.takaful.payout') or '/'
        return super().create(vals_list)

    def _get_retirement_multiplier(self, years):
        if years >= 20:
            return 1.5
        if years >= 10:
            return 1.25
        return 1.0

    def action_compute_amount(self):
        params = self.env['demo_gov.hr.takaful.parameters'].get_parameters()
        for rec in self:
            member = rec.member_id
            if member.member_status != 'active':
                raise UserError(_('لا يمكن صرف مستحقات لعضو غير نشط.'))
            if rec.payout_reason == 'marriage':
                amount = params.marriage_payout
            elif rec.payout_reason == 'birth':
                amount = params.birth_payout
            elif rec.payout_reason == 'death':
                amount = params.death_payout
            elif rec.payout_reason == 'retirement':
                multiplier = rec._get_retirement_multiplier(member.years_of_membership())
                amount = member.total_contributions * multiplier
            else:
                amount = 0.0
            rec.amount = amount

    def action_approve(self):
        for rec in self:
            if not rec.amount:
                raise UserError(_('لازم تحسب المبلغ المستحق أولاً.'))
        self.write({'state': 'approved'})

    def action_pay(self):
        # الصرف لا يتم بدون موافقة مسؤول التكافل (حسب وثيقة التصميم) —
        # ولا يُنشئ قيد يومية محاسبي فعلي في هذا الإصدار التجريبي.
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('لازم يعتمد مسؤول التكافل الطلب أولاً قبل الصرف.'))
            rec.member_id.total_payouts += rec.amount
        self.write({'state': 'paid'})
