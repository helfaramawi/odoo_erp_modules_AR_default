# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPromotion(models.Model):
    _name = 'demo_gov.hr.promotion'
    _description = 'حركة ترقية — إجراء رقم 19'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='رقم الحركة', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    current_grade = fields.Char(related='employee_id.civil_service_grade', readonly=True,
                                 string='الدرجة الحالية')
    new_grade = fields.Char(string='الدرجة الجديدة', required=True)
    decision_number = fields.Char(string='رقم قرار الترقية')
    decision_date = fields.Date(string='تاريخ قرار الترقية')

    state = fields.Selection([
        ('proposed', 'مقترَحة'),
        ('committee_review', 'مُحالة للجنة الموارد البشرية'),
        ('approved', 'معتمَدة'),
        ('rejected', 'مرفوضة'),
    ], default='proposed', string='الحالة', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.promotion') or '/'
        return super().create(vals_list)

    def action_send_to_committee(self):
        self.write({'state': 'committee_review'})

    def action_approve(self):
        for rec in self:
            if rec.state != 'committee_review':
                raise UserError(_('الترقية لازم تكون مُحالة للجنة أولاً.'))
            rec.employee_id.civil_service_grade = rec.new_grade
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})
