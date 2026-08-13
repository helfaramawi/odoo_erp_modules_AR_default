# -*- coding: utf-8 -*-
from odoo import models


class PortSaidDossier(models.Model):
    _inherit = 'port_said.dossier'

    def write(self, vals):
        res = super().write(vals)
        watch = {'state', 'is_complete', 'complete', 'is_completed', 'missing_attachments'}
        if watch.intersection(vals.keys()):
            engine = self.env['port_said.payment.cycle.engine'].sudo()
            for rec in self:
                try:
                    engine.scan_record(rec)
                except Exception as exc:
                    if hasattr(rec, 'message_post'):
                        rec.message_post(body='فشل فحص تأخير دورة الصرف: %s' % exc)
        return res
