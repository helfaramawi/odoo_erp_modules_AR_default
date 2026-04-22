# -*- coding: utf-8 -*-
"""
فولية دفتر نقدية/بنكي
======================
تعرض الحركات اليومية على الحساب النقدي أو البنكي لشهر واحد.
المصدر: account.bank.statement.line (كشف الحساب).

الفارق عن subsidiary/revenue folios:
- هنا الرصيد الجاري مهم (running balance after each line)
- كل سطر له رقم إيداع/شيك/مرجع بنكي يجب عرضه
- الإقفال الشهري يتطلب المطابقة مع كشف البنك الرسمي (Bank Reconciliation)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class CashFolio(models.Model):
    _name = 'port_said.cash.folio'
    _description = 'فولية دفتر نقدية/بنكي'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'book_id, fiscal_year desc, period_month'
    _rec_name = 'display_name'

    # ── الهوية ───────────────────────────────────────────────────────────────
    folio_number = fields.Char(string='رقم الفولية', readonly=True, copy=False, index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    book_id = fields.Many2one('port_said.cash.book', string='الدفتر',
                               required=True, ondelete='restrict', index=True)

    # ── الفترة ───────────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', required=True, index=True)
    period_month = fields.Selection([
        ('07', 'يوليو'), ('08', 'أغسطس'), ('09', 'سبتمبر'),
        ('10', 'أكتوبر'), ('11', 'نوفمبر'), ('12', 'ديسمبر'),
        ('01', 'يناير'), ('02', 'فبراير'), ('03', 'مارس'),
        ('04', 'أبريل'), ('05', 'مايو'), ('06', 'يونيو'),
    ], string='الشهر', required=True, index=True)
    date_from = fields.Date(string='من تاريخ', required=True)
    date_to = fields.Date(string='إلى تاريخ', required=True)

    # ── الأرصدة ──────────────────────────────────────────────────────────────
    opening_balance = fields.Monetary(
        string='الرصيد الافتتاحي',
        currency_field='currency_id',
        help='رصيد آخر الشهر السابق. يُحسب تلقائياً من فولية سابقة أو يُدخل يدوياً.')
    total_receipts = fields.Monetary(
        string='إجمالي المقبوضات',
        compute='_compute_movements', store=True, currency_field='currency_id')
    total_payments = fields.Monetary(
        string='إجمالي المدفوعات',
        compute='_compute_movements', store=True, currency_field='currency_id')
    closing_balance = fields.Monetary(
        string='الرصيد الختامي',
        compute='_compute_movements', store=True, currency_field='currency_id')
    line_count = fields.Integer(string='عدد الحركات',
        compute='_compute_movements', store=True)

    # ── مطابقة البنك ────────────────────────────────────────────────────────
    bank_statement_balance = fields.Monetary(
        string='رصيد كشف البنك الرسمي',
        currency_field='currency_id',
        help='الرصيد كما يظهر في كشف الحساب المُستلَم من البنك. '
             'يُدخَل يدوياً للمطابقة.')
    reconciliation_variance = fields.Monetary(
        string='فرق المطابقة',
        compute='_compute_movements', store=True, currency_field='currency_id',
        help='= الرصيد الختامي المحاسبي − رصيد كشف البنك. يجب أن يكون = 0 للإقفال.')

    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── السطور للعرض ────────────────────────────────────────────────────────
    statement_line_ids = fields.Many2many(
        'account.bank.statement.line',
        compute='_compute_statement_lines',
        string='سطور كشف الحساب')

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',       'مفتوحة'),
        ('reconciled',  'مطابَقة'),
        ('closed',      'مُقفَلة'),
        ('audited',     'مراجَعة'),
        ('archived',    'مؤرشفة'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    closed_by = fields.Many2one('res.users', string='أقفل بواسطة', readonly=True)
    closed_date = fields.Datetime(string='تاريخ الإقفال', readonly=True)
    cashier_signed_by = fields.Char(string='أمين الخزينة (توقيع)')
    accounts_head_signed_by = fields.Char(string='رئيس الحسابات (توقيع)')

    previous_folio_id = fields.Many2one('port_said.cash.folio',
        string='الفولية السابقة', readonly=True)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('uniq_folio_per_book_period',
         'UNIQUE(book_id, fiscal_year, period_month, company_id)',
         'لا يجوز أكثر من فولية واحدة لنفس (الدفتر، السنة، الشهر).'),
    ]

    # ── Display ──────────────────────────────────────────────────────────────
    @api.depends('folio_number', 'period_month', 'fiscal_year', 'book_id')
    def _compute_display_name(self):
        for rec in self:
            month_label = dict(self._fields['period_month'].selection).get(
                rec.period_month, '')
            rec.display_name = '%s — %s/%s — %s' % (
                rec.folio_number or _('جديدة'),
                month_label, rec.fiscal_year or '',
                rec.book_id.name or '')

    # ── Compute Movements ───────────────────────────────────────────────────
    @api.depends('book_id', 'date_from', 'date_to', 'opening_balance',
                 'bank_statement_balance', 'state')
    def _compute_movements(self):
        for folio in self:
            lines = folio._fetch_statement_lines()
            # receipts = amount > 0, payments = amount < 0
            # في Odoo: bank_statement_line.amount موجبة للإيداع، سالبة للسحب
            receipts = sum(l.amount for l in lines if l.amount > 0)
            payments = sum(-l.amount for l in lines if l.amount < 0)
            folio.total_receipts = receipts
            folio.total_payments = payments
            folio.line_count = len(lines)
            folio.closing_balance = folio.opening_balance + receipts - payments
            folio.reconciliation_variance = folio.closing_balance - folio.bank_statement_balance

    @api.depends('book_id', 'date_from', 'date_to')
    def _compute_statement_lines(self):
        for folio in self:
            folio.statement_line_ids = folio._fetch_statement_lines()

    def _fetch_statement_lines(self):
        """يقرأ account.bank.statement.line حسب اليوميات المربوطة بالدفتر."""
        self.ensure_one()
        if not (self.book_id and self.date_from and self.date_to
                and self.book_id.journal_ids):
            return self.env['account.bank.statement.line']
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('journal_id', 'in', self.book_id.journal_ids.ids),
            ('company_id', '=', self.company_id.id),
        ]
        if not self.book_id.include_unreconciled:
            domain.append(('is_reconciled', '=', True))
        return self.env['account.bank.statement.line'].search(
            domain, order='date, id')

    # ── Creation + سلسلة الترحيل ────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('folio_number'):
                book = self.env['port_said.cash.book'].browse(vals['book_id'])
                if book.sequence_id:
                    seq_date = vals.get('date_from') or fields.Date.today()
                    vals['folio_number'] = book.sequence_id.with_context(
                        ir_sequence_date=seq_date
                    ).next_by_id()
        recs = super().create(vals_list)
        for rec in recs:
            rec._link_previous_and_compute_opening()
        return recs

    def _link_previous_and_compute_opening(self):
        self.ensure_one()
        domain = [
            ('book_id', '=', self.book_id.id),
            ('date_to', '<', self.date_from),
            ('state', 'in', ['reconciled', 'closed', 'audited', 'archived']),
            ('id', '!=', self.id),
        ]
        prev = self.search(domain, order='date_to desc', limit=1)
        if prev:
            self.previous_folio_id = prev.id
            self.opening_balance = prev.closing_balance
        else:
            self.opening_balance = 0.0

    # ── Actions ──────────────────────────────────────────────────────────────
    def action_recompute(self):
        for rec in self:
            if rec.state in ('audited', 'archived'):
                raise UserError(_('لا يجوز إعادة حساب فولية مراجَعة أو مؤرشفة.'))
            rec._compute_movements()
            rec.message_post(body=_(
                'أُعيد الحساب. الرصيد الختامي: %s') % rec.closing_balance)
        return True

    def action_reconcile(self):
        """علّم الفولية كمطابَقة — يتطلب variance = 0."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الفولية ليست مفتوحة.'))
            if abs(rec.reconciliation_variance) > 0.01:
                raise UserError(_(
                    'فرق المطابقة = %s. يجب أن يكون صفراً للمطابقة.'
                ) % rec.reconciliation_variance)
            rec.state = 'reconciled'
            rec.message_post(body=_('تمت مطابقة الفولية مع كشف البنك.'))
        return True

    def action_close(self):
        for rec in self:
            if rec.state != 'reconciled':
                raise UserError(_(
                    'يجب مطابقة الفولية مع كشف البنك أولاً.'))
            if not rec.cashier_signed_by:
                raise UserError(_(
                    'يجب توقيع أمين الخزينة قبل الإقفال.'))
            rec.write({
                'state': 'closed',
                'closed_by': self.env.user.id,
                'closed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('أُقفلت الفولية. الرصيد المرحَّل: %s')
                              % rec.closing_balance)
        return True

    def action_audit(self):
        for rec in self:
            if rec.state != 'closed':
                raise UserError(_('يجب إقفال الفولية أولاً.'))
            if not rec.accounts_head_signed_by:
                raise UserError(_('يجب توقيع رئيس الحسابات.'))
            rec.state = 'audited'
        return True

    def action_reopen(self):
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('إعادة الفتح تتطلب صلاحية مدير حسابات.'))
        for rec in self:
            rec.state = 'draft'
            rec.message_post(body=_('أُعيد فتح الفولية بواسطة %s.')
                              % self.env.user.name)
        return True

    # ── Write / Unlink protection ───────────────────────────────────────────
    def write(self, vals):
        protected = {'book_id', 'fiscal_year', 'period_month',
                    'date_from', 'date_to', 'opening_balance',
                    'bank_statement_balance'}
        if any(f in vals for f in protected):
            for rec in self:
                if rec.state in ('closed', 'audited', 'archived'):
                    raise UserError(_(
                        'لا يجوز تعديل فولية مُقفَلة (%s).') % rec.folio_number)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('لا يجوز حذف فولية مُقفَلة.'))
            if rec.line_count > 0:
                raise UserError(_(
                    'لا يجوز حذف فولية بها %d حركة.') % rec.line_count)
        return super().unlink()

    # ── Cron Jobs ────────────────────────────────────────────────────────────
    @api.model
    def cron_recompute_open_folios(self):
        open_folios = self.search([('state', '=', 'draft')])
        for folio in open_folios:
            try:
                folio._compute_movements()
            except Exception as e:
                folio.message_post(body=_('فشل إعادة الحساب: %s') % str(e))
        return len(open_folios)

    @api.model
    def cron_generate_monthly_folios(self):
        today = fields.Date.today()
        if today.month == 1:
            prev_month, prev_year = 12, today.year - 1
        else:
            prev_month, prev_year = today.month - 1, today.year
        date_from = date(prev_year, prev_month, 1)
        from calendar import monthrange
        _, last = monthrange(prev_year, prev_month)
        date_to = date(prev_year, prev_month, last)
        if prev_month >= 7:
            fiscal_year = '%d/%d' % (prev_year, prev_year + 1)
        else:
            fiscal_year = '%d/%d' % (prev_year - 1, prev_year)

        Book = self.env['port_said.cash.book'].search([])
        created = 0
        for book in Book:
            exists = self.search_count([
                ('book_id', '=', book.id),
                ('fiscal_year', '=', fiscal_year),
                ('period_month', '=', '%02d' % prev_month),
            ])
            if exists:
                continue
            self.create({
                'book_id': book.id,
                'fiscal_year': fiscal_year,
                'period_month': '%02d' % prev_month,
                'date_from': date_from,
                'date_to': date_to,
            })
            created += 1
        return created
