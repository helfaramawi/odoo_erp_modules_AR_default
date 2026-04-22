# -*- coding: utf-8 -*-
"""
فولية دفتر حركة النقود
========================
صفحة قانونية شهرية في دفتر 39.

نموذج واحد لكلا الدفترين (مرسل + وارد) مع تمييز عبر direction.
كل فولية تجمع تحويلات شهر واحد حسب الاتجاه.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from calendar import monthrange


class TransferFolio(models.Model):
    _name = 'port_said.cash_transfer.folio'
    _description = 'فولية دفتر حركة النقود'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fiscal_year desc, period_month desc, direction'
    _rec_name = 'display_name'

    folio_number = fields.Char(string='رقم الفولية',
        readonly=True, copy=False, index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    direction = fields.Selection([
        ('outgoing', 'نقود مرسلة'),
        ('incoming', 'نقود واردة'),
    ], string='الاتجاه', required=True, index=True)

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
    opening_cumulative = fields.Monetary(string='نقل من قبله (تراكمي)',
        currency_field='currency_id',
        help='الإجمالي التراكمي منذ بداية السنة المالية حتى نهاية الشهر السابق.')
    total_confirmed = fields.Monetary(string='إجمالي المُؤكَّد',
        compute='_compute_totals', store=True,
        currency_field='currency_id',
        help='إجمالي التحويلات التي بلغت حالة confirmed أو closed.')
    total_disputed = fields.Monetary(string='إجمالي المُتنازَع فيه',
        compute='_compute_totals', store=True,
        currency_field='currency_id')
    total_lost = fields.Monetary(string='إجمالي المفقود',
        compute='_compute_totals', store=True,
        currency_field='currency_id')
    closing_cumulative = fields.Monetary(string='نقل بعده (تراكمي)',
        compute='_compute_totals', store=True,
        currency_field='currency_id')

    transfer_count = fields.Integer(string='عدد التحويلات',
        compute='_compute_totals', store=True)

    # ── العلاقة بالتحويلات ─────────────────────────────────────────────────
    transfer_ids = fields.One2many('port_said.cash_transfer',
        'folio_id', string='التحويلات')

    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',    'مفتوحة'),
        ('closed',   'مُقفَلة'),
        ('audited',  'مراجَعة'),
        ('archived', 'مؤرشفة'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    closed_by = fields.Many2one('res.users', readonly=True)
    closed_date = fields.Datetime(readonly=True)
    cashier_signed_by = fields.Char(string='أمين الخزينة (توقيع)')
    accounts_head_signed_by = fields.Char(string='رئيس الحسابات (توقيع)')

    previous_folio_id = fields.Many2one('port_said.cash_transfer.folio',
        string='الفولية السابقة', readonly=True)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('uniq_folio_per_period',
         'UNIQUE(direction, fiscal_year, period_month, company_id)',
         'لا يجوز فولية مكررة لنفس (الاتجاه، السنة، الشهر).'),
    ]

    @api.depends('folio_number', 'direction', 'period_month', 'fiscal_year')
    def _compute_display_name(self):
        for rec in self:
            dir_label = 'مرسلة' if rec.direction == 'outgoing' else 'واردة'
            month = dict(self._fields['period_month'].selection).get(
                rec.period_month, '')
            rec.display_name = '%s — نقود %s — %s/%s' % (
                rec.folio_number or _('جديدة'),
                dir_label, month, rec.fiscal_year or '')

    @api.depends('transfer_ids', 'transfer_ids.amount', 'transfer_ids.state',
                 'transfer_ids.disputed_amount', 'opening_cumulative')
    def _compute_totals(self):
        for folio in self:
            confirmed = folio.transfer_ids.filtered(
                lambda t: t.state in ('confirmed', 'closed'))
            disputed = folio.transfer_ids.filtered(
                lambda t: t.state == 'disputed')
            lost = folio.transfer_ids.filtered(
                lambda t: t.state == 'lost')
            folio.total_confirmed = sum(t.amount for t in confirmed)
            folio.total_disputed = sum(t.disputed_amount for t in disputed)
            folio.total_lost = sum(t.amount for t in lost)
            folio.transfer_count = len(folio.transfer_ids)
            folio.closing_cumulative = (folio.opening_cumulative
                                        + folio.total_confirmed)

    # ── Create + سلسلة الترحيل ──────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('folio_number'):
                seq_code = (
                    'port_said.cash_transfer.folio.outgoing'
                    if vals.get('direction') == 'outgoing'
                    else 'port_said.cash_transfer.folio.incoming'
                )
                seq_date = vals.get('date_from') or fields.Date.today()
                vals['folio_number'] = self.env['ir.sequence'].with_context(
                    ir_sequence_date=seq_date
                ).next_by_code(seq_code) or '/'
        recs = super().create(vals_list)
        for rec in recs:
            rec._link_previous_and_compute_opening()
            rec._attach_transfers()
        return recs

    def _link_previous_and_compute_opening(self):
        self.ensure_one()
        domain = [
            ('direction', '=', self.direction),
            ('date_to', '<', self.date_from),
            ('state', 'in', ['closed', 'audited', 'archived']),
            ('id', '!=', self.id),
            ('company_id', '=', self.company_id.id),
        ]
        prev = self.search(domain, order='date_to desc', limit=1)
        if prev:
            self.previous_folio_id = prev.id
            self.opening_cumulative = prev.closing_cumulative

    def _attach_transfers(self):
        """يُسند كل التحويلات في الفترة بنفس الاتجاه لهذه الفولية."""
        self.ensure_one()
        Transfer = self.env['port_said.cash_transfer']
        transfers = Transfer.search([
            ('folio_id', '=', False),
            ('direction', '=', self.direction),
            ('transfer_date', '>=', self.date_from),
            ('transfer_date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
            ('state', '!=', 'draft'),
        ])
        transfers.write({'folio_id': self.id})

    # ── Actions ──────────────────────────────────────────────────────────────
    def action_refresh(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('لا يمكن تحديث فولية مُقفَلة.'))
            rec._attach_transfers()
            rec._compute_totals()

    def action_close(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الفولية ليست مفتوحة.'))
            if not rec.cashier_signed_by:
                raise UserError(_('يجب توقيع أمين الخزينة.'))
            # منع الإقفال إن كان هناك تنازع غير مُسَوَّى
            unresolved = rec.transfer_ids.filtered(lambda t: t.state == 'disputed')
            if unresolved:
                raise UserError(_(
                    'يوجد %d تحويل متنازَع فيه لم تُسَوَّ بعد. يجب حل التنازعات قبل الإقفال.'
                ) % len(unresolved))
            rec.write({
                'state': 'closed',
                'closed_by': self.env.user.id,
                'closed_date': fields.Datetime.now(),
            })

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
        protected = {'direction', 'fiscal_year', 'period_month',
                    'date_from', 'date_to', 'opening_cumulative'}
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
            if rec.transfer_count > 0:
                raise UserError(_(
                    'لا يجوز حذف فولية بها %d تحويل.') % rec.transfer_count)
        return super().unlink()

    # ── Cron ─────────────────────────────────────────────────────────────────
    @api.model
    def cron_generate_monthly(self):
        today = fields.Date.today()
        if today.month == 1:
            prev_month, prev_year = 12, today.year - 1
        else:
            prev_month, prev_year = today.month - 1, today.year
        date_from = date(prev_year, prev_month, 1)
        _unused, last = monthrange(prev_year, prev_month)
        date_to = date(prev_year, prev_month, last)
        if prev_month >= 7:
            fiscal_year = '%d/%d' % (prev_year, prev_year + 1)
        else:
            fiscal_year = '%d/%d' % (prev_year - 1, prev_year)

        created = 0
        for direction in ('outgoing', 'incoming'):
            exists = self.search_count([
                ('direction', '=', direction),
                ('fiscal_year', '=', fiscal_year),
                ('period_month', '=', '%02d' % prev_month),
            ])
            if exists:
                continue
            self.create({
                'direction': direction,
                'fiscal_year': fiscal_year,
                'period_month': '%02d' % prev_month,
                'date_from': date_from,
                'date_to': date_to,
            })
            created += 1
        return created
