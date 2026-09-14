# -*- coding: utf-8 -*-
from odoo import api, models


class PortSaidDossier(models.Model):
    _inherit = 'port_said.dossier'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        engine = self.env['port_said.duplicate.claim.engine'].sudo()
        for rec in records:
            try:
                atts = self.env['ir.attachment'].sudo().search([('res_model', '=', rec._name), ('res_id', '=', rec.id)])
                for att in atts:
                    engine.scan_attachment(att)
            except Exception:
                pass
        return records
