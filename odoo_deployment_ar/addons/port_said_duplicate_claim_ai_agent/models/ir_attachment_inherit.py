# -*- coding: utf-8 -*-
from odoo import api, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        engine = self.env['port_said.duplicate.claim.engine'].sudo()
        for rec in records:
            try:
                engine.scan_attachment(rec)
            except Exception:
                pass
        return records
