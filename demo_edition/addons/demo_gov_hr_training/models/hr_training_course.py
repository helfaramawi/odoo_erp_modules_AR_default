# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrTrainingCourse(models.Model):
    _name = 'demo_gov.hr.training.course'
    _description = 'دورة تدريبية'
    _order = 'start_date desc'

    name = fields.Char(string='اسم الدورة', required=True)
    course_type = fields.Selection([
        ('internal', 'داخلي'),
        ('external', 'خارجي'),
        ('competition', 'مسابقة'),
    ], string='نوع الدورة', default='internal', required=True)
    instructor_id = fields.Many2one('demo_gov.hr.training.instructor', string='المدرب')
    location = fields.Char(string='مكان الانعقاد')
    start_date = fields.Date(string='تاريخ البداية')
    end_date = fields.Date(string='تاريخ النهاية')
    seats = fields.Integer(string='عدد المقاعد', default=20)
    registration_ids = fields.One2many('demo_gov.hr.training.registration', 'course_id',
                                        string='المسجَّلون')
    registration_count = fields.Integer(string='عدد المسجَّلين', compute='_compute_registration_count')
    description = fields.Text(string='الوصف')

    @api.depends('registration_ids')
    def _compute_registration_count(self):
        for rec in self:
            rec.registration_count = len(rec.registration_ids)
