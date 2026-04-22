from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    x_contract_price_id = fields.Many2one(
        "contract.price", string="Contract / العقد", readonly=True, copy=False)
    x_contract_price_applied = fields.Boolean(
        string="Contract Price Applied / تم تطبيق سعر العقد", readonly=True, copy=False)

    @api.onchange("product_id")
    def _onchange_product_contract_price(self):
        if not self.product_id or not self.order_id.partner_id:
            return
        date = self.order_id.date_order.date() if self.order_id.date_order else fields.Date.today()
        ContractPrice = self.env["contract.price"]
        price = ContractPrice.get_contract_price(
            self.order_id.partner_id.id, self.product_id.id, date, self.company_id.id)
        if price is not None:
            contract = ContractPrice.search([
                ("partner_id","=",self.order_id.partner_id.id),
                ("product_id","=",self.product_id.id),
                ("date_start","<=",date),("date_end",">=",date),("active","=",True),
            ], limit=1)
            self.price_unit = price
            self.x_contract_price_id = contract
            self.x_contract_price_applied = True
