# -*- coding: utf-8 -*-
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super().button_confirm()
        engine = self.env['port_said.procurement.splitting.engine'].sudo()
        for po in self:
            try:
                engine.scan_purchase_order(po)
            except Exception as exc:
                po.message_post(body='فشل فحص تجزئة المشتريات: %s' % exc)
        return res
