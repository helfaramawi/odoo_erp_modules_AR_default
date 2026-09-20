# -*- coding: utf-8 -*-
"""
hr.employee فيه ثلاثة حقول مختلفة بتتستخدم فعليًا في التطبيق لتخزين
الرقم القومي (تنوّع تاريخي بين الموديولات القديمة): national_id
(حقل خاص من demo_gov_hr_employee)، ssnid و identification_id (حقلين
قياسيين في أودو بيعيد استخدامهم l10n_eg_custody و demo_gov_cash_books
على التوالي). التحقق هنا مُضاف على الثلاثة معاً.
"""
from odoo import api, models

from .national_id_validator import parse_egyptian_national_id


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('national_id')
    def _check_national_id_structure(self):
        for rec in self:
            if rec.national_id:
                parse_egyptian_national_id(rec.national_id, 'الرقم القومي')

    @api.constrains('ssnid')
    def _check_ssnid_structure(self):
        for rec in self:
            if rec.ssnid:
                parse_egyptian_national_id(rec.ssnid, 'الرقم القومي (SSN)')

    @api.constrains('identification_id')
    def _check_identification_id_structure(self):
        for rec in self:
            if rec.identification_id:
                parse_egyptian_national_id(rec.identification_id, 'رقم الهوية')
