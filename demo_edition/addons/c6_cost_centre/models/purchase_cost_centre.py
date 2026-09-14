from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    x_cost_centre_id = fields.Many2one(
        'financial.dimension',
        string='Cost Centre',
        domain=[('dimension_type', '=', 'department')],
    )
