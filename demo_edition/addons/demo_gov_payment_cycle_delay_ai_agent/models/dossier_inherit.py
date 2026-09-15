# -*- coding: utf-8 -*-
from odoo import models


class DemoGovDossier(models.Model):
    _inherit = 'demo_gov.dossier'

    def write(self, vals):
        res = super().write(vals)
        watch = {'state', 'is_complete', 'complete', 'is_completed', 'missing_attachments'}
        if watch.intersection(vals.keys()):
            engine = self.env['demo_gov.payment.cycle.engine'].sudo()
            for rec in self:
                try:
                    engine.scan_record(rec)
                except Exception as exc:
                    if hasattr(rec, 'message_post'):
                        rec.message_post(body='فشل فحص تأخير دورة الصرف: %s' % exc)
        return res
