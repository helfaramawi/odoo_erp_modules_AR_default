# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrTrainingNeed(models.Model):
    _name = 'demo_gov.hr.training.need'
    _description = 'تحديد احتياج تدريبي — نموذج 4'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='الاحتياج التدريبي', required=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف')
    department_id = fields.Many2one('hr.department', string='الإدارة', required=True)
    priority = fields.Selection([
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
    ], string='الأولوية', default='medium')
    requested_by = fields.Many2one('res.users', string='مقدَّم من', default=lambda s: s.env.user)
    fiscal_year = fields.Char(string='السنة', default=lambda s: str(fields.Date.today().year))
    notes = fields.Text(string='ملاحظات')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('submitted', 'مقدَّم'),
        ('approved', 'معتمَد'),
        ('rejected', 'مرفوض'),
        ('planned', 'مُدرَج في الخطة'),
    ], default='draft', string='الحالة', tracking=True)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_add_to_plan(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('لازم الاحتياج يكون معتمَد أولاً قبل إدراجه في الخطة السنوية.'))
        self.write({'state': 'planned'})
