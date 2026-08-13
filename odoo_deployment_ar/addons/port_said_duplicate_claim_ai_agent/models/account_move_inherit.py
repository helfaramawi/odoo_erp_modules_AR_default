# -*- coding: utf-8 -*-
from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        engine = self.env['port_said.duplicate.claim.engine'].sudo()
        for rec in records:
            try:
                if rec.move_type in ['in_invoice', 'in_refund']:
                    engine.scan_claim_record(rec)
            except Exception:
                pass
        return records

    def write(self, vals):
        res = super().write(vals)
        watch = {'partner_id', 'amount_total', 'invoice_date', 'date', 'ref', 'state'}
        if watch.intersection(vals.keys()):
            engine = self.env['port_said.duplicate.claim.engine'].sudo()
            for rec in self:
                try:
                    if rec.move_type in ['in_invoice', 'in_refund']:
                        engine.scan_claim_record(rec)
                except Exception:
                    pass
        return res
