# -*- coding: utf-8 -*-
"""
الفولية (Folio)
================

وحدة الترقيم القانوني للدفاتر المساعدة.
- الفولية = صفحة قانونية واحدة من الدفتر، لها رقم تسلسلي قانوني (نموذج رقم 0001، 0002…)
- الفولية لا تخزن السطور المحاسبية — تخزن فقط:
    * نطاق التاريخ
    * مفتاح التجميع (شريك أو حساب)
    * الأرصدة المُرحَّلة (نقل من قبله / نقل بعده) المحسوبة
    * حالة الإقفال
- السطور المحاسبية تُقرأ live من account.move.line عند العرض/الطباعة
- بمجرد إقفال الفولية (state=closed) تتجمد الأرصدة وتمنع التعديل

تصميم متعمد: لا duplicate data.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from collections import defaultdict


class SubsidiaryFolio(models.Model):
    _name = 'port_said.subsidiary.folio'
    _description = 'فولية دفتر مساعد'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'book_id, fiscal_year desc, folio_number'
    _rec_name = 'display_name'

    # ── الهوية ───────────────────────────────────────────────────────────────
    folio_number = fields.Char(string='رقم الفولية', readonly=True, copy=False, index=True,
                                help='يُولَّد تلقائياً من تسلسل الدفتر')
    display_name = fields.Char(compute='_compute_display_name', store=True)
    book_id = fields.Many2one('port_said.subsidiary.book', string='الدفتر',
                               required=True, ondelete='restrict', index=True)

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', required=True, index=True,
                               help='بصيغة YYYY/YYYY+1، مثلاً 2024/2025 (تبدأ 1 يوليو)')
    period_month = fields.Selection([
        ('07', 'يوليو'), ('08', 'أغسطس'), ('09', 'سبتمبر'),
        ('10', 'أكتوبر'), ('11', 'نوفمبر'), ('12', 'ديسمبر'),
        ('01', 'يناير'), ('02', 'فبراير'), ('03', 'مارس'),
        ('04', 'أبريل'), ('05', 'مايو'), ('06', 'يونيو'),
    ], string='الشهر', required=True, index=True)
    date_from = fields.Date(string='من تاريخ', required=True)
    date_to = fields.Date(string='إلى تاريخ', required=True)

    # ── مفتاح التجميع ────────────────────────────────────────────────────────
    partner_id = fields.Many2one('res.partner', string='الشريك', index=True,
                                  help='للفوليوهات المجموعة بالشريك (مفردات/شخصية)')
    account_id = fields.Many2one('account.account', string='الحساب', index=True,
                                  help='للفوليوهات المجموعة بالحساب (إجمالي)')

    # ── أرصدة الترحيل ────────────────────────────────────────────────────────
    opening_balance = fields.Monetary(string='نقل من قبله',
        currency_field='currency_id',
        help='الرصيد المُرحَّل من الفولية السابقة. يُحسب تلقائياً عند الفتح.')
    period_debit = fields.Monetary(string='حركة مدينة',
        currency_field='currency_id', compute='_compute_period_movements', store=True)
    period_credit = fields.Monetary(string='حركة دائنة',
        currency_field='currency_id', compute='_compute_period_movements', store=True)
    closing_balance = fields.Monetary(string='نقل بعده',
        currency_field='currency_id', compute='_compute_period_movements', store=True,
        help='الرصيد المُرحَّل إلى الفولية التالية = نقل من قبله + مدين − دائن (للحسابات المدينة) أو العكس.')

    line_count = fields.Integer(string='عدد السطور',
        compute='_compute_period_movements', store=True)

    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── الحالة وحوكمة الإقفال ────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',   'مفتوحة'),
        ('closed',  'مُقفَلة (مرحَّلة شهرياً)'),
        ('audited', 'مراجَعة'),
        ('archived','مؤرشفة (سنوياً)'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    closed_by = fields.Many2one('res.users', string='أقفل بواسطة', readonly=True)
    closed_date = fields.Datetime(string='تاريخ الإقفال', readonly=True)
    crossout_signed_by = fields.Char(string='موظف الشطب (توقيع)')
    accounts_head_signed_by = fields.Char(string='رئيس الحسابات (توقيع)')

    # ── ربط بفولية سابقة / لاحقة (سلسلة الترحيل) ─────────────────────────────
    previous_folio_id = fields.Many2one('port_said.subsidiary.folio',
        string='الفولية السابقة', readonly=True,
        help='الفولية التي نقلت رصيدها لهذه الفولية.')

    # ── Computed سطور للعرض ──────────────────────────────────────────────────
    move_line_ids = fields.Many2many('account.move.line',
        compute='_compute_move_lines', string='السطور المحاسبية',
        help='يُحسب عند الطلب من account.move.line حسب فلتر الدفتر.')

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('uniq_folio_per_book_year_key',
         'UNIQUE(book_id, fiscal_year, period_month, partner_id, account_id, company_id)',
         'لا يجوز إنشاء أكثر من فولية واحدة لنفس (الدفتر، السنة، الشهر، مفتاح التجميع).'),
    ]

    # ── Display ──────────────────────────────────────────────────────────────
    @api.depends('folio_number', 'partner_id', 'account_id', 'period_month', 'fiscal_year')
    def _compute_display_name(self):
        for rec in self:
            key = rec.partner_id.name or rec.account_id.display_name or _('بلا مفتاح')
            rec.display_name = '%s — %s — %s/%s' % (
                rec.folio_number or _('جديدة'),
                key,
                dict(self._fields['period_month'].selection).get(rec.period_month, ''),
                rec.fiscal_year or '',
            )

    # ── Compute Movements (the heart of the engine) ──────────────────────────
    @api.depends('book_id', 'date_from', 'date_to', 'partner_id', 'account_id', 'state')
    def _compute_period_movements(self):
        """يقرأ من account.move.line ويحسب مدين/دائن/رصيد للفترة."""
        for folio in self:
            lines = folio._fetch_lines()
            folio.period_debit = sum(lines.mapped('debit'))
            folio.period_credit = sum(lines.mapped('credit'))
            folio.line_count = len(lines)
            # رصيد الإقفال = افتتاحي + (مدين - دائن) للحسابات المدينة
            #              = افتتاحي - (مدين - دائن) للحسابات الدائنة
            net_movement = folio.period_debit - folio.period_credit
            folio.closing_balance = folio.opening_balance + net_movement

    @api.depends('book_id', 'date_from', 'date_to', 'partner_id', 'account_id')
    def _compute_move_lines(self):
        for folio in self:
            folio.move_line_ids = folio._fetch_lines()

    def _fetch_lines(self):
        """البناء الديناميكي للدومين على account.move.line."""
        self.ensure_one()
        if not (self.book_id and self.date_from and self.date_to):
            return self.env['account.move.line']

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
        ]

        # حالة الترحيل
        if not self.book_id.include_unposted:
            domain.append(('parent_state', '=', 'posted'))

        # فلترة على اليوميات
        if self.book_id.journal_ids:
            domain.append(('journal_id', 'in', self.book_id.journal_ids.ids))

        # فلترة على تصنيف الحساب
        if self.book_id.account_classification_ids:
            cls_ids = self.book_id.account_classification_ids.ids
            domain.append(
                ('account_id.x_subsidiary_classification_id', 'in', cls_ids))

        # فلترة على الجانب
        if self.book_id.side == 'debit':
            domain.append(('debit', '>', 0))
        elif self.book_id.side == 'credit':
            domain.append(('credit', '>', 0))
        # side == 'both' : لا فلترة إضافية

        # فلترة على مفتاح التجميع
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.account_id:
            domain.append(('account_id', '=', self.account_id.id))

        return self.env['account.move.line'].search(domain, order='date, id')

    # ── إنشاء الرقم القانوني ────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('folio_number'):
                book = self.env['port_said.subsidiary.book'].browse(vals['book_id'])
                if book.sequence_id:
                    seq_date = vals.get('date_from') or fields.Date.today()
                    vals['folio_number'] = book.sequence_id.with_context(
                        ir_sequence_date=seq_date
                    ).next_by_id()
        recs = super().create(vals_list)
        # ربط بالفولية السابقة وحساب الرصيد الافتتاحي
        for rec in recs:
            rec._link_previous_and_compute_opening()
        return recs

    def _link_previous_and_compute_opening(self):
        """يجد الفولية السابقة لنفس مفتاح التجميع ويحسب الرصيد الافتتاحي."""
        self.ensure_one()
        domain = [
            ('book_id', '=', self.book_id.id),
            ('partner_id', '=', self.partner_id.id),
            ('account_id', '=', self.account_id.id),
            ('date_to', '<', self.date_from),
            ('state', 'in', ['closed', 'audited', 'archived']),
            ('id', '!=', self.id),
        ]
        prev = self.search(domain, order='date_to desc', limit=1)
        if prev:
            self.previous_folio_id = prev.id
            self.opening_balance = prev.closing_balance
        else:
            # الفولية الأولى — رصيد افتتاحي = 0 ما لم يُملأ يدوياً
            self.opening_balance = 0.0

    # ── إعادة الحساب يدوياً (للحالات الاستثنائية) ───────────────────────────
    def action_recompute(self):
        """يُجبر إعادة قراءة السطور وإعادة حساب الأرصدة.
        مفيد بعد تعديل تصنيفات الحسابات أو إعادة ترحيل قيود قديمة."""
        for rec in self:
            if rec.state in ('audited', 'archived'):
                raise UserError(_(
                    'لا يجوز إعادة حساب فولية مراجَعة أو مؤرشفة (%s).'
                ) % rec.folio_number)
            rec._compute_period_movements()
            rec.message_post(body=_(
                'أُعيد حساب الأرصدة بواسطة %s. الرصيد الجديد: %s'
            ) % (self.env.user.name, rec.closing_balance))
        return True

    # ── إقفال شهري ───────────────────────────────────────────────────────────
    def action_close(self):
        """إقفال الفولية شهرياً — يجمد الأرصدة ويسمح بإنشاء فولية الشهر التالي."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الفولية رقم %s ليست في حالة مفتوحة.') % rec.folio_number)
            if not rec.crossout_signed_by:
                raise UserError(_(
                    'يجب توقيع موظف الشطب قبل الإقفال. '
                    'الفولية رقم %s.') % rec.folio_number)
            # تجميد القيم بحفظها كقيم مخزنة (compute store=True يقوم بذلك)
            rec.write({
                'state': 'closed',
                'closed_by': self.env.user.id,
                'closed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('أُقفلت الفولية. الرصيد المُرحَّل: %s') %
                              rec.closing_balance)
        return True

    def action_audit(self):
        """مراجعة الفولية بعد الإقفال — يصبح أي تعديل ممنوعاً."""
        for rec in self:
            if rec.state != 'closed':
                raise UserError(_('يجب إقفال الفولية أولاً.'))
            if not rec.accounts_head_signed_by:
                raise UserError(_(
                    'يجب توقيع رئيس الحسابات قبل اعتماد المراجعة.'))
            rec.state = 'audited'
        return True

    def action_reopen(self):
        """إعادة فتح — صلاحية إدارية فقط، تترك أثراً في chatter."""
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('إعادة فتح الفولية تتطلب صلاحية مدير حسابات.'))
        for rec in self:
            rec.state = 'draft'
            rec.message_post(body=_(
                'أُعيد فتح الفولية بواسطة %s — يُلزم تسجيل سبب في الملاحظات.'
            ) % self.env.user.name)
        return True

    # ── حماية ضد التعديل بعد الإقفال ────────────────────────────────────────
    def write(self, vals):
        # السماح فقط بحقول الحوكمة في الفوليوهات المُقفَلة
        protected_fields = {'date_from', 'date_to', 'partner_id', 'account_id',
                           'book_id', 'fiscal_year', 'period_month',
                           'opening_balance'}
        if any(f in vals for f in protected_fields):
            for rec in self:
                if rec.state in ('closed', 'audited', 'archived'):
                    raise UserError(_(
                        'لا يجوز تعديل الفولية المُقفَلة (%s). '
                        'استخدم "إعادة فتح" بصلاحية المدير.') % rec.folio_number)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('لا يجوز حذف فولية مُقفَلة.'))
            if rec.line_count > 0:
                raise UserError(_(
                    'لا يجوز حذف فولية تحتوي على سطور محاسبية. '
                    'الفولية رقم %s تحتوي %d سطر.') %
                    (rec.folio_number, rec.line_count))
        return super().unlink()

    # ── توليد جماعي شهري ────────────────────────────────────────────────────
    @api.model
    def cron_recompute_open_folios(self):
        """مهمة ليلية: تُعيد حساب أرصدة الفوليوهات المفتوحة (state=draft) لقراءة
        أي قيود محاسبية جديدة رُحِّلت بعد آخر حساب. لا تمس الفوليوهات المُقفَلة."""
        open_folios = self.search([('state', '=', 'draft')])
        for folio in open_folios:
            try:
                folio._compute_period_movements()
            except Exception as e:
                folio.message_post(body=_(
                    'فشل إعادة حساب الأرصدة: %s'
                ) % str(e))
        return len(open_folios)

    @api.model
    def cron_generate_monthly_folios(self):
        """مهمة دورية شهرية: تنشئ فولية جديدة لكل (دفتر × مفتاح تجميع نشط) في
        الشهر الجاري إن لم تكن موجودة بالفعل. يُشغَّل ليلاً يوم 2 من كل شهر."""
        today = fields.Date.today()
        # الشهر السابق
        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year
        date_from = date(prev_year, prev_month, 1)
        if prev_month == 12:
            date_to = date(prev_year, 12, 31)
        else:
            from calendar import monthrange
            _, last = monthrange(prev_year, prev_month)
            date_to = date(prev_year, prev_month, last)

        # السنة المالية تبدأ 1 يوليو
        if prev_month >= 7:
            fiscal_year = '%d/%d' % (prev_year, prev_year + 1)
        else:
            fiscal_year = '%d/%d' % (prev_year - 1, prev_year)

        Book = self.env['port_said.subsidiary.book'].search([])
        AML = self.env['account.move.line']
        created_count = 0

        for book in Book:
            # ابحث عن كل المفاتيح النشطة في الفترة
            domain = [
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', book.company_id.id),
            ]
            if book.account_classification_ids:
                domain.append(
                    ('account_id.x_subsidiary_classification_id',
                     'in', book.account_classification_ids.ids))
            lines = AML.search(domain)

            keys = set()
            for line in lines:
                if book.grouping_key == 'partner':
                    keys.add((line.partner_id.id, False))
                elif book.grouping_key == 'account':
                    keys.add((False, line.account_id.id))
                else:  # partner_account
                    keys.add((line.partner_id.id, line.account_id.id))

            for partner_id, account_id in keys:
                # تخطَّ إن كانت الفولية موجودة
                exists = self.search_count([
                    ('book_id', '=', book.id),
                    ('fiscal_year', '=', fiscal_year),
                    ('period_month', '=', '%02d' % prev_month),
                    ('partner_id', '=', partner_id or False),
                    ('account_id', '=', account_id or False),
                ])
                if exists:
                    continue
                self.create({
                    'book_id': book.id,
                    'fiscal_year': fiscal_year,
                    'period_month': '%02d' % prev_month,
                    'date_from': date_from,
                    'date_to': date_to,
                    'partner_id': partner_id or False,
                    'account_id': account_id or False,
                })
                created_count += 1
        return created_count
