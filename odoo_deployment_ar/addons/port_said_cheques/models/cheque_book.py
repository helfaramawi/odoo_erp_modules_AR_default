# -*- coding: utf-8 -*-
"""
دفتر الشيكات الورقي (Physical Cheque Book)
============================================
يُمثِّل دفتر شيكات ورقي واحد مسبق الطباعة، صادر من البنك للوحدة الحكومية.

الغرض:
- تتبع نطاق أرقام الشيكات المتاحة في كل دفتر (مثال: 100001 - 100050)
- ضمان أن كل شيك صادر مربوط بدفتر ورقي محدد (auditability requirement)
- منع إصدار شيك برقم خارج النطاق المتاح
- التحكم في دورة الحياة: مُستلَم → قيد الاستخدام → مُكتمل → مُسلَّم للأرشيف

المتطلب القانوني: اللائحة التنفيذية للمحاسبة الحكومية تتطلب أن يكون كل شيك
صادر قابلاً للربط مع كعب الدفتر الورقي الأصلي، وأن يُحفَظ الدفتر حتى بعد اكتماله
للرجوع إليه في حالة الخلاف أو المراجعة.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ChequeBook(models.Model):
    _name = 'port_said.cheque.book'
    _description = 'دفتر شيكات ورقي'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'received_date desc, book_reference'
    _rec_name = 'display_name'

    # ── الهوية ───────────────────────────────────────────────────────────────
    book_reference = fields.Char(string='رقم الدفتر المرجعي', required=True,
        help='الرقم المُعطى من البنك أو الوحدة للدفتر الورقي.')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    bank_name = fields.Char(string='البنك المُصدر', required=True,
        help='مثال: البنك المركزي المصري، بنك مصر...')
    bank_account_id = fields.Many2one('res.partner.bank',
        string='الحساب البنكي',
        help='الحساب البنكي الذي يُسحَب عليه من هذا الدفتر.')
    bank_account_no = fields.Char(string='رقم الحساب البنكي')

    # ── نطاق الأرقام ────────────────────────────────────────────────────────
    first_cheque_number = fields.Integer(string='أول رقم شيك', required=True,
        help='أول رقم في الدفتر (مثال: 100001)')
    last_cheque_number = fields.Integer(string='آخر رقم شيك', required=True,
        help='آخر رقم في الدفتر (مثال: 100050)')
    total_cheques = fields.Integer(string='عدد الشيكات',
        compute='_compute_total_cheques', store=True)
    cheques_used = fields.Integer(string='عدد المستخدَم',
        compute='_compute_usage', store=True)
    cheques_remaining = fields.Integer(string='المتبقي',
        compute='_compute_usage', store=True)
    next_available_number = fields.Integer(string='الرقم التالي المتاح',
        compute='_compute_usage', store=True,
        help='يُحسب من آخر شيك مُستخدَم + 1.')

    # ── التواريخ ────────────────────────────────────────────────────────────
    received_date = fields.Date(string='تاريخ الاستلام', required=True,
        default=fields.Date.today,
        help='تاريخ استلام الدفتر من البنك.')
    start_use_date = fields.Date(string='تاريخ بدء الاستخدام')
    completion_date = fields.Date(string='تاريخ اكتمال الاستخدام', readonly=True)
    archive_date = fields.Date(string='تاريخ التسليم للأرشيف', readonly=True)

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('received', 'مُستلَم'),
        ('in_use',   'قيد الاستخدام'),
        ('completed','مُكتمل'),
        ('archived', 'مُرسَل للأرشيف'),
        ('lost',     'مفقود / مسروق'),
    ], string='الحالة', default='received', tracking=True, required=True)

    lost_reason = fields.Text(string='تفاصيل الفقدان/السرقة')
    lost_report_reference = fields.Char(string='رقم محضر الشرطة',
        help='مطلوب في حالة الفقدان — للتسجيل في دفاتر الرقابة.')

    # ── الربط المحاسبي ──────────────────────────────────────────────────────
    journal_id = fields.Many2one('account.journal',
        string='اليومية المحاسبية المرتبطة',
        domain="[('type', '=', 'bank')]",
        help='اليومية البنكية التي تُقيَّد عليها الشيكات من هذا الدفتر.')

    # ── الأمانة ─────────────────────────────────────────────────────────────
    custodian_id = fields.Many2one('hr.employee',
        string='الموظف المسؤول (الأمين)',
        help='الموظف المُكلَّف بحفظ الدفتر واستخدامه.')

    # ── العلاقات ────────────────────────────────────────────────────────────
    cheque_ids = fields.One2many('port_said.cheque', 'cheque_book_id',
        string='الشيكات الصادرة')

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('book_reference_uniq',
         'UNIQUE(book_reference, bank_name, company_id)',
         'رقم دفتر الشيكات مكرر على نفس البنك.'),
    ]

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('book_reference', 'bank_name', 'first_cheque_number',
                 'last_cheque_number')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s — %s (%d–%d)' % (
                rec.bank_name or '—',
                rec.book_reference or '?',
                rec.first_cheque_number or 0,
                rec.last_cheque_number or 0,
            )

    @api.depends('first_cheque_number', 'last_cheque_number')
    def _compute_total_cheques(self):
        for rec in self:
            if rec.first_cheque_number and rec.last_cheque_number:
                rec.total_cheques = rec.last_cheque_number - rec.first_cheque_number + 1
            else:
                rec.total_cheques = 0

    @api.depends('cheque_ids', 'cheque_ids.state', 'total_cheques',
                 'first_cheque_number')
    def _compute_usage(self):
        for rec in self:
            # الشيكات المُستخدَمة = كل ما ليس draft أو cancelled
            used = rec.cheque_ids.filtered(
                lambda c: c.state not in ('draft', 'cancelled'))
            rec.cheques_used = len(used)
            rec.cheques_remaining = rec.total_cheques - rec.cheques_used

            # الرقم التالي المتاح: أكبر رقم مُستخدَم + 1، أو first_cheque_number
            used_numbers = []
            for c in used:
                try:
                    used_numbers.append(int(c.cheque_number))
                except (ValueError, TypeError):
                    pass
            if used_numbers:
                rec.next_available_number = max(used_numbers) + 1
            else:
                rec.next_available_number = rec.first_cheque_number

    # ── Constraints ──────────────────────────────────────────────────────────
    @api.constrains('first_cheque_number', 'last_cheque_number')
    def _check_number_range(self):
        for rec in self:
            if rec.first_cheque_number <= 0 or rec.last_cheque_number <= 0:
                raise ValidationError(_(
                    'أرقام الشيكات يجب أن تكون موجبة.'))
            if rec.first_cheque_number > rec.last_cheque_number:
                raise ValidationError(_(
                    'أول رقم يجب أن يكون أصغر من أو يساوي آخر رقم.'))

    @api.constrains('first_cheque_number', 'last_cheque_number', 'bank_name')
    def _check_no_overlap(self):
        """يمنع تداخل نطاقات الأرقام على نفس البنك."""
        for rec in self:
            if not all([rec.first_cheque_number, rec.last_cheque_number, rec.bank_name]):
                continue
            conflicting = self.search([
                ('id', '!=', rec.id),
                ('bank_name', '=', rec.bank_name),
                ('state', '!=', 'lost'),
                '|', '|',
                # النطاقات متداخلة في الحالات الثلاث:
                '&', ('first_cheque_number', '<=', rec.first_cheque_number),
                     ('last_cheque_number', '>=', rec.first_cheque_number),
                '&', ('first_cheque_number', '<=', rec.last_cheque_number),
                     ('last_cheque_number', '>=', rec.last_cheque_number),
                '&', ('first_cheque_number', '>=', rec.first_cheque_number),
                     ('last_cheque_number', '<=', rec.last_cheque_number),
            ])
            if conflicting:
                raise ValidationError(_(
                    'نطاق أرقام الشيكات متداخل مع دفتر آخر: %s (%d – %d).'
                ) % (conflicting[0].book_reference,
                     conflicting[0].first_cheque_number,
                     conflicting[0].last_cheque_number))

    # ── Lifecycle Actions ────────────────────────────────────────────────────
    def action_start_use(self):
        for rec in self:
            if rec.state != 'received':
                raise UserError(_('الدفتر ليس في حالة "مُستلَم".'))
            if not rec.journal_id:
                raise UserError(_(
                    'يجب تحديد اليومية البنكية قبل بدء الاستخدام.'))
            rec.state = 'in_use'
            rec.start_use_date = fields.Date.today()

    def action_complete(self):
        for rec in self:
            if rec.state != 'in_use':
                raise UserError(_('الدفتر ليس قيد الاستخدام.'))
            if rec.cheques_remaining > 0:
                raise UserError(_(
                    'لا يمكن اكتمال الدفتر وبه %d شيك متبقي. '
                    'استخدم "مفقود/مسروق" بدلاً من ذلك.') % rec.cheques_remaining)
            rec.state = 'completed'
            rec.completion_date = fields.Date.today()

    def action_archive(self):
        for rec in self:
            if rec.state != 'completed':
                raise UserError(_(
                    'يجب أن يكون الدفتر مُكتملاً قبل التسليم للأرشيف.'))
            rec.state = 'archived'
            rec.archive_date = fields.Date.today()

    def action_report_lost(self):
        """إجراء استثنائي يتطلب محضر شرطة."""
        for rec in self:
            if rec.state in ('archived', 'lost'):
                raise UserError(_('الدفتر بالفعل في حالة نهائية.'))
            if not rec.lost_reason or not rec.lost_report_reference:
                raise UserError(_(
                    'يجب إدخال سبب الفقدان ورقم محضر الشرطة قبل الإبلاغ.'))
            rec.state = 'lost'
            rec.message_post(body=_(
                '⚠ تم الإبلاغ عن فقدان/سرقة الدفتر. محضر: %s. السبب: %s'
            ) % (rec.lost_report_reference, rec.lost_reason))

    # ── Helper: validate a cheque number is within this book ────────────────
    def _is_number_in_range(self, cheque_number_str):
        """يتحقق من أن رقم الشيك يقع ضمن نطاق هذا الدفتر."""
        self.ensure_one()
        try:
            n = int(cheque_number_str)
        except (ValueError, TypeError):
            return False
        return self.first_cheque_number <= n <= self.last_cheque_number
