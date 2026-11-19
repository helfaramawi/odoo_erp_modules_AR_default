# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrJobEvaluation(models.Model):
    _name = 'demo_gov.hr.job.evaluation'
    _description = 'تقييم الوظائف والدرجات المالية — FDD-HR-07'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'evaluation_date desc'

    job_id = fields.Many2one('hr.job', string='الوظيفة', required=True)
    department_id = fields.Many2one(related='job_id.department_id', store=True, string='الإدارة')
    evaluation_date = fields.Date(string='تاريخ التقييم', default=fields.Date.today, required=True)
    evaluated_grade = fields.Char(string='الدرجة المالية المقترحة', required=True)
    points_score = fields.Float(string='مجموع نقاط التقييم')
    evaluator_id = fields.Many2one('res.users', string='المُقيِّم', default=lambda s: s.env.user)
    notes = fields.Text(string='ملاحظات')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('approved', 'معتمَد'),
    ], default='draft', string='الحالة', tracking=True)

    def action_approve(self):
        for rec in self:
            if rec.state == 'approved':
                raise UserError(_('التقييم معتمَد بالفعل.'))
            rec.job_id.write({
                'min_grade': rec.evaluated_grade,
                'max_grade': rec.evaluated_grade,
            })
        self.write({'state': 'approved'})
