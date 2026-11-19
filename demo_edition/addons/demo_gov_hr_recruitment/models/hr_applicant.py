# -*- coding: utf-8 -*-
from odoo import models, fields


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    recruitment_project_id = fields.Many2one('demo_gov.hr.recruitment.project',
                                              string='مشروع التعيين')
