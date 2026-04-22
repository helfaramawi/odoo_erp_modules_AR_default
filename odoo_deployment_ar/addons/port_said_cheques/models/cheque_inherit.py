# -*- coding: utf-8 -*-
"""
تمديد نموذج الشيك (Cheque Inherit)
====================================
يضيف لنموذج port_said.cheque الأساسي:
1. ربط بدفتر شيكات ورقي (cheque_book_id) + validation
2. حقول الإيداع للتحصيل (collection fee, collection account)
3. حقول متابعة الشيكات المرتدة
4. ربط بأمر دفع مرسل (outgoing_po_id)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ChequeInherit(models.Model):
    _inherit = 'port_said.cheque'

    # ── الربط بالدفتر الورقي ────────────────────────────────────────────────
    cheque_book_id = fields.Many2one('port_said.cheque.book',
        string='دفتر الشيكات الورقي',
        help='الدفتر المسبق الطباعة الذي صدر منه هذا الشيك. '
             'مطلوب للشيكات الصادرة.',
        domain="[('state', '=', 'in_use')]")

    # ── التصنيف التفصيلي ───────────────────────────────────────────────────
    cheque_category = fields.Selection([
        ('standard_out', 'صادر عادي'),
        ('standard_in',  'وارد عادي'),
        ('for_collection', 'وارد للتحصيل (رسم تحصيل)'),
        ('certified',    'مُعتمَد (Certified)'),
        ('bank_draft',   'حوالة بنكية'),
    ], string='تصنيف الشيك', default='standard_out',
        help='التصنيف القانوني. "للتحصيل" يظهر في دفتر 78 شيكات رسم التحصيل.')

    # ── حقول التحصيل (Form 78) ──────────────────────────────────────────────
    collection_fee = fields.Monetary(string='رسم التحصيل',
        currency_field='currency_id',
        help='الرسم الذي يحصله البنك مقابل تحصيل الشيك.')
    net_collected = fields.Monetary(string='صافي المحصَّل',
        compute='_compute_net_collected', store=True,
        currency_field='currency_id',
        help='= المبلغ الأصلي - رسم التحصيل')
    collection_account_id = fields.Many2one('account.account',
        string='حساب رسوم التحصيل',
        help='الحساب الذي يُقيَّد عليه رسم التحصيل كمصروف.')

    # ── متابعة الشيكات المرتدة ─────────────────────────────────────────────
    bounce_followup_id = fields.Many2one('port_said.cheque.bounced_followup',
        string='ملف الارتداد')

    # ── الربط بأمر الدفع المرسل ────────────────────────────────────────────
    outgoing_po_id = fields.Many2one('port_said.outgoing_po',
        string='أمر الدفع المرسل',
        help='ربط بأمر الدفع المرسل الذي صُرف بهذا الشيك.')

    # ── التسلسل القانوني لدفتر 56 ──────────────────────────────────────────
    form56_sequence = fields.Char(string='تسلسل دفتر 56',
        readonly=True, copy=False, index=True,
        help='رقم متسلسل قانوني داخل دفتر الشيكات القانوني 56 ع.ح.')

    # ── الحسابات ─────────────────────────────────────────────────────────────
    @api.depends('amount', 'collection_fee')
    def _compute_net_collected(self):
        for rec in self:
            rec.net_collected = (rec.amount or 0) - (rec.collection_fee or 0)

    # ── Validation: رقم الشيك ضمن نطاق الدفتر ────────────────────────────────
    @api.constrains('cheque_number', 'cheque_book_id', 'direction')
    def _check_cheque_in_book_range(self):
        for rec in self:
            # فقط للشيكات الصادرة (outgoing) يجب أن تكون ضمن دفتر
            if rec.direction != 'outgoing':
                continue
            if not rec.cheque_book_id:
                # مسموح في draft فقط، سنفحصه عند action_issue
                continue
            if not rec.cheque_book_id._is_number_in_range(rec.cheque_number):
                raise ValidationError(_(
                    'رقم الشيك %s خارج نطاق دفتر الشيكات %s (%d – %d).'
                ) % (rec.cheque_number, rec.cheque_book_id.book_reference,
                     rec.cheque_book_id.first_cheque_number,
                     rec.cheque_book_id.last_cheque_number))

    @api.constrains('cheque_number', 'cheque_book_id', 'direction', 'drawn_on_bank')
    def _check_no_duplicate_in_book(self):
        """يمنع إصدار شيكين بنفس الرقم من نفس الدفتر."""
        for rec in self:
            if rec.direction != 'outgoing' or not rec.cheque_book_id:
                continue
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('cheque_book_id', '=', rec.cheque_book_id.id),
                ('cheque_number', '=', rec.cheque_number),
                ('state', '!=', 'cancelled'),
            ])
            if duplicate:
                raise ValidationError(_(
                    'رقم الشيك %s مكرر في نفس الدفتر %s.'
                ) % (rec.cheque_number, rec.cheque_book_id.book_reference))

    # ── Override action_issue: فرض ربط الدفتر + تسلسل Form 56 ───────────────
    def action_issue(self):
        for rec in self:
            # قبل الإصدار: الشيك الصادر يجب أن يكون مربوطاً بدفتر ورقي
            if rec.direction == 'outgoing' and not rec.cheque_book_id:
                raise UserError(_(
                    'الشيك الصادر يجب أن يكون مربوطاً بدفتر شيكات ورقي قبل الإصدار.'))
        # استدعِ super أولاً. إذا فشل، لن يُستهلَك رقم التسلسل القانوني.
        result = super().action_issue()
        # الآن نُولِّد التسلسل — super نجح والحالة فعلياً تغيَّرت
        Seq = self.env['ir.sequence']
        for rec in self:
            if not rec.form56_sequence:
                if rec.direction == 'outgoing':
                    rec.form56_sequence = Seq.next_by_code(
                        'port_said.cheque.form56.out') or '/'
                elif rec.cheque_category == 'for_collection':
                    rec.form56_sequence = Seq.next_by_code(
                        'port_said.cheque.form78.collection') or '/'
        return result

    # ── Override action_return: يفتح ملف ارتداد تلقائياً ───────────────────
    def action_return(self):
        result = super().action_return()
        # أنشئ ملف متابعة إن لم يكن موجوداً
        for rec in self:
            if not rec.bounce_followup_id:
                followup = self.env['port_said.cheque.bounced_followup'].create({
                    'cheque_id': rec.id,
                    'bounce_date': rec.return_date or fields.Date.today(),
                    'bounce_reason': rec.return_reason,
                    'original_amount': rec.amount,
                })
                rec.bounce_followup_id = followup.id
        return result
