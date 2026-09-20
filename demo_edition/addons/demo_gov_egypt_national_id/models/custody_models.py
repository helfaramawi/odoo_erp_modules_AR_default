# -*- coding: utf-8 -*-
from odoo import api, models

from .national_id_validator import parse_egyptian_national_id


class CustodyAssignment(models.Model):
    _inherit = 'custody.assignment'

    @api.constrains('national_id')
    def _check_national_id_structure(self):
        for rec in self:
            if rec.national_id:
                parse_egyptian_national_id(rec.national_id, 'الرقم القومي')


class CustodyTransfer(models.Model):
    _inherit = 'custody.transfer'

    @api.constrains('to_national_id')
    def _check_to_national_id_structure(self):
        for rec in self:
            if rec.to_national_id:
                parse_egyptian_national_id(rec.to_national_id, 'الرقم القومي للمستلم')
