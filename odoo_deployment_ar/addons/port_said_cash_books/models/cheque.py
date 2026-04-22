# -*- coding: utf-8 -*-
"""
نموذج الشيك الأساسي (Cheque Base Model)
========================================
نموذج خفيف يتتبع دورة حياة الشيك الواحد:
issued → endorsed → deposited → cleared → (returned)

يُستخدَم هنا من دفتر أوامر الدفع الواردة (كل PO وارد غالباً بشيك).
سيمدَّد في C-FM-12 port_said_cheques لإضافة دفتر 56 القانوني الخاص بالشيكات.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Cheque(models.Model):
    _name = 'port_said.cheque'
    _description = 'شيك'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, cheque_number desc'
    _rec_name = 'display_name'

    # ── الهوية ───────────────────────────────────────────────────────────────
    cheque_number = fields.Char(string='رقم الشيك', required=True, index=True,
                                 help='الرقم المطبوع على دفتر الشيكات')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ── الاتجاه ──────────────────────────────────────────────────────────────
    direction = fields.Selection([
        ('incoming', 'وارد (استُلم لصالحنا)'),
        ('outgoing', 'صادر (حرَّرناه لطرف آخر)'),
    ], string='الاتجاه', required=True, index=True)

    # ── الأطراف ─────────────────────────────────────────────────────────────
    partner_id = fields.Many2one('res.partner', string='الطرف الآخر',
                                  required=True,
                                  help='مُصدر الشيك الوارد، أو المستفيد من الشيك الصادر.')
    drawn_on_bank = fields.Char(string='مسحوب على بنك', required=True)
    drawer_account = fields.Char(string='رقم حساب مُصدر الشيك')

    # ── القيم ────────────────────────────────────────────────────────────────
    amount = fields.Monetary(string='المبلغ', required=True,
                              currency_field='currency_id')
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── التواريخ ─────────────────────────────────────────────────────────────
    issue_date = fields.Date(string='تاريخ الإصدار', required=True,
                              default=fields.Date.today)
    received_date = fields.Date(string='تاريخ الاستلام / التسليم')
    deposit_date = fields.Date(string='تاريخ الإيداع')
    clearing_date = fields.Date(string='تاريخ المقاصة')
    return_date = fields.Date(string='تاريخ الإرتداد')

    # ── دورة الحياة ──────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',     'مسودة'),
        ('issued',    'مُصدَر'),
        ('endorsed',  'مُظهَّر (للتحصيل)'),
        ('deposited', 'مودَع'),
        ('cleared',   'محصَّل'),
        ('returned',  'مرتد'),
        ('cancelled', 'مُلغى'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    return_reason = fields.Text(string='سبب الارتداد')

    # ── ربط محاسبي ───────────────────────────────────────────────────────────
    move_id = fields.Many2one('account.move', string='القيد المحاسبي',
                               help='القيد المرتبط بإيداع/تحصيل هذا الشيك.')
    payment_id = fields.Many2one('account.payment', string='الدفعة المرتبطة')
    statement_line_id = fields.Many2one('account.bank.statement.line',
                                         string='سطر كشف الحساب')

    # ── مرجعية اختيارية ─────────────────────────────────────────────────────
    daftar55_id = fields.Many2one('port_said.daftar55',
        string='مرجع دفتر 55',
        help='لو الشيك صرف على أمر دفع (صادر)')
    payment_order_id = fields.Many2one('port_said.payment_order',
        string='أمر الدفع الوارد',
        help='لو الشيك مقابل أمر دفع وارد')

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('cheque_number_uniq',
         'UNIQUE(cheque_number, drawn_on_bank, direction, company_id)',
         'رقم الشيك مكرر على نفس البنك والاتجاه.'),
    ]

    @api.depends('cheque_number', 'drawn_on_bank', 'amount', 'partner_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '#%s — %s — %s' % (
                rec.cheque_number or '?',
                rec.partner_id.name or '—',
                rec.amount or 0,
            )

    @api.constrains('amount')
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('مبلغ الشيك يجب أن يكون موجباً.'))

    # ── دورة الحياة ──────────────────────────────────────────────────────────
    def action_issue(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الشيك ليس في حالة مسودة.'))
            rec.state = 'issued'

    def action_endorse(self):
        for rec in self:
            if rec.direction != 'incoming':
                raise UserError(_('التظهير للتحصيل للشيكات الواردة فقط.'))
            if rec.state != 'issued':
                raise UserError(_('الشيك يجب أن يكون مُصدَراً.'))
            rec.state = 'endorsed'

    def action_deposit(self):
        for rec in self:
            if rec.direction != 'incoming':
                raise UserError(_('الإيداع للشيكات الواردة فقط.'))
            if rec.state not in ('issued', 'endorsed'):
                raise UserError(_('الشيك ليس مُصدَراً أو مُظهَّراً.'))
            rec.state = 'deposited'
            rec.deposit_date = fields.Date.today()

    def action_clear(self):
        for rec in self:
            if rec.state != 'deposited' and rec.direction == 'incoming':
                raise UserError(_('الشيك الوارد يجب إيداعه أولاً.'))
            if rec.state not in ('issued', 'deposited'):
                raise UserError(_('الشيك ليس جاهزاً للمقاصة.'))
            rec.state = 'cleared'
            rec.clearing_date = fields.Date.today()

    def action_return(self):
        for rec in self:
            if rec.state == 'cleared':
                raise UserError(_('الشيك محصَّل بالفعل، لا يمكن إرجاعه.'))
            if not rec.return_reason:
                raise UserError(_('يجب تسجيل سبب الارتداد.'))
            rec.state = 'returned'
            rec.return_date = fields.Date.today()

    def action_cancel(self):
        for rec in self:
            if rec.state in ('cleared',):
                raise UserError(_('لا يمكن إلغاء شيك محصَّل.'))
            rec.state = 'cancelled'
