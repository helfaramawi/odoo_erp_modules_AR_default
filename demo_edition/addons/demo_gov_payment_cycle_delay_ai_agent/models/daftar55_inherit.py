# -*- coding: utf-8 -*-
from odoo import models


class DemoGovDaftar55(models.Model):
    _inherit = 'demo_gov.daftar55'

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            engine = self.env['demo_gov.payment.cycle.engine'].sudo()
            for rec in self:
                try:
                    engine.scan_record(rec)
                except Exception as exc:
                    if hasattr(rec, 'message_post'):
                        rec.message_post(body='فشل فحص تأخير دورة الصرف: %s' % exc)
        return res
