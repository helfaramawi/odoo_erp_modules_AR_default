# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrTrainingRegistration(models.Model):
    _name = 'demo_gov.hr.training.registration'
    _description = 'تسجيل موظف في دورة تدريبية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='رقم التسجيل', readonly=True, copy=False)
    course_id = fields.Many2one('demo_gov.hr.training.course', string='الدورة', required=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True)
    manager_id = fields.Many2one(related='employee_id.parent_id', string='المدير المباشر', store=True)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('requested', 'مطلوب'),
        ('manager_approved', 'معتمَد من المدير'),
        ('confirmed', 'مؤكَّد من قسم التدريب'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ], default='draft', string='الحالة', tracking=True)

    # ── قياس أثر التدريب ─────────────────────────────────────────────────
    performance_before = fields.Selection([
        ('1', 'ضعيف'), ('2', 'مقبول'), ('3', 'جيد'), ('4', 'جيد جداً'), ('5', 'ممتاز'),
    ], string='الكفاءة قبل الدورة')
    performance_after = fields.Selection([
        ('1', 'ضعيف'), ('2', 'مقبول'), ('3', 'جيد'), ('4', 'جيد جداً'), ('5', 'ممتاز'),
    ], string='الكفاءة بعد الدورة')
    impact_notes = fields.Text(string='ملاحظات قياس الأثر')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.training.registration') or '/'
        return super().create(vals_list)

    def action_request(self):
        self.write({'state': 'requested'})

    def action_manager_approve(self):
        for rec in self:
            if rec.state != 'requested':
                raise UserError(_('التسجيل لازم يكون في حالة "مطلوب" أولاً.'))
        self.write({'state': 'manager_approved'})

    def action_confirm_by_training_dept(self):
        for rec in self:
            if rec.state != 'manager_approved':
                raise UserError(_('التسجيل لازم يكون معتمَد من المدير أولاً.'))
        self.write({'state': 'confirmed'})

    def action_complete(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_('التسجيل لازم يكون مؤكَّد من قسم التدريب أولاً.'))
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
