from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ContractPrice(models.Model):
    _name = "contract.price"
    _description = "Contract Price / سعر العقد"
    _order = "partner_id, product_id, date_start"

    name = fields.Char(string="Contract Ref / مرجع العقد", required=True)
    partner_id = fields.Many2one("res.partner", string="Customer / العميل", required=True, index=True)
    product_id = fields.Many2one("product.product", string="Product / المنتج", required=True, index=True)
    price = fields.Float(string="Contract Price / سعر العقد", required=True, digits="Product Price")
    currency_id = fields.Many2one("res.currency", string="Currency / العملة",
        default=lambda self: self.env.company.currency_id)
    date_start = fields.Date(string="Start Date / تاريخ البداية", required=True)
    date_end = fields.Date(string="End Date / تاريخ النهاية", required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    notes = fields.Text(string="Notes / ملاحظات")

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_end <= rec.date_start:
                raise ValidationError(_("End date must be after start date."))

    @api.constrains("partner_id", "product_id", "date_start", "date_end")
    def _check_no_overlap(self):
        for rec in self:
            overlap = self.search([
                ("id", "!=", rec.id),
                ("partner_id", "=", rec.partner_id.id),
                ("product_id", "=", rec.product_id.id),
                ("active", "=", True),
                ("date_start", "<", rec.date_end),
                ("date_end", ">", rec.date_start),
            ])
            if overlap:
                raise ValidationError(
                    _("Contract price overlaps with existing record: %s") % overlap[0].name)

    def get_contract_price(self, partner_id, product_id, date, company_id=None):
        domain = [
            ("partner_id", "=", partner_id),
            ("product_id", "=", product_id),
            ("date_start", "<=", date),
            ("date_end", ">=", date),
            ("active", "=", True),
        ]
        if company_id:
            domain.append(("company_id", "=", company_id))
        record = self.search(domain, limit=1)
        return record.price if record else None
