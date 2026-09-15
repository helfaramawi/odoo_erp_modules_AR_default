# -*- coding: utf-8 -*-
from odoo import models


class PortSaidDaftar55(models.Model):
    _inherit = 'port_said.daftar55'

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            engine = self.env['port_said.daftar55.account.reconcile.engine'].sudo()
            for rec in self:
                try:
                    engine.check_daftar55_record(rec)
                except Exception as exc:
                    if hasattr(rec, 'message_post'):
                        rec.message_post(body='فشل فحص مطابقة دفتر 55 مع القيود: %s' % exc)
        return res
