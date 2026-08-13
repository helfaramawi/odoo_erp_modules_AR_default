# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PortSaidConflictInterestAlert(models.Model):
    _name = 'port_said.conflict.interest.alert'
    _description = 'تنبيه تضارب مصالح محتمل'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'risk_score desc, create_date desc'

    name = fields.Char(string='رقم التنبيه', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    source_model = fields.Char(string='النموذج المصدر', readonly=True, tracking=True)
    source_res_id = fields.Integer(string='رقم السجل المصدر', readonly=True, tracking=True)
    source_display_name = fields.Char(string='اسم السجل المصدر', readonly=True)
    committee_name = fields.Char(string='اللجنة / جهة الفحص', readonly=True, tracking=True)
    supplier_id = fields.Many2one('res.partner', string='المورد', index=True, tracking=True)
    supplier_name = fields.Char(string='اسم المورد وقت الفحص', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='عضو اللجنة / الموظف', index=True, tracking=True)
    employee_name = fields.Char(string='اسم عضو اللجنة وقت الفحص', readonly=True)

    check_type = fields.Selection([
        ('phone_match', 'تطابق رقم هاتف'),
        ('email_match', 'تطابق بريد إلكتروني'),
        ('domain_match', 'تطابق نطاق بريد إلكتروني'),
        ('family_name_match', 'تشابه اسم عائلة'),
        ('repeated_supplier_committee', 'تكرار المورد مع نفس اللجنة'),
        ('historical_pattern', 'نمط تاريخي متكرر'),
        ('combined', 'مؤشرات متعددة'),
    ], string='نوع الاشتباه', required=True, tracking=True)

    risk_score = fields.Integer(string='درجة الخطورة', default=0, tracking=True)
    risk_level = fields.Selection([
        ('low', 'منخفضة'), ('medium', 'متوسطة'), ('high', 'مرتفعة'), ('critical', 'حرجة')
    ], string='مستوى الخطورة', compute='_compute_risk_level', store=True, tracking=True)

    reason = fields.Text(string='سبب الاشتباه', readonly=True)
    recommendation = fields.Text(string='التوصية', readonly=True)
    state = fields.Selection([
        ('new', 'جديد'),
        ('under_review', 'تحت المراجعة'),
        ('accepted_with_reservation', 'اعتماد مع تحفظ'),
        ('cleared', 'لا توجد مشكلة'),
        ('escalated', 'تم التصعيد'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='new', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_notes = fields.Text(string='ملاحظات المراجعة')

    _sql_constraints = [
        ('unique_conflict_alert_key',
         'unique(source_model, source_res_id, supplier_id, employee_id, check_type)',
         'يوجد تنبيه سابق لنفس السجل والمورد وعضو اللجنة ونوع الاشتباه.')
    ]

    @api.depends('risk_score')
    def _compute_risk_level(self):
        for rec in self:
            if rec.risk_score >= 80: rec.risk_level = 'critical'
            elif rec.risk_score >= 60: rec.risk_level = 'high'
            elif rec.risk_score >= 40: rec.risk_level = 'medium'
            else: rec.risk_level = 'low'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].sudo().next_by_code('port_said.conflict.interest.alert') or _('New')
        return super().create(vals_list)

    def action_open_source(self):
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'السجل المصدر',
            'res_model': self.source_model,
            'res_id': self.source_res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _set_review_state(self, state):
        for rec in self:
            rec.write({'state': state, 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_review(self): self._set_review_state('under_review')
    def action_clear(self): self._set_review_state('cleared')
    def action_escalate(self): self._set_review_state('escalated')
    def action_accept_with_reservation(self): self._set_review_state('accepted_with_reservation')
