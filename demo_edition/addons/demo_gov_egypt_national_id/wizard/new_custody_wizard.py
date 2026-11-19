# -*- coding: utf-8 -*-
from odoo import api, models

from ..models.national_id_validator import (
    check_national_id_gender_match,
    parse_egyptian_national_id,
)


class NewCustodyWizard(models.TransientModel):
    _inherit = 'new.custody.wizard'

    @api.constrains('national_id', 'employee_id')
    def _check_national_id_structure(self):
        for rec in self:
            if rec.national_id:
                parsed = parse_egyptian_national_id(rec.national_id, 'الرقم القومي')
                if rec.employee_id:
                    check_national_id_gender_match(
                        parsed, rec.employee_id.gender, 'الرقم القومي')
