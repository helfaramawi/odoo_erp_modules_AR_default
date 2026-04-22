# -*- coding: utf-8 -*-
"""
فولية إيرادات/مصروفات
=====================
كل فولية = شهر واحد من دفتر إيرادات/مصروفات. تحتوي على:
- مصفوفة (days × budget_items) محسوبة من account.move.line
- إجمالي يومي + إجمالي شهري لكل بند
- ترقيم قانوني + ترحيل (نقل بعده / من قبله)
- حالة وحوكمة الإقفال (مماثل لـ subsidiary.folio)

التصميم: نفس مبدأ subsidiary_books — الفولية لا تخزن السطور، تقرأها live.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
from collections import defaultdict
import json


class RevenueFolio(models.Model):
    _name = 'port_said.revenue.folio'
    _description = 'فولية دفتر إيرادات/مصروفات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'book_id, fiscal_year desc, period_month'
    _rec_name = 'display_name'

    # ── الهوية ───────────────────────────────────────────────────────────────
    folio_number = fields.Char(string='رقم الفولية', readonly=True, copy=False, index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    book_id = fields.Many2one('port_said.revenue.book', string='الدفتر',
                               required=True, ondelete='restrict', index=True)

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', required=True, index=True)
    period_month = fields.Selection([
        ('07', 'يوليو'), ('08', 'أغسطس'), ('09', 'سبتمبر'),
        ('10', 'أكتوبر'), ('11', 'نوفمبر'), ('12', 'ديسمبر'),
        ('01', 'يناير'), ('02', 'فبراير'), ('03', 'مارس'),
        ('04', 'أبريل'), ('05', 'مايو'), ('06', 'يونيو'),
    ], string='الشهر', required=True, index=True)
    date_from = fields.Date(string='من تاريخ', required=True)
    date_to = fields.Date(string='إلى تاريخ', required=True)

    # ── خطة الموازنة المرجعية (لاسترداد بنود الموازنة المعرَّفة) ────────────
    budget_plan_id = fields.Many2one('port_said.budget.plan',
        string='خطة الموازنة المرجعية',
        help='تحدد الأعمدة الافتراضية في طباعة Cross-tab (نموذج 10).')

    # ── أرصدة شهرية ──────────────────────────────────────────────────────────
    period_total = fields.Monetary(string='إجمالي الشهر',
        currency_field='currency_id',
        compute='_compute_period_totals', store=True)
    opening_carryforward = fields.Monetary(string='نقل من قبله',
        currency_field='currency_id',
        help='الإجمالي التراكمي من بداية السنة المالية حتى نهاية الشهر السابق.')
    closing_carryforward = fields.Monetary(string='نقل بعده',
        currency_field='currency_id',
        compute='_compute_period_totals', store=True,
        help='= نقل من قبله + إجمالي الشهر')

    line_count = fields.Integer(string='عدد السطور',
        compute='_compute_period_totals', store=True)

    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── مصفوفة Cross-tab (محسوبة، لا مخزَّنة) ────────────────────────────────
    matrix_json = fields.Text(string='مصفوفة الأعمدة (JSON)',
        compute='_compute_matrix', store=False,
        help='مصفوفة بنية {day: {budget_code: amount}} — للاستخدام الداخلي بالطباعة.')

    matrix_columns_json = fields.Text(string='ترتيب الأعمدة (JSON)',
        compute='_compute_matrix', store=False)

    # ── الحالة وحوكمة الإقفال ────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',    'مفتوحة'),
        ('closed',   'مُقفَلة'),
        ('audited',  'مراجَعة'),
        ('archived', 'مؤرشفة'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    closed_by = fields.Many2one('res.users', string='أقفل بواسطة', readonly=True)
    closed_date = fields.Datetime(string='تاريخ الإقفال', readonly=True)
    crossout_signed_by = fields.Char(string='موظف الشطب (توقيع)')
    accounts_head_signed_by = fields.Char(string='رئيس الحسابات (توقيع)')

    previous_folio_id = fields.Many2one('port_said.revenue.folio',
        string='الفولية السابقة', readonly=True)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('uniq_folio_per_book_period',
         'UNIQUE(book_id, fiscal_year, period_month, company_id)',
         'لا يجوز إنشاء أكثر من فولية واحدة لنفس (الدفتر، السنة، الشهر).'),
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

    # ── Compute Period Totals ────────────────────────────────────────────────
    @api.depends('book_id', 'date_from', 'date_to', 'opening_carryforward', 'state')
    def _compute_period_totals(self):
        for folio in self:
            lines = folio._fetch_lines()
            # للإيرادات: المبلغ = credit - debit (الإيرادات في الجانب الدائن طبيعياً)
            # للمصروفات: المبلغ = debit - credit
            # للكلاهما: نضيف القيم الموجبة فقط
            total = 0.0
            if folio.book_id.direction == 'expenses':
                total = sum(lines.mapped('debit')) - sum(lines.mapped('credit'))
            elif folio.book_id.direction == 'revenues':
                total = sum(lines.mapped('credit')) - sum(lines.mapped('debit'))
            else:  # both / settlements
                total = sum(lines.mapped('debit')) + sum(lines.mapped('credit'))
            folio.period_total = total
            folio.line_count = len(lines)
            folio.closing_carryforward = folio.opening_carryforward + total

    # ── Compute Matrix ───────────────────────────────────────────────────────
    @api.depends('book_id', 'date_from', 'date_to', 'budget_plan_id')
    def _compute_matrix(self):
        """يبني مصفوفة (day → budget_code → amount) من السطور المحاسبية.
        يُستخدم في القالب form10 cross-tab."""
        for folio in self:
            lines = folio._fetch_lines()
            level = folio.book_id.grouping_level

            matrix = defaultdict(lambda: defaultdict(float))
            columns_seen = set()

            for line in lines:
                # استخراج كود الميزانية حسب المستوى
                code = folio._extract_budget_code(line, level)
                if not code:
                    code = '__unspec__'
                # المبلغ حسب اتجاه الدفتر
                if folio.book_id.direction == 'expenses':
                    amt = line.debit - line.credit
                elif folio.book_id.direction == 'revenues':
                    amt = line.credit - line.debit
                else:
                    amt = line.debit + line.credit
                day_key = line.date.isoformat()
                matrix[day_key][code] += amt
                columns_seen.add(code)

            # ترتيب الأعمدة: ترتيب أبجدي على الأكواد
            ordered_columns = sorted(columns_seen)

            # أضف أي بنود موجودة في budget_plan_id حتى لو لم تكن مستخدَمة
            if folio.budget_plan_id:
                plan_codes = set()
                for bl in folio.budget_plan_id.line_ids:
                    if level == 'bab':
                        plan_codes.add(bl.bab or '')
                    elif level == 'fasle':
                        plan_codes.add('%s%s' % (bl.bab or '', bl.fasle or ''))
                    else:
                        plan_codes.add(bl.full_code or '')
                ordered_columns = sorted(set(ordered_columns) | plan_codes)
                ordered_columns = [c for c in ordered_columns if c]

            folio.matrix_json = json.dumps({k: dict(v) for k, v in matrix.items()},
                                            ensure_ascii=False)
            folio.matrix_columns_json = json.dumps(ordered_columns, ensure_ascii=False)

    def _extract_budget_code(self, line, level):
        """يستخرج كود الميزانية من السطر المحاسبي.
        المصدر بالأولوية:
        1. الحقل التحليلي analytic_distribution إن كان مرتبطاً ببند موازنة
        2. حقل ref على القيد إن كان يحوي كوداً منسَّقاً مثل '4/01/02'
        3. كود الحساب (account.code) كآخر ملاذ"""
        # المحاولة 1: الحقل التحليلي
        if line.analytic_distribution:
            for analytic_id in line.analytic_distribution.keys():
                # البحث عن budget.line مرتبط بالحساب التحليلي
                bl = self.env['port_said.budget.line'].search([
                    ('dimension_id', '=', int(analytic_id))
                ], limit=1)
                if bl:
                    if level == 'bab':
                        return bl.bab or ''
                    elif level == 'fasle':
                        return '%s%s' % (bl.bab or '', bl.fasle or '')
                    else:
                        return bl.full_code or ''
        # المحاولة 2: ref على account.move
        ref = line.move_id.ref or ''
        if '/' in ref:
            parts = ref.split('/')
            if len(parts) >= 1 and parts[0].isdigit():
                if level == 'bab':
                    return parts[0]
                elif level == 'fasle' and len(parts) >= 2:
                    return ''.join(parts[:2])
                elif level == 'full_code':
                    return ''.join(parts)
        # المحاولة 3: account.code
        if line.account_id and line.account_id.code:
            ac = line.account_id.code
            if level == 'bab':
                return ac[:1]
            elif level == 'fasle':
                return ac[:4]
            else:
                return ac
        return ''

    def _fetch_lines(self):
        """دومين القراءة على account.move.line."""
        self.ensure_one()
        if not (self.book_id and self.date_from and self.date_to):
            return self.env['account.move.line']

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id),
        ]
        if not self.book_id.include_unposted:
            domain.append(('parent_state', '=', 'posted'))
        if self.book_id.journal_ids:
            domain.append(('journal_id', 'in', self.book_id.journal_ids.ids))

        # فلترة حسب نطاق الباب
        # نتطلب أن يبدأ كود الحساب أو ref بأحد الأرقام في النطاق
        try:
            f = int(self.book_id.bab_range_from)
            t = int(self.book_id.bab_range_to)
            allowed_babs = [str(b) for b in range(f, t + 1)]
        except (ValueError, TypeError):
            allowed_babs = []

        lines = self.env['account.move.line'].search(domain, order='date, id')

        if allowed_babs:
            # فلترة في Python (account.code prefix أو ref prefix)
            filtered = []
            for line in lines:
                code = line.account_id.code or ''
                ref = line.move_id.ref or ''
                bab_from_code = code[:1] if code else ''
                bab_from_ref = ref.split('/')[0] if '/' in ref else ''
                if bab_from_code in allowed_babs or bab_from_ref in allowed_babs:
                    filtered.append(line.id)
            return self.env['account.move.line'].browse(filtered)

        return lines

    # ── إنشاء الرقم القانوني وحساب الترحيل ──────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('folio_number'):
                book = self.env['port_said.revenue.book'].browse(vals['book_id'])
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
            ('fiscal_year', '=', self.fiscal_year),
            ('date_to', '<', self.date_from),
            ('state', 'in', ['closed', 'audited', 'archived']),
            ('id', '!=', self.id),
        ]
        prev = self.search(domain, order='date_to desc', limit=1)
        if prev:
            self.previous_folio_id = prev.id
            self.opening_carryforward = prev.closing_carryforward
        else:
            # أول فولية في السنة المالية: opening = 0
            self.opening_carryforward = 0.0

    # ── إعادة الحساب يدوياً ─────────────────────────────────────────────────
    def action_recompute(self):
        for rec in self:
            if rec.state in ('audited', 'archived'):
                raise UserError(_(
                    'لا يجوز إعادة حساب فولية مراجَعة أو مؤرشفة.'))
            rec._compute_period_totals()
            rec._compute_matrix()
            rec.message_post(body=_(
                'أُعيد حساب الأرصدة. الإجمالي الجديد: %s'
            ) % rec.period_total)
        return True

    # ── إقفال شهري ───────────────────────────────────────────────────────────
    def action_close(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الفولية رقم %s ليست مفتوحة.') % rec.folio_number)
            if not rec.crossout_signed_by:
                raise UserError(_(
                    'يجب توقيع موظف الشطب قبل الإقفال (الفولية %s).'
                ) % rec.folio_number)
            rec.write({
                'state': 'closed',
                'closed_by': self.env.user.id,
                'closed_date': fields.Datetime.now(),
            })
            rec.message_post(body=_(
                'أُقفلت الفولية. نقل بعده: %s') % rec.closing_carryforward)
        return True

    def action_audit(self):
        for rec in self:
            if rec.state != 'closed':
                raise UserError(_('يجب إقفال الفولية أولاً.'))
            if not rec.accounts_head_signed_by:
                raise UserError(_('يجب توقيع رئيس الحسابات قبل اعتماد المراجعة.'))
            rec.state = 'audited'
        return True

    def action_reopen(self):
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('إعادة فتح الفولية تتطلب صلاحية مدير حسابات.'))
        for rec in self:
            rec.state = 'draft'
            rec.message_post(body=_(
                'أُعيد فتح الفولية بواسطة %s — يُلزم تسجيل سبب.'
            ) % self.env.user.name)
        return True

    # ── الحماية ضد التعديل بعد الإقفال ──────────────────────────────────────
    def write(self, vals):
        protected_fields = {'date_from', 'date_to', 'book_id', 'fiscal_year',
                           'period_month', 'opening_carryforward'}
        if any(f in vals for f in protected_fields):
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
                    'لا يجوز حذف فولية تحتوي %d سطر.') % rec.line_count)
        return super().unlink()

    # ── مساعد الطباعة (Cross-tab form 10) ───────────────────────────────────
    def _get_matrix_for_print(self):
        """يحوِّل matrix_json إلى بنية مرتَّبة للاستخدام في QWeb form10.
        يعيد dict بالبنية:
        {
          'columns': [list of budget codes ordered],
          'column_labels': {code: label},
          'rows': [
            {'day': 'YYYY-MM-DD', 'values': {code: amount}, 'day_total': x},
            ...
          ],
          'column_totals': {code: x},
          'grand_total': x,
        }"""
        self.ensure_one()
        import json as _json
        try:
            matrix = _json.loads(self.matrix_json or '{}')
            columns = _json.loads(self.matrix_columns_json or '[]')
        except (ValueError, TypeError):
            matrix, columns = {}, []

        # تسميات الأعمدة: ابحث عن budget.line للحصول على الوصف
        column_labels = {}
        for code in columns:
            if code == '__unspec__':
                column_labels[code] = _('غير محدَّد')
                continue
            bl = self._find_budget_line_by_code(code)
            column_labels[code] = bl.description if bl else code

        # ترتيب الصفوف زمنياً
        days = sorted(matrix.keys())
        rows = []
        column_totals = {c: 0.0 for c in columns}
        grand_total = 0.0
        for day in days:
            day_values = matrix.get(day, {})
            day_total = 0.0
            for code in columns:
                v = day_values.get(code, 0.0)
                column_totals[code] += v
                day_total += v
            grand_total += day_total
            rows.append({
                'day': day,
                'values': {c: day_values.get(c, 0.0) for c in columns},
                'day_total': day_total,
            })

        return {
            'columns': columns,
            'column_labels': column_labels,
            'rows': rows,
            'column_totals': column_totals,
            'grand_total': grand_total,
        }

    def _find_budget_line_by_code(self, code):
        """يبحث عن port_said.budget.line مطابق للكود حسب مستوى التجميع."""
        self.ensure_one()
        BL = self.env['port_said.budget.line']
        level = self.book_id.grouping_level
        if level == 'bab':
            return BL.search([('bab', '=', code)], limit=1)
        elif level == 'fasle':
            # code = bab+fasle concatenated
            if len(code) >= 3:
                return BL.search([
                    ('bab', '=', code[:1]),
                    ('fasle', '=', code[1:]),
                ], limit=1)
        else:  # full_code
            return BL.search([('full_code', '=', code)], limit=1)
        return BL.browse()

    # ── Cron Jobs ────────────────────────────────────────────────────────────
    @api.model
    def cron_recompute_open_folios(self):
        """يومي: إعادة حساب الفوليوهات المفتوحة."""
        open_folios = self.search([('state', '=', 'draft')])
        for folio in open_folios:
            try:
                folio._compute_period_totals()
                folio._compute_matrix()
            except Exception as e:
                folio.message_post(body=_('فشل إعادة الحساب: %s') % str(e))
        return len(open_folios)

    @api.model
    def cron_generate_monthly_folios(self):
        """شهري: إنشاء فولية الشهر السابق لكل دفتر نشط."""
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

        Book = self.env['port_said.revenue.book'].search([])
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
