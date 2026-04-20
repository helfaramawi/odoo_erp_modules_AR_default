# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date


class GlReportWizard(models.TransientModel):
    """
    ويزارد التقارير المحاسبية الحكومية
    - ميزان المراجعة الحكومي
    - كشف حساب مورد / عميل
    - تقرير دفتر الأستاذ العام
    """
    _name = 'port_said.gl.report.wizard'
    _description = 'ويزارد التقارير المحاسبية'

    report_type = fields.Selection([
        ('trial_balance',   'ميزان المراجعة الحكومي'),
        ('partner_ledger',  'كشف حساب مورد / عميل'),
        ('general_ledger',  'دفتر الأستاذ العام'),
        ('chart_of_accounts', 'شجرة الحسابات المصرية'),
    ], string='نوع التقرير', required=True, default='trial_balance')

    date_from = fields.Date(
        string='من تاريخ', required=True,
        default=lambda self: date(date.today().year, 1, 1),
    )
    date_to = fields.Date(
        string='إلى تاريخ', required=True,
        default=fields.Date.context_today,
    )
    fiscal_year = fields.Char(
        string='السنة المالية',
        default=lambda self: str(date.today().year),
    )

    # فلاتر ميزان المراجعة
    account_ids = fields.Many2many(
        'account.account', string='الحسابات (اتركها فارغة للكل)',
    )
    account_type_filter = fields.Selection([
        ('all',       'جميع الحسابات'),
        ('asset',     'الأصول فقط'),
        ('liability', 'الخصوم فقط'),
        ('income',    'الإيرادات فقط'),
        ('expense',   'المصروفات فقط'),
    ], string='تصفية حسب النوع', default='all')
    hide_zero_balance = fields.Boolean(
        string='إخفاء الحسابات ذات الرصيد صفر', default=True,
    )

    # فلاتر كشف الحساب
    partner_ids = fields.Many2many(
        'res.partner', string='الموردون / العملاء (فارغ = الكل)',
    )
    partner_type = fields.Selection([
        ('supplier', 'موردون فقط'),
        ('customer', 'عملاء فقط'),
        ('all',      'الكل'),
    ], string='نوع الشركاء', default='supplier')

    # فلاتر الأستاذ العام
    journal_ids = fields.Many2many(
        'account.journal', string='الدفاتر (فارغ = الكل)',
    )

    company_id = fields.Many2one(
        'res.company', default=lambda s: s.env.company,
    )

    # ── دوال استخراج البيانات ────────────────────────────────────

    def _get_trial_balance_data(self):
        """استخراج بيانات ميزان المراجعة"""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
        ]
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))

        type_map = {
            'asset':     ['asset_fixed', 'asset_receivable', 'asset_cash',
                          'asset_current', 'asset_prepayments', 'asset_non_current'],
            'liability': ['liability_payable', 'liability_credit_card',
                          'liability_current', 'liability_non_current'],
            'income':    ['income', 'income_other'],
            'expense':   ['expense', 'expense_depreciation', 'expense_direct_cost'],
        }
        if self.account_type_filter != 'all':
            types = type_map.get(self.account_type_filter, [])
            if types:
                domain.append(('account_id.account_type', 'in', types))

        lines = self.env['account.move.line'].read_group(
            domain,
            ['account_id', 'debit', 'credit'],
            ['account_id'],
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
                'account_type': account.account_type,
                'debit': debit,
                'credit': credit,
                'balance': balance,
                'debit_balance': balance if balance > 0 else 0,
                'credit_balance': abs(balance) if balance < 0 else 0,
            })

        result.sort(key=lambda x: x['account_code'])
        return result

    def _get_partner_ledger_data(self):
        """استخراج بيانات كشف الحساب"""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
            ('partner_id', '!=', False),
        ]

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        if self.partner_type == 'supplier':
            domain.append(('account_id.account_type', '=', 'liability_payable'))
        elif self.partner_type == 'customer':
            domain.append(('account_id.account_type', '=', 'asset_receivable'))
        else:
            domain.append(('account_id.account_type', 'in',
                           ['liability_payable', 'asset_receivable']))

        lines = self.env['account.move.line'].read_group(
            domain,
            ['partner_id', 'debit', 'credit'],
            ['partner_id'],
        )

        result = []
        for line in lines:
            debit = line['debit'] or 0.0
            credit = line['credit'] or 0.0
            balance = debit - credit
            partner = self.env['res.partner'].browse(line['partner_id'][0])
            result.append({
                'partner_name': partner.name,
                'partner_vat': partner.vat or '',
                'debit': debit,
                'credit': credit,
                'balance': balance,
            })

        result.sort(key=lambda x: x['partner_name'])
        return result

    def _get_general_ledger_data(self):
        """استخراج بيانات دفتر الأستاذ العام"""
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
        ]
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))

        move_lines = self.env['account.move.line'].search(
            domain, order='account_id, date, id'
        )
        # Group by account
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


    def _get_chart_of_accounts_data(self):
        """استخراج شجرة الحسابات المصرية كاملة"""
        accounts = self.env['account.account'].search(
            [('company_id', '=', self.company_id.id)],
            order='code'
        )

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
            'expense_depreciation':  'اهلاك',
            'expense_direct_cost':   'تكلفة مباشرة',
            'off_balance':           'خارج الميزانية',
        }

        result = []
        for acc in accounts:
            # Get current balance
            move_lines = self.env['account.move.line'].search([
                ('account_id', '=', acc.id),
                ('parent_state', '=', 'posted'),
                ('date', '<=', self.date_to),
            ])
            debit = sum(move_lines.mapped('debit'))
            credit = sum(move_lines.mapped('credit'))
            balance = debit - credit

            result.append({
                'code':         acc.code,
                'name':         acc.name,
                'account_type': TYPE_LABELS.get(acc.account_type, acc.account_type),
                'currency':     acc.currency_id.name if acc.currency_id else '',
                'deprecated':   acc.deprecated,
                'debit':        debit,
                'credit':       credit,
                'balance':      balance,
                'level':        len(acc.code) - len(acc.code.lstrip('0123456789')) if acc.code else 0,
            })

        return result

    # ── Actions ──────────────────────────────────────────────────
    def action_print(self):
        report_map = {
            'trial_balance':  'port_said_gl_reports.rpt_trial_balance',
            'partner_ledger': 'port_said_gl_reports.rpt_partner_ledger',
            'general_ledger': 'port_said_gl_reports.rpt_general_ledger',
            'chart_of_accounts': 'port_said_gl_reports.rpt_chart_of_accounts',
        }
        ref = report_map.get(self.report_type)
        if not ref:
            raise UserError(_('نوع التقرير غير معروف'))
        return self.env.ref(ref).report_action(self)
