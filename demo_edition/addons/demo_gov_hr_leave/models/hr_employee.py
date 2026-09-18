# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    years_of_service = fields.Integer(string='سنوات الخدمة', compute='_compute_years_of_service')
    # مرجعي فقط — يحتاج تأكيد من الموارد البشرية على أحدث اللائحة التنفيذية
    # لقانون الخدمة المدنية 81/2016 قبل الاعتماد عليه في الاستحقاق الفعلي:
    #   أقل من سنة: تناسبي (21 يوم / 12 شهر لكل شهر خدمة)
    #   من سنة إلى أقل من 10 سنوات: 21 يوم
    #   10 سنوات فأكثر، أو سن 50 فأكثر: 30 يوم
    annual_leave_entitlement_days = fields.Integer(
        string='استحقاق الإجازة السنوية (يوم)', compute='_compute_years_of_service')

    @api.depends('appointment_decision_date', 'birthday')
    def _compute_years_of_service(self):
        today = fields.Date.today()
        for rec in self:
            if not rec.appointment_decision_date:
                rec.years_of_service = 0
                rec.annual_leave_entitlement_days = 0
                continue
            delta = relativedelta(today, rec.appointment_decision_date)
            years = delta.years
            rec.years_of_service = years
            age = relativedelta(today, rec.birthday).years if rec.birthday else 0
            if years < 1:
                months = delta.years * 12 + delta.months
                rec.annual_leave_entitlement_days = round(21 * months / 12)
            elif years >= 10 or age >= 50:
                rec.annual_leave_entitlement_days = 30
            else:
                rec.annual_leave_entitlement_days = 21
