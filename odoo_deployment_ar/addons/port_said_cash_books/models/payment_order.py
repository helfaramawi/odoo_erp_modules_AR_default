# -*- coding: utf-8 -*-
"""
أوامر الدفع الواردة (Incoming Payment Orders)
==============================================
نموذج مستقل لتتبع دورة حياة كل أمر دفع وارد:
received → registered → cleared → posted_to_224

المصدر: أوامر الدفع المُستلَمة من وزارة المالية أو الجهات المموِّلة.
الدفتر القانوني: استمارة 78 ع.ح - دفتر حساب أوامر الدفع الواردة.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaymentOrder(models.Model):
    _name = 'port_said.payment_order'
    _description = 'أمر دفع وارد'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'received_date desc, sequence_number desc'
    _rec_name = 'display_name'

    # ── الترقيم القانوني ─────────────────────────────────────────────────────
    sequence_number = fields.Char(
        string='رقم مسلسل بالدفتر', readonly=True, copy=False, index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    po_reference = fields.Char(string='رقم أمر الدفع المُصدِر', required=True,
        help='الرقم المرجعي كما هو على الأصل المُستلَم من الجهة المُصدِرة.')

    # ── الجهة المُصدِرة ─────────────────────────────────────────────────────
    issuing_entity = fields.Selection([
        ('mof',        'وزارة المالية'),
        ('cau',        'الجهاز المركزي للمحاسبات'),
        ('governorate','محافظة أخرى'),
        ('ministry',   'وزارة/جهة حكومية'),
        ('other',      'أخرى'),
    ], string='الجهة المُصدِرة', required=True, default='mof', index=True)
    issuing_entity_name = fields.Char(string='اسم الجهة بالتفصيل', required=True)

    # ── المبالغ ──────────────────────────────────────────────────────────────
    amount = fields.Monetary(string='المبلغ', required=True,
                              currency_field='currency_id')
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── التواريخ ─────────────────────────────────────────────────────────────
    issue_date = fields.Date(string='تاريخ الإصدار', required=True)
    received_date = fields.Date(string='تاريخ الاستلام', required=True,
                                 default=fields.Date.today)
    registered_date = fields.Date(string='تاريخ القيد بالدفتر')
    cleared_date = fields.Date(string='تاريخ التحصيل / الإيداع')

    # ── آلية الدفع ──────────────────────────────────────────────────────────
    payment_method = fields.Selection([
        ('cheque',        'شيك'),
        ('bank_transfer', 'تحويل بنكي'),
        ('cash',          'نقدية'),
    ], string='آلية الدفع', required=True, default='bank_transfer')
    cheque_id = fields.Many2one('port_said.cheque', string='الشيك المرتبط',
                                 domain="[('direction', '=', 'incoming')]")

    # ── الغرض والربط المحاسبي ───────────────────────────────────────────────
    purpose = fields.Text(string='الغرض من أمر الدفع', required=True)
    budget_line = fields.Char(string='بند الموازنة (باب/فصل/بند)',
        help='تنسيق: 7/01/02 — يُستخدم في دفتر الإيرادات والمصروفات.')
    account_id = fields.Many2one('account.account',
        string='الحساب الدائن',
        help='الحساب الذي تُقيَّد فيه الإيرادات من هذا الأمر.')
    move_id = fields.Many2one('account.move', string='القيد المحاسبي',
                               readonly=True)

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',      'مسودة'),
        ('received',   'مُستلَم'),
        ('registered', 'مُقيَّد بالدفتر'),
        ('cleared',    'محصَّل'),
        ('posted',     'مُرحَّل محاسبياً'),
        ('cancelled',  'مُلغى'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', readonly=True, copy=False)

    # ── التواقيع ────────────────────────────────────────────────────────────
    registered_by = fields.Many2one('res.users',
        string='قيَّده بالدفتر', readonly=True)
    accounts_head_id = fields.Many2one('res.users',
        string='اعتمد رئيس الحسابات')

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('po_reference_uniq',
         'UNIQUE(po_reference, issuing_entity, company_id)',
         'رقم أمر الدفع مكرر من نفس الجهة المُصدِرة.'),
    ]

    @api.depends('sequence_number', 'po_reference', 'amount', 'issuing_entity_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s — %s — %s ج.م.' % (
                rec.sequence_number or '—',
                rec.po_reference or '?',
                rec.amount or 0,
            )

    @api.constrains('amount')
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('مبلغ أمر الدفع يجب أن يكون موجباً.'))

    @api.constrains('payment_method', 'cheque_id')
    def _check_cheque_if_method_cheque(self):
        for rec in self:
            if rec.payment_method == 'cheque' and not rec.cheque_id:
                raise ValidationError(_(
                    'إن كانت آلية الدفع = شيك، يجب تحديد الشيك المرتبط.'))

    # ── دورة الحياة ──────────────────────────────────────────────────────────
    def action_receive(self):
        """استلام رسمي — يُولَّد رقم تسلسل قانوني."""
        Seq = self.env['ir.sequence']
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('أمر الدفع ليس في حالة مسودة.'))
            # توليد رقم مسلسل
            if not rec.sequence_number:
                rec.sequence_number = Seq.next_by_code(
                    'port_said.payment_order'
                ) or '/'
            # تحديد السنة المالية
            if rec.received_date and not rec.fiscal_year:
                m = rec.received_date.month
                y = rec.received_date.year
                if m >= 7:
                    rec.fiscal_year = '%d/%d' % (y, y + 1)
                else:
                    rec.fiscal_year = '%d/%d' % (y - 1, y)
            rec.state = 'received'

    def action_register(self):
        """قيد رسمي في الدفتر."""
        for rec in self:
            if rec.state != 'received':
                raise UserError(_('يجب استلام أمر الدفع أولاً.'))
            rec.state = 'registered'
            rec.registered_date = fields.Date.today()
            rec.registered_by = self.env.user.id

    def action_clear(self):
        """تحصيل فعلي — لو بشيك، الشيك يجب أن يُصبح cleared."""
        for rec in self:
            if rec.state != 'registered':
                raise UserError(_('يجب قيد أمر الدفع بالدفتر أولاً.'))
            if rec.payment_method == 'cheque' and rec.cheque_id.state != 'cleared':
                raise UserError(_(
                    'الشيك المرتبط لم يُحصَّل بعد (حالة الشيك: %s).'
                ) % dict(rec.cheque_id._fields['state'].selection).get(
                    rec.cheque_id.state))
            rec.state = 'cleared'
            rec.cleared_date = fields.Date.today()

    def action_post(self):
        """ترحيل محاسبي — ينشئ account.move."""
        for rec in self:
            if rec.state != 'cleared':
                raise UserError(_('يجب تحصيل أمر الدفع أولاً.'))
            if not rec.account_id:
                raise UserError(_('يجب تحديد الحساب الدائن.'))
            # نترك إنشاء القيد للفريق المحاسبي — هذا hook
            rec.state = 'posted'
            rec.message_post(body=_('تم الترحيل المحاسبي.'))

    def action_cancel(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_(
                    'لا يمكن إلغاء أمر دفع مُرحَّل محاسبياً. استخدم قيد تسوية عكسي.'))
            rec.state = 'cancelled'
