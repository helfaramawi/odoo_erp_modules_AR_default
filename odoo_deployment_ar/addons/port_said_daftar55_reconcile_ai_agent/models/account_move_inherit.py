# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        engine = self.env['port_said.daftar55.account.reconcile.engine'].sudo()
        Daftar55 = self.env['port_said.daftar55'].sudo()
        for move in self:
            refs = [x for x in [move.ref or '', move.name or ''] if x]
            for ref in refs:
                domain = []
                for fname in ['name', 'number', 'daftar55_no', 'sequence', 'reference']:
                    if fname in Daftar55._fields:
                        domain = ['|'] + domain + [(fname, 'ilike', ref)] if domain else [(fname, 'ilike', ref)]
                try:
                    records = Daftar55.search(domain, limit=10) if domain else Daftar55.browse()
                    for rec in records:
                        engine.check_daftar55_record(rec)
                except Exception as exc:
                    move.message_post(body='فشل فحص مطابقة دفتر 55 بعد ترحيل القيد: %s' % exc)
        return res
