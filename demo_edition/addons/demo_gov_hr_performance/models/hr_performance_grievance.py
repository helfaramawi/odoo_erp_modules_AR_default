# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPerformanceGrievance(models.Model):
    _name = 'demo_gov.hr.performance.grievance'
    _description = 'تظلم موظف من تقرير كفاءة الأداء — إجراء رقم 14'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='رقم التظلم', readonly=True, copy=False)
    appraisal_id = fields.Many2one('demo_gov.hr.performance.appraisal', string='تقييم الأداء',
                                    required=True, ondelete='cascade')
    employee_id = fields.Many2one(related='appraisal_id.employee_id', store=True,
                                   string='الموظف')
    grievance_text = fields.Text(string='نص التظلم', required=True)
    committee_notes = fields.Text(string='ملاحظات لجنة التظلمات')
    union_notes = fields.Text(string='ملاحظات النقابة')
    decision_text = fields.Text(string='القرار النهائي')

    state = fields.Selection([
        ('submitted', 'مقدَّم'),
        ('committee_review', 'مُحال للجنة التظلمات'),
        ('union_review', 'مُحال للنقابة'),
        ('resolved', 'تم البت فيه'),
    ], default='submitted', string='الحالة', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.performance.grievance') or '/'
        return super().create(vals_list)

    def action_send_to_committee(self):
        self.write({'state': 'committee_review'})

    def action_send_to_union(self):
        for rec in self:
            if rec.state != 'committee_review':
                raise UserError(_('لازم يكون التظلم مُحال للجنة أولاً.'))
        self.write({'state': 'union_review'})

    def action_resolve(self):
        for rec in self:
            if not rec.decision_text:
                raise UserError(_('لازم تسجّل القرار النهائي قبل إغلاق التظلم.'))
        self.write({'state': 'resolved'})
