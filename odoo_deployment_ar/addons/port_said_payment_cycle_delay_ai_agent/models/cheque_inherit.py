# -*- coding: utf-8 -*-
from odoo import models


class PortSaidCheque(models.Model):
    _inherit = 'port_said.cheque'

    def write(self, vals):
        res = super().write(vals)
        watch = {'state', 'issue_date', 'date_issue', 'delivery_date', 'date_delivery', 'received_date', 'paid_date'}
        if watch.intersection(vals.keys()):
            engine = self.env['port_said.payment.cycle.engine'].sudo()
            for rec in self:
                try:
                    engine.scan_record(rec)
                except Exception as exc:
                    if hasattr(rec, 'message_post'):
                        rec.message_post(body='فشل فحص تأخير دورة الصرف: %s' % exc)
        return res
