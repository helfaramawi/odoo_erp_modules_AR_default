# -*- coding: utf-8 -*-
from odoo import models, fields


class HrTrainingInstructor(models.Model):
    _name = 'demo_gov.hr.training.instructor'
    _description = 'مدرب — داخلي أو خارجي'

    name = fields.Char(string='الاسم', required=True)
    instructor_type = fields.Selection([
        ('internal', 'داخلي'),
        ('external', 'خارجي'),
    ], string='النوع', default='internal', required=True)
    specialization = fields.Char(string='التخصص')
    phone = fields.Char(string='الهاتف')
    email = fields.Char(string='البريد الإلكتروني')
    employee_id = fields.Many2one('hr.employee', string='الموظف (لو داخلي)')
    notes = fields.Text(string='ملاحظات')
