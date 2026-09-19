# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrRecruitmentProject(models.Model):
    _name = 'demo_gov.hr.recruitment.project'
    _description = 'مشروع تعيين — وظيفة شاغرة (FDD-HR-05)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='اسم المشروع', required=True)
    job_id = fields.Many2one('hr.job', string='الوظيفة', required=True)
    department_id = fields.Many2one(related='job_id.department_id', store=True,
                                     string='الإدارة')
    planned_positions = fields.Integer(string='عدد الوظائف الشاغرة', default=1)
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('published', 'منشور'),
        ('screening', 'فرز الطلبات'),
        ('interviewing', 'مقابلات'),
        ('closed', 'مغلق'),
    ], default='draft', string='الحالة', tracking=True)
    applicant_ids = fields.One2many('hr.applicant', 'recruitment_project_id',
                                     string='المتقدمون')
    applicant_count = fields.Integer(compute='_compute_applicant_count',
                                      string='عدد المتقدمين')

    @api.depends('applicant_ids')
    def _compute_applicant_count(self):
        for rec in self:
            rec.applicant_count = len(rec.applicant_ids)

    def action_publish(self):
        self.write({'state': 'published'})

    def action_start_screening(self):
        self.write({'state': 'screening'})

    def action_start_interviews(self):
        self.write({'state': 'interviewing'})

    def action_close(self):
        self.write({'state': 'closed'})
