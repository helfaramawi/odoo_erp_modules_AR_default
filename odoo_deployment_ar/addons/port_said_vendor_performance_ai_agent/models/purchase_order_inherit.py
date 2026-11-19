# -*- coding: utf-8 -*-
from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_done(self):
        res = super().button_done()
        engine = self.env['port_said.vendor.performance.engine'].sudo()
        for po in self:
            if po.partner_id:
                try:
                    period = fields.Date.to_date(po.date_order) if po.date_order else fields.Date.today()
                    engine.compute_vendor_score(po.partner_id, period)
                except Exception as exc:
                    po.message_post(body='فشل تحديث تقييم كفاءة المورد: %s' % exc)
        return res

    def button_confirm(self):
        res = super().button_confirm()
        engine = self.env['port_said.vendor.performance.engine'].sudo()
        for po in self:
            if po.partner_id:
                try:
                    period = fields.Date.to_date(po.date_order) if po.date_order else fields.Date.today()
                    engine.compute_vendor_score(po.partner_id, period)
                except Exception as exc:
                    po.message_post(body='فشل تحديث تقييم كفاءة المورد: %s' % exc)
        return res
