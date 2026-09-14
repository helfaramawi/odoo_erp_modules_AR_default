# -*- coding: utf-8 -*-
from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        engine = self.env['port_said.vendor.performance.engine'].sudo()
        for picking in self:
            try:
                if picking.picking_type_code == 'incoming' and picking.purchase_id and picking.purchase_id.partner_id:
                    period = fields.Date.to_date(picking.date_done) if picking.date_done else fields.Date.today()
                    engine.compute_vendor_score(picking.purchase_id.partner_id, period)
            except Exception as exc:
                picking.message_post(body='فشل تحديث تقييم كفاءة المورد بعد الاستلام: %s' % exc)
        return res
