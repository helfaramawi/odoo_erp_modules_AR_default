# -*- coding: utf-8 -*-
from odoo import api, models

from .national_id_validator import parse_egyptian_national_id


class HrPayrollNonEmployeeReward(models.Model):
    _inherit = 'demo_gov.hr.payroll.non.employee.reward'

    @api.constrains('national_id')
    def _check_national_id_structure(self):
        for rec in self:
            if rec.national_id:
                parse_egyptian_national_id(rec.national_id, 'الرقم القومي')


class HrPayrollExternalSalary(models.Model):
    _inherit = 'demo_gov.hr.payroll.external.salary'

    @api.constrains('national_id')
    def _check_national_id_structure(self):
        for rec in self:
            if rec.national_id:
                parse_egyptian_national_id(rec.national_id, 'الرقم القومي')
