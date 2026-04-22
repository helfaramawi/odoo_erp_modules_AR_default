# -*- coding: utf-8 -*-
"""
أوامر الدفع المرسلة (Outgoing Payment Orders)
===============================================
دفتر حساب أوامر الدفع المرسلة - استمارة 56 ع.ح.

التكامل مع port_said.daftar55:
- كل أمر دفع مرسل يُنشأ عادةً من قيد صرف (Daftar 55) معتمَد ومُسمَّح
- أمر الدفع المرسل يُعبِّر عن الخطوة التنفيذية: إرسال التعليمات للبنك
  لتحويل الأموال إلى المستفيد

الفارق عن port_said.payment_order (من cash_books):
- تلك واردة (من الخزانة إلى المحافظة)
- هذه مرسلة (من المحافظة إلى المستفيدين)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class OutgoingPaymentOrder(models.Model):
    _name = 'port_said.outgoing_po'
    _description = 'أمر دفع مرسل'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, sequence_number desc'
    _rec_name = 'display_name'

    # ── الترقيم القانوني ─────────────────────────────────────────────────────
    sequence_number = fields.Char(
        string='رقم مسلسل بالدفتر', readonly=True, copy=False, index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    po_number = fields.Char(string='رقم أمر الدفع', required=True, index=True,
        help='الرقم الرسمي المُصدَر للأمر.')

    # ── المستفيد ────────────────────────────────────────────────────────────
    beneficiary_id = fields.Many2one('res.partner', string='المستفيد',
        required=True)
    beneficiary_account = fields.Char(string='رقم حساب المستفيد')
    beneficiary_bank = fields.Char(string='بنك المستفيد')
    beneficiary_iban = fields.Char(string='IBAN المستفيد')

    # ── المبالغ ──────────────────────────────────────────────────────────────
    amount = fields.Monetary(string='المبلغ', required=True,
        currency_field='currency_id')
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── التواريخ ─────────────────────────────────────────────────────────────
    issue_date = fields.Date(string='تاريخ الإصدار', required=True,
        default=fields.Date.today)
    sent_date = fields.Date(string='تاريخ الإرسال للبنك')
    cleared_date = fields.Date(string='تاريخ تأكيد التنفيذ')

    # ── آلية الدفع ──────────────────────────────────────────────────────────
    payment_method = fields.Selection([
        ('cheque',        'شيك'),
        ('bank_transfer', 'تحويل بنكي'),
        ('swift',         'تحويل دولي (SWIFT)'),
    ], string='آلية الدفع', required=True, default='bank_transfer')
    cheque_id = fields.Many2one('port_said.cheque',
        string='الشيك الصادر',
        domain="[('direction', '=', 'outgoing')]",
        help='للشيكات الصادرة فقط.')

    # ── الربط مع دفتر 55 ───────────────────────────────────────────────────
    daftar55_id = fields.Many2one('port_said.daftar55',
        string='قيد دفتر 55',
        help='قيد الصرف الأساسي الذي نتج عنه أمر الدفع هذا.')
    daftar55_sequence = fields.Char(
        string='رقم مسلسل 55', related='daftar55_id.sequence_number',
        store=True, readonly=True)

    # ── الغرض والميزانية ────────────────────────────────────────────────────
    purpose = fields.Text(string='الغرض', required=True)
    budget_line = fields.Char(string='بند الموازنة',
        help='تنسيق: 2/01/03 — يُستخدم في التقارير.')

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',     'مسودة'),
        ('registered','مُقيَّد بالدفتر'),
        ('sent',      'مُرسَل للبنك'),
        ('cleared',   'مُنفَّذ'),
        ('rejected',  'مرفوض'),
        ('cancelled', 'مُلغى'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    rejection_reason = fields.Text(string='سبب الرفض')

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', readonly=True, copy=False)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('po_number_uniq',
         'UNIQUE(po_number, company_id)',
         'رقم أمر الدفع مكرر.'),
    ]

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('sequence_number', 'po_number', 'amount', 'beneficiary_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s — %s — %s' % (
                rec.sequence_number or '—',
                rec.beneficiary_id.name or '?',
                rec.amount or 0,
            )

    # ── Constraints ──────────────────────────────────────────────────────────
    @api.constrains('amount')
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('مبلغ أمر الدفع يجب أن يكون موجباً.'))

    @api.constrains('payment_method', 'cheque_id')
    def _check_cheque_consistency(self):
        for rec in self:
            if rec.payment_method == 'cheque' and not rec.cheque_id:
                raise ValidationError(_(
                    'آلية الدفع = شيك لكن لم يُحدَّد الشيك.'))
            if rec.payment_method != 'cheque' and rec.cheque_id:
                raise ValidationError(_(
                    'تم تحديد شيك لكن آلية الدفع ليست شيكاً.'))

    @api.constrains('cheque_id', 'amount')
    def _check_cheque_amount_matches(self):
        for rec in self:
            if rec.cheque_id and abs(rec.cheque_id.amount - rec.amount) > 0.01:
                raise ValidationError(_(
                    'مبلغ الشيك (%s) لا يطابق مبلغ أمر الدفع (%s).'
                ) % (rec.cheque_id.amount, rec.amount))

    # ── Lifecycle ────────────────────────────────────────────────────────────
    def action_register(self):
        Seq = self.env['ir.sequence']
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('أمر الدفع ليس في حالة مسودة.'))
            if not rec.sequence_number:
                rec.sequence_number = Seq.next_by_code(
                    'port_said.outgoing_po') or '/'
            # السنة المالية
            if rec.issue_date and not rec.fiscal_year:
                m, y = rec.issue_date.month, rec.issue_date.year
                if m >= 7:
                    rec.fiscal_year = '%d/%d' % (y, y + 1)
                else:
                    rec.fiscal_year = '%d/%d' % (y - 1, y)
            rec.state = 'registered'

    def action_send(self):
        for rec in self:
            if rec.state != 'registered':
                raise UserError(_('يجب قيد أمر الدفع بالدفتر أولاً.'))
            # إن كان بشيك، الشيك يجب أن يكون على الأقل issued
            if rec.payment_method == 'cheque' and rec.cheque_id.state == 'draft':
                raise UserError(_(
                    'الشيك المرتبط ما زال في حالة مسودة. '
                    'أصدر الشيك قبل إرسال أمر الدفع.'))
            rec.state = 'sent'
            rec.sent_date = fields.Date.today()

    def action_clear(self):
        for rec in self:
            if rec.state != 'sent':
                raise UserError(_('يجب إرسال أمر الدفع للبنك أولاً.'))
            rec.state = 'cleared'
            rec.cleared_date = fields.Date.today()

    def action_reject(self):
        for rec in self:
            if rec.state not in ('sent',):
                raise UserError(_(
                    'الرفض متاح فقط لأوامر الدفع المُرسَلة.'))
            if not rec.rejection_reason:
                raise UserError(_('يجب تسجيل سبب الرفض.'))
            rec.state = 'rejected'
            rec.message_post(body=_('رُفض أمر الدفع. السبب: %s')
                              % rec.rejection_reason)

    def action_cancel(self):
        for rec in self:
            if rec.state == 'cleared':
                raise UserError(_(
                    'لا يمكن إلغاء أمر دفع مُنفَّذ. استخدم قيد تسوية عكسي.'))
            rec.state = 'cancelled'
