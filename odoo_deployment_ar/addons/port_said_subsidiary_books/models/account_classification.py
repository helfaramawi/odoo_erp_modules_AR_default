# -*- coding: utf-8 -*-
"""
تصنيف الحسابات الحكومية (Account Classification)
=================================================

الجسر بين دليل الحسابات الموحد للوحدات الحكومية المصرية وبين الدفاتر المساعدة.
كل حساب في account.account ينتمي إلى تصنيف واحد، وكل تصنيف يظهر في دفتر واحد أو أكثر.

التصنيفات المعرّفة افتراضياً (data/account_classification_data.xml):
- CUR_DR  : حسابات جارية مدينة (Receivables, Advances, Imprest)
- CUR_CR  : حسابات جارية دائنة (Payables, Withholdings, Accruals)
- MEMO_DR : حسابات نظامية مدينة (Commitments outstanding, Allotments)
- MEMO_CR : حسابات نظامية دائنة (Contingent liabilities, Bank guarantees received)
- PERSONAL: حسابات شخصية (Specific named-person accounts — Form 29)
"""
from odoo import models, fields, api


class SubsidiaryAccountClassification(models.Model):
    _name = 'port_said.subsidiary.account.classification'
    _description = 'تصنيف الحسابات للدفاتر المساعدة'
    _order = 'sequence, code'

    name = fields.Char(string='الاسم', required=True, translate=False)
    code = fields.Char(string='الكود', required=True, index=True)
    sequence = fields.Integer(string='الترتيب', default=10)

    nature = fields.Selection([
        ('current', 'جارية (Current)'),
        ('memo',    'نظامية (Memorandum)'),
        ('personal','شخصية (Personal)'),
    ], string='الطبيعة', required=True, default='current')

    natural_side = fields.Selection([
        ('debit',  'مدين بطبيعته'),
        ('credit', 'دائن بطبيعته'),
    ], string='الطبيعة الرصيدية', required=True, default='debit')

    description = fields.Text(string='الوصف القانوني',
        help='شرح طبيعة هذا التصنيف وفق دليل الحسابات الموحد للوحدات الحكومية '
             'الصادر من وزارة المالية المصرية.')

    coa_code_prefix = fields.Char(string='بداية كود دليل الحسابات',
        help='يُستخدم في الإسناد التلقائي: كل account.account يبدأ كوده بهذه البداية '
             'يُسند تلقائياً إلى هذا التصنيف. مثلاً: 12 = حسابات جارية مدينة.')

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    account_count = fields.Integer(string='عدد الحسابات المسندة',
                                    compute='_compute_account_count')

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code, company_id)',
         'كود التصنيف يجب أن يكون فريداً.'),
    ]

    def _compute_account_count(self):
        Account = self.env['account.account']
        for rec in self:
            rec.account_count = Account.search_count([
                ('x_subsidiary_classification_id', '=', rec.id)
            ])

    def action_open_accounts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'account.account',
            'view_mode': 'list,form',
            'domain': [('x_subsidiary_classification_id', '=', self.id)],
        }

    def action_auto_assign_by_prefix(self):
        """يُسند كل الحسابات التي تبدأ بـ coa_code_prefix إلى هذا التصنيف."""
        Account = self.env['account.account']
        for rec in self:
            if not rec.coa_code_prefix:
                continue
            accounts = Account.search([('code', '=like', rec.coa_code_prefix + '%')])
            accounts.write({'x_subsidiary_classification_id': rec.id})
        return True
