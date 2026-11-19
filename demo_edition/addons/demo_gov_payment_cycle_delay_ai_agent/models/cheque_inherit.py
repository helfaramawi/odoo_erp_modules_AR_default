# -*- coding: utf-8 -*-
from odoo import models


class DemoGovCheque(models.Model):
    _inherit = 'demo_gov.cheque'

    def write(self, vals):
        res = super().write(vals)
        watch = {'state', 'issue_date', 'date_issue', 'delivery_date', 'date_delivery', 'received_date', 'paid_date'}
        if watch.intersection(vals.keys()):
            engine = self.env['demo_gov.payment.cycle.engine'].sudo()
            for rec in self:
                try:
                    engine.scan_record(rec)
                except Exception as exc:
                    if hasattr(rec, 'message_post'):
                        rec.message_post(body='فشل فحص تأخير دورة الصرف: %s' % exc)
        return res
