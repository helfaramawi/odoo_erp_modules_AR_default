from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class PortSaidReportWizard(models.TransientModel):
    """
    معالج التقارير الحكومية الموحد
    يوفر واجهة موحدة لإصدار جميع التقارير الحكومية
    """
    _name = 'port_said.report.wizard'
    _description = 'معالج التقارير الحكومية — محافظة بورسعيد'

    report_type = fields.Selection([
        # ── تقارير الحسابات ─────────────────────────────────────
        ('daftar55_summary',      'تقرير ملخص دفتر 55 ع.ح — سجل الصرف'),
        ('daftar55_detail',       'كشف تفصيلي دفتر 55 ع.ح — كل القيود'),
        ('daftar224_daily',       'تقرير دفتر 224 ع.ح — السجل اليومي المزدوج'),
        ('deductions_summary',    'ملخص الاستقطاعات (دمغة — ضريبة)'),
        ('monthly_expenditure',   'كشف المصروفات الشهرية'),
        ('budget_execution',      'تقرير تنفيذ الموازنة — المقارنة'),
        ('commitment_status',     'كشف حالة الارتباطات والتسميح'),
        # ── تقارير المزادات ─────────────────────────────────────
        ('auction_results',       'نتائج المزادات — ملخص الترسية'),
        ('lease_collection',      'كشف تحصيل عقود الإيجار والانتفاع'),
        ('lease_overdue',         'كشف المتأخرات — عقود الإيجار'),
        # ── تقارير إدارية ───────────────────────────────────────
        ('payment_methods',       'توزيع المدفوعات حسب طريقة الصرف'),
        ('dept_expenditure',      'المصروفات حسب المصلحة / الإدارة'),
        # ── تقارير محاسبية ──────────────────────────────────────
        ('trial_balance',         'ميزان المراجعة الحكومي'),
        ('partner_ledger',        'كشف حساب مورد / عميل'),
        ('general_ledger',        'دفتر الأستاذ العام'),
        ('budget_summary',        'ملخص الموازنة التقديرية'),
        ('budget_variance',       'تقرير الانحرافات عن الموازنة'),
        ('budget_by_dept',        'تنفيذ الموازنة لكل إدارة'),
        ('aging_suppliers',       'تقرير أعمار الموردين'),
        ('aging_customers',       'تقرير أعمار العملاء'),
        ('cash_bank_movement',    'حركة الصندوق والبنك'),
        ('advances_register',     'سجل السلف القائمة والمتأخرة'),
        ('guarantees_register',   'سجل خطابات الضمان'),
        ('stock_valuation',       'كشف المخزون بالقيمة'),
        ('chart_of_accounts',     'دليل الحسابات المصرية — شجرة الحسابات'),
    ], string='نوع التقرير', required=True,
       default='daftar55_summary')

    date_from = fields.Date(
        string='من تاريخ',
        required=True,
        default=lambda self: date(date.today().year, 1, 1),
    )
    date_to = fields.Date(
        string='إلى تاريخ',
        required=True,
        default=fields.Date.today,
    )
    fiscal_year = fields.Char(
        string='السنة المالية',
        default=lambda self: str(date.today().year),
    )
    department_name = fields.Char(string='تصفية حسب المصلحة (اختياري)')
    budget_line = fields.Char(string='تصفية حسب البند (اختياري)')
    state_filter = fields.Selection([
        ('all',      'جميع الحالات'),
        ('draft',    'مسودة'),
        ('received', 'مستلم'),
        ('reviewed', 'تحت المراجعة'),
        ('cleared',  'مُسمَّح'),
        ('posted',   'مرحّل'),
        ('archived', 'محفوظ'),
    ], string='تصفية حسب الحالة', default='all')

    # ── فلاتر التقارير المحاسبية ─────────────────────────────
    hide_zero_balance = fields.Boolean(
        string='إخفاء الأرصدة الصفرية', default=True,
    )
    partner_type = fields.Selection([
        ('supplier', 'موردون'),
        ('customer', 'عملاء'),
        ('all',      'الكل'),
    ], string='نوع الشركاء', default='supplier')
    company_id = fields.Many2one(
        'res.company', string='الشركة',
        default=lambda s: s.env.company,
    )

    # ── بيانات محسوبة للتقارير ────────────────────────────────
    def _get_daftar55_records(self):
        domain = [
            ('date_received', '>=', self.date_from),
            ('date_received', '<=', self.date_to),
        ]
        if self.fiscal_year:
            domain.append(('fiscal_year', '=', self.fiscal_year))
        if self.department_name:
            domain.append(('department_name', 'ilike', self.department_name))
        if self.budget_line:
            domain.append(('budget_line', 'ilike', self.budget_line))
        if self.state_filter and self.state_filter != 'all':
            domain.append(('state', '=', self.state_filter))
        return self.env['port_said.daftar55'].search(domain, order='sequence_number asc')

    def _get_commitment_records(self):
        domain = [
            ('date_requested', '>=', self.date_from),
            ('date_requested', '<=', self.date_to),
        ]
        if self.fiscal_year:
            domain.append(('fiscal_year', '=', int(self.fiscal_year)))
        return self.env['port_said.commitment'].search(domain, order='commitment_number asc')

    def _get_daftar224_records(self):
        domain = [
            ('entry_date', '>=', self.date_from),
            ('entry_date', '<=', self.date_to),
        ]
        return self.env['port_said.daftar224'].search(domain, order='entry_date asc, sequence_in_day asc')

    def _get_auction_records(self):
        domain = [
            ('auction_date', '>=', str(self.date_from)),
            ('auction_date', '<=', str(self.date_to) + ' 23:59:59'),
        ]
        return self.env['auction.request'].search(domain, order='auction_date asc')

    def _get_lease_records(self):
        domain = [('state', 'in', ['active', 'expired'])]
        if self.date_from:
            domain.append(('start_date', '<=', self.date_to))
        return self.env['auction.lease.contract'].search(domain, order='start_date asc')

    # ── إصدار التقرير ─────────────────────────────────────────
    def _get_trial_balance_data(self):
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
        ]
        lines = self.env['account.move.line'].read_group(
            domain, ['account_id', 'debit', 'credit'], ['account_id'],
        )
        result = []
        for line in lines:
            debit = line['debit'] or 0.0
            credit = line['credit'] or 0.0
            balance = debit - credit
            if self.hide_zero_balance and abs(balance) < 0.01:
                continue
            account = self.env['account.account'].browse(line['account_id'][0])
            result.append({
                'account_code': account.code,
                'account_name': account.name,
                'debit': debit, 'credit': credit, 'balance': balance,
                'debit_balance': balance if balance > 0 else 0,
                'credit_balance': abs(balance) if balance < 0 else 0,
            })
        return sorted(result, key=lambda x: x['account_code'])

    def _get_partner_ledger_data(self):
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
            ('partner_id', '!=', False),
        ]
        if self.partner_type == 'supplier':
            domain.append(('account_id.account_type', '=', 'liability_payable'))
        elif self.partner_type == 'customer':
            domain.append(('account_id.account_type', '=', 'asset_receivable'))
        else:
            domain.append(('account_id.account_type', 'in',
                           ['liability_payable', 'asset_receivable']))
        lines = self.env['account.move.line'].read_group(
            domain, ['partner_id', 'debit', 'credit'], ['partner_id'],
        )
        result = []
        for line in lines:
            debit = line['debit'] or 0.0
            credit = line['credit'] or 0.0
            partner = self.env['res.partner'].browse(line['partner_id'][0])
            result.append({
                'partner_name': partner.name,
                'partner_vat': partner.vat or '',
                'debit': debit, 'credit': credit, 'balance': debit - credit,
            })
        return sorted(result, key=lambda x: x['partner_name'])

    def _get_general_ledger_data(self):
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
        ]
        move_lines = self.env['account.move.line'].search(
            domain, order='account_id, date, id'
        )
        accounts = {}
        for line in move_lines:
            acc_id = line.account_id.id
            if acc_id not in accounts:
                accounts[acc_id] = {
                    'account': line.account_id,
                    'lines': [],
                    'total_debit': 0.0,
                    'total_credit': 0.0,
                }
            accounts[acc_id]['lines'].append(line)
            accounts[acc_id]['total_debit'] += line.debit
            accounts[acc_id]['total_credit'] += line.credit
        return sorted(accounts.values(), key=lambda x: x['account'].code)

    def _get_budget_summary_data(self):
        plans = self.env['port_said.budget.plan'].search([
            ('fiscal_year', '=', int(self.fiscal_year)),
            ('state', 'in', ['approved', 'active', 'closed']),
        ])
        return plans

    def _get_budget_variance_data(self):
        return self.env['port_said.budget.plan'].search([
            ('fiscal_year', '=', int(self.fiscal_year)),
            ('state', 'in', ['approved', 'active', 'closed']),
        ])

    def _get_aging_data(self, partner_type):
        from datetime import date, timedelta
        today = date.today()
        buckets = [(0,30,'0-30 يوم'), (31,60,'31-60 يوم'),
                   (61,90,'61-90 يوم'), (91,180,'91-180 يوم'), (181,9999,'أكثر من 180 يوم')]
        acc_type = 'liability_payable' if partner_type == 'supplier' else 'asset_receivable'
        lines = self.env['account.move.line'].search([
            ('company_id', '=', self.company_id.id),
            ('account_id.account_type', '=', acc_type),
            ('parent_state', '=', 'posted'),
            ('reconciled', '=', False),
            ('partner_id', '!=', False),
        ])
        partners = {}
        for line in lines:
            pid = line.partner_id.id
            if pid not in partners:
                partners[pid] = {
                    'name': line.partner_id.name,
                    'buckets': {b[2]: 0.0 for b in buckets},
                    'total': 0.0,
                }
            bal = line.debit - line.credit
            days = (today - line.date_maturity).days if line.date_maturity else 0
            for lo, hi, label in buckets:
                if lo <= days <= hi:
                    partners[pid]['buckets'][label] += abs(bal)
                    break
            partners[pid]['total'] += abs(bal)
        result = sorted(partners.values(), key=lambda x: -x['total'])
        return {'rows': result, 'buckets': [b[2] for b in buckets]}

    def _get_cash_bank_data(self):
        journals = self.env['account.journal'].search([
            ('type', 'in', ['cash', 'bank']),
            ('company_id', '=', self.company_id.id),
        ])
        result = []
        for j in journals:
            lines = self.env['account.move.line'].search([
                ('journal_id', '=', j.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('parent_state', '=', 'posted'),
            ], order='date asc')
            total_in = sum(l.debit for l in lines)
            total_out = sum(l.credit for l in lines)
            result.append({
                'journal': j.name,
                'type': 'صندوق' if j.type == 'cash' else 'بنك',
                'lines': lines,
                'total_in': total_in,
                'total_out': total_out,
                'net': total_in - total_out,
            })
        return result

    def _get_advances_register_data(self):
        return self.env['port_said.advance'].search([
            ('state', 'in', ['disbursed', 'submitted', 'approved']),
        ], order='is_overdue desc, due_date asc')

    def _get_guarantees_register_data(self):
        return self.env['port_said.bank.guarantee'].search([
            ('state', 'in', ['active', 'extended']),
        ], order='expiry_date asc')

    def _get_stock_valuation_data(self):
        quants = self.env['stock.quant'].search([
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0),
        ])
        result = []
        for q in quants:
            result.append({
                'product_code': q.product_id.default_code or '',
                'product_name': q.product_id.name,
                'location': q.location_id.complete_name,
                'qty': q.quantity,
                'unit_cost': q.product_id.standard_price,
                'total_value': q.quantity * q.product_id.standard_price,
            })
        return sorted(result, key=lambda x: -x['total_value'])


    def _get_chart_of_accounts_data(self):
        """استخراج دليل الحسابات المصرية كاملاً"""
        TYPE_LABELS = {
            'asset_receivable':      'ذمم مدينة',
            'asset_cash':            'نقدية وبنوك',
            'asset_current':         'أصول متداولة',
            'asset_non_current':     'أصول غير متداولة',
            'asset_prepayments':     'مدفوعات مقدمة',
            'asset_fixed':           'أصول ثابتة',
            'liability_payable':     'ذمم دائنة',
            'liability_credit_card': 'بطاقات ائتمان',
            'liability_current':     'خصوم متداولة',
            'liability_non_current': 'خصوم غير متداولة',
            'equity':                'حقوق الملكية',
            'equity_unaffected':     'أرباح غير موزعة',
            'income':                'إيرادات',
            'income_other':          'إيرادات أخرى',
            'expense':               'مصروفات',
            'expense_depreciation':  'إهلاك',
            'expense_direct_cost':   'تكلفة مباشرة',
            'off_balance':           'خارج الميزانية',
        }
        accounts = self.env['account.account'].search(
            [('company_id', '=', self.company_id.id)],
            order='code'
        )
        # Single aggregation query instead of N+1
        totals_raw = self.env['account.move.line'].read_group(
            [
                ('account_id', 'in', accounts.ids),
                ('parent_state', '=', 'posted'),
                ('date', '<=', self.date_to),
            ],
            ['account_id', 'debit:sum', 'credit:sum'],
            ['account_id'],
        )
        totals_map = {t['account_id'][0]: t for t in totals_raw}

        result = []
        for acc in accounts:
            t = totals_map.get(acc.id, {})
            debit  = t.get('debit', 0.0) or 0.0
            credit = t.get('credit', 0.0) or 0.0
            result.append({
                'code':         acc.code,
                'name':         acc.name,
                'account_type': TYPE_LABELS.get(acc.account_type, acc.account_type),
                'currency':     acc.currency_id.name if acc.currency_id else 'EGP',
                'deprecated':   acc.deprecated,
                'debit':        debit,
                'credit':       credit,
                'balance':      debit - credit,
            })
        return result

    def action_print_report(self):
        self.ensure_one()

        # Map report_type to QWeb template name
        template_map = {
            'daftar55_summary':   'port_said_reports.rpt_daftar55_summary',
            'daftar55_detail':    'port_said_reports.rpt_daftar55_detail',
            'daftar224_daily':    'port_said_reports.rpt_daftar224_daily',
            'deductions_summary': 'port_said_reports.rpt_deductions_summary',
            'monthly_expenditure':'port_said_reports.rpt_monthly_expenditure',
            'budget_execution':   'port_said_reports.rpt_budget_execution',
            'commitment_status':  'port_said_reports.rpt_commitment_status',
            'auction_results':    'port_said_reports.rpt_auction_results',
            'lease_collection':   'port_said_reports.rpt_lease_collection',
            'lease_overdue':      'port_said_reports.rpt_lease_overdue',
            'payment_methods':    'port_said_reports.rpt_payment_methods',
            'dept_expenditure':   'port_said_reports.rpt_dept_expenditure',
            'trial_balance':      'port_said_reports.rpt_trial_balance',
            'partner_ledger':     'port_said_reports.rpt_partner_ledger',
            'general_ledger':     'port_said_reports.rpt_general_ledger',
            'budget_summary':     'port_said_reports.rpt_budget_summary_gov',
            'budget_variance':    'port_said_reports.rpt_budget_variance',
            'budget_by_dept':     'port_said_reports.rpt_budget_by_dept',
            'aging_suppliers':    'port_said_reports.rpt_aging_suppliers',
            'aging_customers':    'port_said_reports.rpt_aging_customers',
            'cash_bank_movement': 'port_said_reports.rpt_cash_bank',
            'advances_register':  'port_said_reports.rpt_advances_register_gov',
            'guarantees_register':'port_said_reports.rpt_guarantees_register_gov',
            'stock_valuation':    'port_said_reports.rpt_stock_valuation_gov',
            'chart_of_accounts':  'port_said_reports.rpt_chart_of_accounts_template',
        }

        report_name = template_map.get(self.report_type)
        if not report_name:
            raise UserError(_('نوع التقرير غير معروف'))

        # Try env.ref first, fall back to direct report generation
        try:
            # Build xmlid from report_name by finding matching action
            report = self.env['ir.actions.report'].search([
                ('report_name', '=', report_name),
                ('model', '=', self._name),
            ], limit=1)
            if report:
                return report.report_action(self)
        except Exception:
            pass

        # Direct fallback
        return {
            'type': 'ir.actions.report',
            'report_name': report_name,
            'report_type': 'qweb-pdf',
            'model': self._name,
            'res_id': self.id,
        }
