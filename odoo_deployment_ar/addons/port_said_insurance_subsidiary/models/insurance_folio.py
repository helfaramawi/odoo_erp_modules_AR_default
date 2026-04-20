# -*- coding: utf-8 -*-
"""
فولية دفتر التأمينات
=====================
صفحة قانونية شهرية في دفتر 78 للتأمينات المؤقتة أو النهائية.

كل فولية:
- ترقيم قانوني مستقل
- ترحيل رصيد من فولية سابقة
- جمع كل حركات الإيداع والاسترداد والمصادرة للشهر
- رصيد ختامي يمثل إجمالي التأمينات القائمة في نهاية الشهر
- تواقيع أمين الخزينة + رئيس الحسابات
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from collections import defaultdict


class InsuranceFolio(models.Model):
    _name = 'port_said.insurance.folio'
    _description = 'فولية دفتر تأمينات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fiscal_year desc, period_month desc, book_classification'
    _rec_name = 'display_name'

    # ── الهوية ───────────────────────────────────────────────────────────────
    folio_number = fields.Char(string='رقم الفولية', readonly=True, copy=False,
        index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    book_classification = fields.Selection([
        ('provisional', 'تأمين مؤقت (دفتر 19)'),
        ('final',       'تأمين نهائي (دفتر 20)'),
    ], string='تصنيف الدفتر', required=True, index=True)

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

    # ── الأرصدة والإجماليات ─────────────────────────────────────────────────
    opening_balance = fields.Monetary(string='نقل من قبله',
        currency_field='currency_id',
        help='إجمالي التأمينات القائمة في نهاية الشهر السابق.')

    total_deposits_cash = fields.Monetary(string='إيداعات نقدية',
        compute='_compute_movements', store=True,
        currency_field='currency_id')
    total_deposits_cheque = fields.Monetary(string='إيداعات بشيك',
        compute='_compute_movements', store=True,
        currency_field='currency_id')
    total_deposits_guarantee = fields.Monetary(string='إيداعات خطابات ضمان',
        compute='_compute_movements', store=True,
        currency_field='currency_id')
    total_deposits = fields.Monetary(string='إجمالي الإيداعات',
        compute='_compute_movements', store=True,
        currency_field='currency_id')

    total_withdrawals = fields.Monetary(string='إجمالي الاستردادات',
        compute='_compute_movements', store=True,
        currency_field='currency_id')
    total_forfeitures = fields.Monetary(string='إجمالي المصادرات',
        compute='_compute_movements', store=True,
        currency_field='currency_id')

    closing_balance = fields.Monetary(string='نقل بعده',
        compute='_compute_movements', store=True,
        currency_field='currency_id',
        help='= نقل من قبله + إجمالي الإيداعات − إجمالي الاستردادات − إجمالي المصادرات.')

    movement_count = fields.Integer(string='عدد الحركات',
        compute='_compute_movements', store=True)

    # ── الحركات المرتبطة ────────────────────────────────────────────────────
    movement_ids = fields.One2many('port_said.insurance.movement',
        'folio_id', string='الحركات')

    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',    'مفتوحة'),
        ('closed',   'مُقفَلة'),
        ('audited',  'مراجَعة'),
        ('archived', 'مؤرشفة'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    closed_by = fields.Many2one('res.users', string='أقفل بواسطة', readonly=True)
    closed_date = fields.Datetime(string='تاريخ الإقفال', readonly=True)
    cashier_signed_by = fields.Char(string='أمين الخزينة (توقيع)')
    accounts_head_signed_by = fields.Char(string='رئيس الحسابات (توقيع)')

    previous_folio_id = fields.Many2one('port_said.insurance.folio',
        string='الفولية السابقة', readonly=True)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('uniq_folio_per_period',
         'UNIQUE(book_classification, fiscal_year, period_month, company_id)',
         'لا يجوز إنشاء فولية مكررة لنفس (الدفتر، السنة، الشهر).'),
    ]

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('folio_number', 'book_classification', 'period_month',
                 'fiscal_year')
    def _compute_display_name(self):
        for rec in self:
            book = dict(self._fields['book_classification'].selection).get(
                rec.book_classification, '')
            month = dict(self._fields['period_month'].selection).get(
                rec.period_month, '')
            rec.display_name = '%s — %s — %s/%s' % (
                rec.folio_number or _('جديدة'),
                book, month, rec.fiscal_year or '')

    @api.depends('movement_ids', 'movement_ids.amount',
                 'movement_ids.movement_type',
                 'movement_ids.collateral_type',
                 'opening_balance', 'state')
    def _compute_movements(self):
        for folio in self:
            deposits = folio.movement_ids.filtered(
                lambda m: m.movement_type == 'deposit')
            folio.total_deposits_cash = sum(
                m.amount for m in deposits if m.collateral_type == 'cash')
            folio.total_deposits_cheque = sum(
                m.amount for m in deposits if m.collateral_type == 'cheque')
            folio.total_deposits_guarantee = sum(
                m.amount for m in deposits if m.collateral_type == 'guarantee')
            folio.total_deposits = (folio.total_deposits_cash +
                                     folio.total_deposits_cheque +
                                     folio.total_deposits_guarantee)
            folio.total_withdrawals = sum(m.amount for m in folio.movement_ids
                                           if m.movement_type == 'withdrawal')
            folio.total_forfeitures = sum(m.amount for m in folio.movement_ids
                                           if m.movement_type == 'forfeiture')
            folio.movement_count = len(folio.movement_ids)
            folio.closing_balance = (folio.opening_balance
                                      + folio.total_deposits
                                      - folio.total_withdrawals
                                      - folio.total_forfeitures)

    # ── Create ───────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('folio_number'):
                seq_code = (
                    'port_said.insurance.folio.final'
                    if vals.get('book_classification') == 'final'
                    else 'port_said.insurance.folio.provisional'
                )
                seq_date = vals.get('date_from') or fields.Date.today()
                vals['folio_number'] = self.env['ir.sequence'].with_context(
                    ir_sequence_date=seq_date
                ).next_by_code(seq_code) or '/'
        recs = super().create(vals_list)
        for rec in recs:
            rec._link_previous_and_compute_opening()
            rec._attach_movements()
        return recs

    def _link_previous_and_compute_opening(self):
        """يجد الفولية السابقة لنفس التصنيف ويحسب الرصيد الافتتاحي."""
        self.ensure_one()
        domain = [
            ('book_classification', '=', self.book_classification),
            ('date_to', '<', self.date_from),
            ('state', 'in', ['closed', 'audited', 'archived']),
            ('id', '!=', self.id),
            ('company_id', '=', self.company_id.id),
        ]
        prev = self.search(domain, order='date_to desc', limit=1)
        if prev:
            self.previous_folio_id = prev.id
            self.opening_balance = prev.closing_balance

    def _attach_movements(self):
        """يسند كل الحركات في الفترة إلى هذه الفولية."""
        self.ensure_one()
        Movement = self.env['port_said.insurance.movement']
        domain = [
            ('folio_id', '=', False),
            ('movement_date', '>=', self.date_from),
            ('movement_date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
        ]
        # فلترة حسب تصنيف الدفتر
        movements = Movement.search(domain)
        filtered = movements.filtered(
            lambda m: (
                (m.bank_guarantee_id and m.bank_guarantee_id.book_classification
                 == self.book_classification)
                or (m.insurance_deposit_id and m.insurance_deposit_id.book_classification
                    == self.book_classification)
            )
        )
        filtered.write({'folio_id': self.id})

    # ── Actions ──────────────────────────────────────────────────────────────
    def action_refresh_movements(self):
        """يُعيد ربط الحركات للفولية (للحالات التي أُنشئت حركات جديدة بعد فتحها)."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('لا يمكن تحديث فولية مُقفَلة.'))
            rec._attach_movements()
            rec._compute_movements()

    def action_close(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الفولية ليست مفتوحة.'))
            if not rec.cashier_signed_by:
                raise UserError(_('يجب توقيع أمين الخزينة.'))
            rec.write({
                'state': 'closed',
                'closed_by': self.env.user.id,
                'closed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_('أُقفلت الفولية. نقل بعده: %s')
                              % rec.closing_balance)

    def action_audit(self):
        for rec in self:
            if rec.state != 'closed':
                raise UserError(_('يجب إقفال الفولية أولاً.'))
            if not rec.accounts_head_signed_by:
                raise UserError(_('يجب توقيع رئيس الحسابات.'))
            rec.state = 'audited'

    def action_reopen(self):
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('إعادة الفتح تتطلب صلاحية مدير حسابات.'))
        for rec in self:
            rec.state = 'draft'
            rec.message_post(body=_('أُعيد فتح الفولية بواسطة %s.')
                              % self.env.user.name)

    def write(self, vals):
        protected = {'book_classification', 'fiscal_year', 'period_month',
                    'date_from', 'date_to', 'opening_balance'}
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
            if rec.movement_count > 0:
                raise UserError(_(
                    'لا يجوز حذف فولية بها %d حركة.') % rec.movement_count)
        return super().unlink()

    # ── Cron ─────────────────────────────────────────────────────────────────
    @api.model
    def cron_generate_monthly_folios(self):
        """شهري: إنشاء فوليوهات الشهر السابق للدفترين (مؤقت + نهائي)."""
        today = fields.Date.today()
        if today.month == 1:
            prev_month, prev_year = 12, today.year - 1
        else:
            prev_month, prev_year = today.month - 1, today.year
        date_from = date(prev_year, prev_month, 1)
        from calendar import monthrange
        _last_day, last = monthrange(prev_year, prev_month)
        date_to = date(prev_year, prev_month, last)
        if prev_month >= 7:
            fiscal_year = '%d/%d' % (prev_year, prev_year + 1)
        else:
            fiscal_year = '%d/%d' % (prev_year - 1, prev_year)

        created = 0
        for classification in ('provisional', 'final'):
            exists = self.search_count([
                ('book_classification', '=', classification),
                ('fiscal_year', '=', fiscal_year),
                ('period_month', '=', '%02d' % prev_month),
            ])
            if exists:
                continue
            self.create({
                'book_classification': classification,
                'fiscal_year': fiscal_year,
                'period_month': '%02d' % prev_month,
                'date_from': date_from,
                'date_to': date_to,
            })
            created += 1
        return created
