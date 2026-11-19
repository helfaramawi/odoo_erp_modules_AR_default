# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrPositionBudget(models.Model):
    _name = 'demo_gov.hr.position.budget'
    _description = 'استمارة موازنة الوظائف — استمارة 5 (SSRS-04)'
    _order = 'fiscal_year desc'

    job_id = fields.Many2one('hr.job', string='الوظيفة', required=True)
    department_id = fields.Many2one(related='job_id.department_id', store=True, string='الإدارة')
    fiscal_year = fields.Char(string='السنة المالية', required=True,
                               default=lambda s: str(fields.Date.today().year))
    budgeted_positions = fields.Integer(string='الوظائف المعتمدة بالموازنة', required=True)

    filled_positions = fields.Integer(compute='_compute_positions', string='الوظائف المشغولة')
    vacant_positions = fields.Integer(compute='_compute_positions', string='الوظائف الشاغرة')
    movements_in = fields.Integer(compute='_compute_positions', string='حركات دخول (تعيينات)')
    movements_out = fields.Integer(compute='_compute_positions', string='حركات خروج (إنهاءات)')

    _sql_constraints = [
        ('unique_job_year', 'unique(job_id, fiscal_year)',
         'يوجد استمارة موازنة مسجَّلة بالفعل لهذه الوظيفة عن نفس السنة.'),
    ]

    def _compute_positions(self):
        Employee = self.env['hr.employee'].with_context(active_test=False)
        for rec in self:
            employees = Employee.search([('job_id', '=', rec.job_id.id)])
            rec.filled_positions = len(employees.filtered('active'))
            rec.vacant_positions = max(rec.budgeted_positions - rec.filled_positions, 0)
            rec.movements_in = len(employees.filtered(
                lambda e: e.appointment_decision_date
                and str(e.appointment_decision_date.year) == rec.fiscal_year))
            rec.movements_out = len(employees.filtered(
                lambda e: e.termination_date
                and str(e.termination_date.year) == rec.fiscal_year))
