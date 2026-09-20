# -*- coding: utf-8 -*-
from odoo import api, models

from .national_id_validator import parse_egyptian_national_id


class CashTransfer(models.Model):
    _inherit = 'demo_gov.cash_transfer'

    @api.constrains('receiver_id_number')
    def _check_receiver_id_number_structure(self):
        for rec in self:
            if rec.receiver_id_number:
                parse_egyptian_national_id(rec.receiver_id_number, 'رقم قومي للمستلم')
