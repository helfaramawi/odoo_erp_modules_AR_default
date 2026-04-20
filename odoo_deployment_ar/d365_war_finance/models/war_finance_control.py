from odoo import fields, models


class WarFinanceControl(models.Model):
    _name = 'war.finance.control'
    _description = 'War Finance Control'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    journal_threshold = fields.Monetary(required=True, default=0.0)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, readonly=True)
    active = fields.Boolean(default=True)
