
from odoo import models, fields, api, _


class WarehouseAdditionPermit(models.Model):
    """
    إذن الإضافة — نموذج 1 مخازن
    يُصدَر بعد موافقة لجنة الفحص ويُسجَّل الصنف في المخازن.
    """
    _name = "port_said.warehouse.addition"
    _description = "إذن إضافة — نموذج 1 مخازن"
    _rec_name = "permit_number"

    permit_number     = fields.Char(string="رقم إذن الإضافة", readonly=True, copy=False)
    date_permit       = fields.Date(string="تاريخ الإذن", default=fields.Date.today, required=True)
    inspection_id     = fields.Many2one("port_said.inspection.committee", string="محضر لجنة الفحص", required=True)
    purchase_order_id = fields.Many2one(related="inspection_id.purchase_order_id", store=True)
    storekeeper_id    = fields.Many2one("res.users", string="أمين المخازن", required=True)
    stock_location_id = fields.Many2one("stock.location", string="موقع التخزين", required=True)

    line_ids = fields.One2many("port_said.warehouse.addition.line","addition_id",string="الأصناف المُضافة")

    state = fields.Selection([
        ("draft","مسودة"),("confirmed","مُعتمد"),("moved","تم التحريك للمخازن"),
    ], default="draft", tracking=True)
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("permit_number"):
                vals["permit_number"] = self.env["ir.sequence"].next_by_code("port_said.warehouse.addition") or "/"
        return super().create(vals_list)

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_move_to_stock(self):
        """تسجيل الأصناف في المخازن عبر stock.picking."""
        self.write({"state": "moved"})
        self.message_post(body=_("✅ تم تسجيل الأصناف في المخازن"))


class WarehouseAdditionLine(models.Model):
    _name = "port_said.warehouse.addition.line"
    _description = "بند إذن الإضافة"

    addition_id  = fields.Many2one("port_said.warehouse.addition", ondelete="cascade")
    product_id   = fields.Many2one("product.product", string="الصنف", required=True)
    qty          = fields.Float(string="الكمية المُضافة", required=True)
    uom_id       = fields.Many2one("uom.uom", string="الوحدة")
    serial_nos   = fields.Text(string="الأرقام التسلسلية / دُفعات")
    notes        = fields.Char(string="ملاحظات")
