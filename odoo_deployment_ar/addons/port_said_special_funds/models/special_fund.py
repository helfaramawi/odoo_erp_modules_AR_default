from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SpecialFund(models.Model):
    """
    الصندوق الخاص - وحدة الصناديق والحسابات الخاصة (FR-S-01/02)
    HARD CONSTRAINT: Fund balances CANNOT be mixed — financial violation.
    """
    _name = 'port_said.special_fund'
    _description = 'الصندوق الخاص (وحدة الصناديق والحسابات الخاصة)'
    _inherit = ['mail.thread']
    _rec_name = 'name_ar'

    name_ar          = fields.Char(string='اسم الصندوق', required=True)
    fund_code        = fields.Char(string='رمز الصندوق', required=True, index=True)
    fund_type        = fields.Selection([
        ('service_fees',  'رسوم الخدمات'),
        ('rentals',       'إيجارات'),
        ('donations',     'تبرعات وهبات'),
        ('grants',        'منح'),
        ('other',         'أخرى'),
    ], string='نوع الصندوق', required=True)

    responsible_manager_id = fields.Many2one('res.users', string='المدير المسؤول')
    bank_account_no        = fields.Char(string='رقم الحساب البنكي')
    bank_name              = fields.Char(string='اسم البنك')
    account_id             = fields.Many2one('account.account', string='حساب دفتر الأستاذ')

    budget_approved        = fields.Monetary(string='الاعتمادات المعتمدة', currency_field='currency_id')
    current_balance        = fields.Monetary(
        string='الرصيد الحالي', compute='_compute_balance', store=True,
        currency_field='currency_id',
    )
    total_revenue          = fields.Monetary(
        string='إجمالي الإيرادات', compute='_compute_balance', store=True,
        currency_field='currency_id',
    )
    total_expenditure      = fields.Monetary(
        string='إجمالي المصروفات', compute='_compute_balance', store=True,
        currency_field='currency_id',
    )
    currency_id            = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    active                 = fields.Boolean(default=True)
    notes                  = fields.Text(string='ملاحظات')
    transaction_ids        = fields.One2many('port_said.fund_transaction', 'fund_id', string='المعاملات')

    _sql_constraints = [
        ('unique_code', 'UNIQUE(fund_code)', 'رمز الصندوق يجب أن يكون فريداً.'),
    ]

    @api.depends('transaction_ids.amount', 'transaction_ids.transaction_type', 'transaction_ids.state')
    def _compute_balance(self):
        for fund in self:
            posted_txns = fund.transaction_ids.filtered(lambda t: t.state == 'posted')
            revenue = sum(posted_txns.filtered(lambda t: t.transaction_type == 'revenue').mapped('amount'))
            expense = sum(posted_txns.filtered(lambda t: t.transaction_type == 'expense').mapped('amount'))
            fund.total_revenue      = revenue
            fund.total_expenditure  = expense
            fund.current_balance    = revenue - expense

    def check_disbursement_allowed(self, amount):
        """Raise if fund has insufficient balance for disbursement."""
        self.ensure_one()
        if amount > self.current_balance:
            raise ValidationError(_(
                'الرصيد غير كافٍ في الصندوق "%(fund)s".\n'
                'المبلغ المطلوب: %(req)s | الرصيد المتاح: %(bal)s\n'
                'لا يمكن الخلط بين أرصدة الصناديق — يُعد ذلك مخالفة مالية.',
                fund=self.name_ar, req=amount, bal=self.current_balance,
            ))
