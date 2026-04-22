# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date


class AcctReportWizard(models.TransientModel):
    """
    ويزارد التقارير المحاسبية الحكومية
    ميزان المراجعة + كشف حساب مورد/عميل
    """
    _name = 'port_said.acct.report.wizard'
    _description = 'التقارير المحاسبية الحكومية'

    report_type = fields.Selection([
        ('trial_balance',  'ميزان المراجعة الحكومي'),
        ('partner_ledger', 'كشف حساب مورد / عميل'),
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
    company_id = fields.Many2one(
        'res.company', default=lambda s: s.env.company,
    )

    # فلاتر ميزان المراجعة
    hide_zero_balance = fields.Boolean(
        string='إخفاء الأرصدة الصفرية', default=True,
    )
    account_ids = fields.Many2many(
        'account.account', string='حسابات محددة (فارغ = الكل)',
    )

    # فلاتر كشف الحساب
    partner_type = fields.Selection([
        ('supplier', 'موردون'),
        ('customer', 'عملاء'),
        ('all',      'الكل'),
    ], string='نوع الشركاء', default='supplier')
    partner_ids = fields.Many2many(
        'res.partner', string='شركاء محددون (فارغ = الكل)',
    )

    def _get_trial_balance_data(self):
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('parent_state', '=', 'posted'),
        ]
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))

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
                'debit': debit,
                'credit': credit,
                'balance': balance,
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
            domain, ['partner_id', 'debit', 'credit'], ['partner_id'],
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
        return sorted(result, key=lambda x: x['partner_name'])

    def action_print(self):
        if self.report_type == 'trial_balance':
            return self.env.ref(
                'port_said_acct_reports.action_rpt_acct_trial_balance'
            ).report_action(self)
        else:
            return self.env.ref(
                'port_said_acct_reports.action_rpt_acct_partner_ledger'
            ).report_action(self)
