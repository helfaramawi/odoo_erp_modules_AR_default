# -*- coding: utf-8 -*-
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        engine = self.env['port_said.procurement.legal.engine'].sudo()
        for po in self:
            engine.check_and_block_if_needed(po, 'before_po')
        return super().button_confirm()
