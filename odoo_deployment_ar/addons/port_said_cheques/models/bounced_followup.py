# -*- coding: utf-8 -*-
"""
متابعة الشيكات المرتدة (Bounced Cheques Follow-up)
====================================================
يُنشأ تلقائياً عند إرجاع شيك (cheque.action_return).
يتتبع الإجراءات القانونية والإدارية لاسترداد المبلغ.

الحالات:
- open          : مفتوح للمتابعة
- negotiating   : تفاوض مع الطرف الآخر
- legal_action  : إحالة للنيابة/القضاء
- recovered     : استُرد المبلغ
- written_off   : شُطِب (مبلغ غير قابل للاسترداد)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BouncedFollowup(models.Model):
    _name = 'port_said.cheque.bounced_followup'
    _description = 'متابعة شيك مرتد'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'bounce_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)

    cheque_id = fields.Many2one('port_said.cheque', string='الشيك المرتد',
        required=True, ondelete='cascade', index=True)
    cheque_number = fields.Char(related='cheque_id.cheque_number', store=True)
    drawer_partner_id = fields.Many2one('res.partner',
        related='cheque_id.partner_id', store=True,
        string='مُصدر الشيك')
    drawn_on_bank = fields.Char(related='cheque_id.drawn_on_bank', store=True)

    # ── تفاصيل الارتداد ─────────────────────────────────────────────────────
    bounce_date = fields.Date(string='تاريخ الارتداد', required=True)
    bounce_reason = fields.Text(string='سبب الارتداد', required=True)
    original_amount = fields.Monetary(string='المبلغ الأصلي',
        currency_field='currency_id')
    returned_charges = fields.Monetary(string='رسوم الإرجاع من البنك',
        currency_field='currency_id',
        help='الرسوم التي يحمِّلها البنك على المحافظة لارتداد الشيك.')
    total_claim = fields.Monetary(string='إجمالي المطالبة',
        compute='_compute_total_claim', store=True,
        currency_field='currency_id',
        help='= المبلغ الأصلي + رسوم الإرجاع')

    # ── الإجراءات ───────────────────────────────────────────────────────────
    first_notice_date = fields.Date(string='تاريخ أول إنذار')
    second_notice_date = fields.Date(string='تاريخ الإنذار الثاني')
    legal_referral_date = fields.Date(string='تاريخ الإحالة للنيابة')
    case_number = fields.Char(string='رقم القضية')
    court_name = fields.Char(string='المحكمة')

    # ── الاسترداد ───────────────────────────────────────────────────────────
    amount_recovered = fields.Monetary(string='المبلغ المُسترَد',
        currency_field='currency_id')
    recovery_date = fields.Date(string='تاريخ الاسترداد')
    recovery_method = fields.Selection([
        ('cash',       'نقدية'),
        ('new_cheque', 'شيك جديد'),
        ('transfer',   'تحويل بنكي'),
        ('court_order','أمر محكمة'),
        ('settlement', 'تسوية ودية'),
    ], string='طريقة الاسترداد')

    # ── الشطب ────────────────────────────────────────────────────────────────
    write_off_date = fields.Date(string='تاريخ الشطب')
    write_off_reason = fields.Text(string='سبب الشطب')
    write_off_approved_by = fields.Many2one('res.users',
        string='اعتمد الشطب')

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('open',        'مفتوح'),
        ('negotiating', 'قيد التفاوض'),
        ('legal_action','إجراءات قانونية'),
        ('recovered',   'مُسترَد'),
        ('written_off', 'مشطوب'),
    ], string='الحالة', default='open', tracking=True, required=True)

    currency_id = fields.Many2one('res.currency',
        related='cheque_id.currency_id', store=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    notes = fields.Text(string='ملاحظات')

    @api.depends('cheque_id', 'cheque_id.cheque_number', 'cheque_id.amount')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = _('ارتداد شيك #%s — %s') % (
                rec.cheque_id.cheque_number or '?',
                rec.cheque_id.amount or 0,
            )

    @api.depends('original_amount', 'returned_charges')
    def _compute_total_claim(self):
        for rec in self:
            rec.total_claim = (rec.original_amount or 0) + (rec.returned_charges or 0)

    # ── Actions ──────────────────────────────────────────────────────────────
    def action_start_negotiation(self):
        for rec in self:
            if rec.state != 'open':
                raise UserError(_('الملف ليس في حالة "مفتوح".'))
            if not rec.first_notice_date:
                rec.first_notice_date = fields.Date.today()
            rec.state = 'negotiating'

    def action_refer_to_legal(self):
        for rec in self:
            if rec.state not in ('open', 'negotiating'):
                raise UserError(_(
                    'الإحالة القانونية متاحة للملفات المفتوحة أو قيد التفاوض فقط.'))
            rec.state = 'legal_action'
            rec.legal_referral_date = fields.Date.today()

    def action_mark_recovered(self):
        for rec in self:
            if not rec.amount_recovered:
                raise UserError(_('أدخل المبلغ المُسترَد أولاً.'))
            if not rec.recovery_method:
                raise UserError(_('أدخل طريقة الاسترداد.'))
            rec.state = 'recovered'
            rec.recovery_date = fields.Date.today()
            rec.message_post(body=_(
                'تم استرداد %s من إجمالي %s بطريقة: %s'
            ) % (rec.amount_recovered, rec.total_claim,
                 dict(self._fields['recovery_method'].selection).get(
                     rec.recovery_method)))

    def action_write_off(self):
        """شطب المبلغ — يتطلب صلاحية مدير."""
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('الشطب يتطلب صلاحية مدير حسابات.'))
        for rec in self:
            if not rec.write_off_reason:
                raise UserError(_('يجب إدخال سبب الشطب.'))
            rec.state = 'written_off'
            rec.write_off_date = fields.Date.today()
            rec.write_off_approved_by = self.env.user.id
            rec.message_post(body=_('شُطب المبلغ بواسطة %s. السبب: %s')
                              % (self.env.user.name, rec.write_off_reason))
