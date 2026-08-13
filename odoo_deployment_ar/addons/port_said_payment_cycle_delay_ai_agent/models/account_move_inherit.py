# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            engine = self.env['port_said.payment.cycle.engine'].sudo()
            for rec in self:
                try:
                    engine.scan_record(rec)
                except Exception:
                    pass
        return res
