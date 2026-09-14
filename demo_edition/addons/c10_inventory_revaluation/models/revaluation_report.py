from odoo import models, fields, api, _
from datetime import date
from dateutil.relativedelta import relativedelta


class InventoryRevaluationWizard(models.TransientModel):
    _name = "inventory.revaluation.wizard"
    _description = "معالج تقرير إعادة تقييم المخزون"

    as_of_date = fields.Date(string="حتى تاريخ", required=True, default=fields.Date.today)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True)
    location_ids = fields.Many2many("stock.location",
        domain="[('usage','=','internal')]",
        string="المواقع")
    show_zero_qty = fields.Boolean(string="إظهار الكميات الصفرية", default=False)

    def action_print_report(self):
        return self.env.ref("c10_inventory_revaluation.action_report_revaluation").report_action(self)

    def _get_revaluation_data(self):
        as_of = self.as_of_date or date.today()
        company = self.company_id

        # فلتر على internal locations فقط
        domain = [
            ("company_id", "=", company.id),
            ("location_id.usage", "=", "internal"),
        ]
        if self.location_ids:
            domain.append(("location_id", "in", self.location_ids.ids))

        quants = self.env["stock.quant"].search(domain)

        # جمّع حسب المنتج
        product_data = {}
        for q in quants:
            pid = q.product_id.id
            if pid not in product_data:
                product_data[pid] = {
                    "product_obj": q.product_id,
                    "qty": 0.0,
                }
            product_data[pid]["qty"] += q.quantity

        result = []
        for pid, data in product_data.items():
            product = data["product_obj"]
            qty = data["qty"]
            cost = product.standard_price
            current_value = qty * cost

            if not self.show_zero_qty and abs(current_value) < 0.01:
                continue

            result.append({
                "product": product.display_name,
                "category": product.categ_id.complete_name,
                "qty": qty,
                "uom": product.uom_id.name,
                "cost": cost,
                "current_value": current_value,
                "prior_value": 0.0,
                "variance": 0.0,
            })

        return sorted(result, key=lambda x: (x["category"], x["product"]))
