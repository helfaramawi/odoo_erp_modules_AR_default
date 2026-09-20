# -*- coding: utf-8 -*-
from odoo import api, models

from ..models.national_id_validator import parse_egyptian_national_id


class NewCustodyWizard(models.TransientModel):
    _inherit = 'new.custody.wizard'

    @api.constrains('national_id')
    def _check_national_id_structure(self):
        for rec in self:
            if rec.national_id:
                parse_egyptian_national_id(rec.national_id, 'الرقم القومي')
