# -*- coding: utf-8 -*-
from odoo import api, models

from .national_id_validator import parse_egyptian_national_id


class Surety(models.Model):
    _inherit = 'demo_gov.surety'

    # ملحوظة: حقل national_id هنا related من employee_id.identification_id
    # (يتم التحقق منه عند مصدره في hr.employee)، فالتحقق المضاف هنا يقتصر
    # على guarantor_national_id (الكفيل الخارجي، يُدخَل مباشرة).
    @api.constrains('guarantor_national_id')
    def _check_guarantor_national_id_structure(self):
        for rec in self:
            if rec.guarantor_national_id:
                parse_egyptian_national_id(
                    rec.guarantor_national_id, 'الرقم القومي للكفيل')
