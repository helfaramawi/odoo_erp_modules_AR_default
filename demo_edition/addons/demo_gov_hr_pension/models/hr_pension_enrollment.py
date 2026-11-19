# -*- coding: utf-8 -*-
from odoo import models, fields


class HrPensionEnrollment(models.Model):
    _name = 'demo_gov.hr.pension.enrollment'
    _description = 'اشتراك موظف في خطة معاش أو تأمين'
    _order = 'enrollment_date desc'

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True)
    plan_id = fields.Many2one('demo_gov.hr.pension.plan', string='الخطة', required=True)
    enrollment_date = fields.Date(string='تاريخ الاشتراك', default=fields.Date.today, required=True)
    end_date = fields.Date(string='تاريخ الانتهاء')
    state = fields.Selection([
        ('active', 'نشط'),
        ('ended', 'منتهٍ'),
    ], default='active', string='الحالة')

    _sql_constraints = [
        ('unique_employee_plan', 'unique(employee_id, plan_id)',
         'الموظف مشترك بالفعل في هذه الخطة.'),
    ]
