from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PaymentScheduleLine(models.Model):
    """سطر جدول الدفعات — Lease Payment Installment"""
    _name = 'payment.schedule.line'
    _description = 'دفعة إيجار - Lease Payment Installment'
    _order = 'due_date asc, installment_number asc'

    lease_contract_id = fields.Many2one(
        'auction.lease.contract', string='العقد',
        required=True, ondelete='cascade', index=True,
    )
    installment_number = fields.Integer(string='رقم الدفعة', required=True)
    year_number        = fields.Integer(string='السنة')
    due_date           = fields.Date(string='تاريخ الاستحقاق', required=True)
    amount             = fields.Float(string='المبلغ المستحق', digits='Account', required=True)
    amount_paid        = fields.Float(string='المبلغ المحصل',  digits='Account', default=0.0)
    amount_outstanding = fields.Float(
        string='المتبقي', compute='_compute_outstanding',
        store=True, digits='Account',
    )
    payment_date  = fields.Date(string='تاريخ التحصيل')
    receipt_ref   = fields.Char(string='رقم الإيصال')
    state = fields.Selection([
        ('pending',  'قيد الانتظار'),
        ('partial',  'مدفوع جزئياً'),
        ('paid',     'مدفوع'),
        ('overdue',  'متأخر'),
    ], default='pending', string='الحالة')
    notes = fields.Text(string='ملاحظات')

    _sql_constraints = [
        ('amount_positive',  'CHECK(amount > 0)',        'مبلغ الدفعة يجب أن يكون موجباً'),
        ('paid_not_exceed',  'CHECK(amount_paid <= amount)',
         'المبلغ المحصل لا يمكن أن يتجاوز المبلغ المستحق'),
    ]

    @api.depends('amount', 'amount_paid')
    def _compute_outstanding(self):
        for rec in self:
            rec.amount_outstanding = rec.amount - rec.amount_paid

    def action_mark_paid(self):
        for rec in self:
            rec.write({
                'amount_paid':   rec.amount,
                'state':         'paid',
                'payment_date':  fields.Date.context_today(self),
            })

    def action_mark_overdue(self):
        for rec in self:
            if rec.state in ('pending', 'partial'):
                rec.write({'state': 'overdue'})

    @api.model
    def _cron_update_overdue(self):
        today = fields.Date.context_today(self)
        overdue = self.search([
            ('due_date', '<', today),
            ('state', 'in', ['pending', 'partial']),
        ])
        overdue.write({'state': 'overdue'})
