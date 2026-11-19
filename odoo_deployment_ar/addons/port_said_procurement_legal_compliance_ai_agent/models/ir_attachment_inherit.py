# -*- coding: utf-8 -*-
from odoo import api, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        engine = self.env['port_said.procurement.legal.engine'].sudo()
        for att in records:
            try:
                if att.res_model in ['procurement.adjudication', 'procurement.committee', 'purchase.order', 'port_said.dossier'] and att.res_id:
                    rec = self.env[att.res_model].sudo().browse(att.res_id)
                    if rec.exists():
                        engine.check_procurement_record(rec, 'general')
            except Exception:
                pass
        return records
