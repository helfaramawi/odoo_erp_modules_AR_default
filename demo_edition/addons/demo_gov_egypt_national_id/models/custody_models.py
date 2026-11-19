# -*- coding: utf-8 -*-
from odoo import api, models

from .national_id_validator import (
    check_national_id_gender_match,
    parse_egyptian_national_id,
)


class CustodyAssignment(models.Model):
    _inherit = 'custody.assignment'

    @api.constrains('national_id', 'employee_id')
    def _check_national_id_structure(self):
        for rec in self:
            if rec.national_id:
                parsed = parse_egyptian_national_id(rec.national_id, 'الرقم القومي')
                if rec.employee_id:
                    check_national_id_gender_match(
                        parsed, rec.employee_id.gender, 'الرقم القومي')


class CustodyTransfer(models.Model):
    _inherit = 'custody.transfer'

    @api.constrains('to_national_id', 'to_employee_id')
    def _check_to_national_id_structure(self):
        for rec in self:
            if rec.to_national_id:
                parsed = parse_egyptian_national_id(
                    rec.to_national_id, 'الرقم القومي للمستلم')
                if rec.to_employee_id:
                    check_national_id_gender_match(
                        parsed, rec.to_employee_id.gender, 'الرقم القومي للمستلم')
