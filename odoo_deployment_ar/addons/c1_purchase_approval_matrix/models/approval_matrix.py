from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseApprovalThreshold(models.Model):
    _name = 'purchase.approval.threshold'
    _description = 'Purchase Approval Threshold'
    _order = 'tier asc'

    name = fields.Char(string='Name', required=True)
    tier = fields.Selection([
        ('1', 'Tier 1'),
        ('2', 'Tier 2'),
        ('3', 'Tier 3'),
    ], string='Tier', required=True)
    min_amount = fields.Monetary(string='Min Amount', currency_field='currency_id', required=True)
    max_amount = fields.Monetary(string='Max Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    approver_ids = fields.Many2many('res.users', string='Approvers', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def get_approvers_for_amount(self, amount, company_id=None):
        domain = [('min_amount', '<=', amount), ('active', '=', True)]
        if company_id:
            domain.append(('company_id', '=', company_id))
        thresholds = self.search(domain, order='tier asc')
        return thresholds.filtered(lambda t: not t.max_amount or t.max_amount >= amount)


class PurchaseApprovalLog(models.Model):
    _name = 'purchase.approval.log'
    _description = 'Purchase Approval Log'
    _order = 'create_date desc'

    purchase_id = fields.Many2one('purchase.order', required=True, ondelete='cascade', index=True)
    tier = fields.Char(string='Tier')
    action = fields.Selection([
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reset', 'Reset'),
    ], required=True)
    user_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user)
    comment = fields.Text(string='Comment')
