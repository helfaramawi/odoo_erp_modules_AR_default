# -*- coding: utf-8 -*-
from odoo import api, models


class PortSaidDaftar55(models.Model):
    _inherit = 'port_said.daftar55'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        engine = self.env['port_said.duplicate.claim.engine'].sudo()
        for rec in records:
            try:
                engine.scan_claim_record(rec)
            except Exception as exc:
                if hasattr(rec, 'message_post'):
                    rec.message_post(body='فشل فحص تكرار المطالبة: %s' % exc)
        return records

    def write(self, vals):
        res = super().write(vals)
        watch = {'amount_gross', 'amount_total', 'total_amount', 'amount', 'invoice_number', 'invoice_no', 'vendor_id', 'partner_id', 'beneficiary_id', 'date_received', 'date', 'state'}
        if watch.intersection(vals.keys()):
            engine = self.env['port_said.duplicate.claim.engine'].sudo()
            for rec in self:
                try:
                    engine.scan_claim_record(rec)
                except Exception as exc:
                    if hasattr(rec, 'message_post'):
                        rec.message_post(body='فشل فحص تكرار المطالبة: %s' % exc)
        return res
