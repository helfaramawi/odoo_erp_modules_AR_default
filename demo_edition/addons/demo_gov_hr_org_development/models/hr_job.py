# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrJob(models.Model):
    _inherit = 'hr.job'

    # بطاقة الوصف الوظيفي — FDD-HR-07
    job_duties = fields.Text(string='المهام والواجبات')
    job_requirements = fields.Text(string='الاشتراطات')
    job_qualifications = fields.Text(string='المؤهلات المطلوبة')
    reporting_to = fields.Char(string='يتبع وظيفياً')
    min_grade = fields.Char(string='أدنى درجة مالية')
    max_grade = fields.Char(string='أقصى درجة مالية')

    evaluation_ids = fields.One2many('demo_gov.hr.job.evaluation', 'job_id',
                                      string='تقييمات الوظيفة')
    budget_ids = fields.One2many('demo_gov.hr.position.budget', 'job_id',
                                  string='موازنات الوظيفة')
