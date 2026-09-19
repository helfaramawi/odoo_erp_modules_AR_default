# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

GOV_RATINGS = [
    ('excellent', 'ممتاز'),
    ('very_good', 'جيد جداً'),
    ('good', 'جيد'),
    ('acceptable', 'مقبول'),
    ('weak', 'ضعيف'),
]

# نسبة العلاوة التشجيعية المرتبطة بالتقدير — مرجعية فقط، تحتاج اعتماد
# الموارد البشرية على أحدث لائحة الحوافز قبل استخدامها في صرف فعلي.
INCENTIVE_ALLOWANCE_BY_RATING = {
    'excellent': 10.0,
    'very_good': 5.0,
    'good': 0.0,
    'acceptable': 0.0,
    'weak': 0.0,
}


class HrPerformanceAppraisal(models.Model):
    _name = 'demo_gov.hr.performance.appraisal'
    _description = 'تقييم الأداء السنوي — دفتر يومية الأداء'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fiscal_year desc, create_date desc'

    name = fields.Char(string='رقم التقييم', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True,
                                     string='الإدارة')
    fiscal_year = fields.Char(string='السنة', default=lambda s: str(fields.Date.today().year),
                               required=True)
    goals_text = fields.Text(string='الأهداف المرتبطة بالوصف الوظيفي')
    rating = fields.Selection(GOV_RATINGS, string='التقدير', tracking=True)
    reviewer_id = fields.Many2one('res.users', string='المُقيِّم', default=lambda s: s.env.user)
    incentive_allowance_pct = fields.Float(string='نسبة العلاوة التشجيعية %')
    grievance_ids = fields.One2many('demo_gov.hr.performance.grievance', 'appraisal_id',
                                     string='التظلمات')
    grievance_count = fields.Integer(compute='_compute_grievance_count')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('submitted', 'مقدَّم'),
        ('reviewed', 'تمت المراجعة'),
        ('finalized', 'معتمَد نهائياً'),
    ], default='draft', string='الحالة', tracking=True)

    _sql_constraints = [
        ('unique_appraisal_per_year', 'unique(employee_id, fiscal_year)',
         'يوجد تقييم أداء مسجَّل بالفعل لهذا الموظف عن نفس السنة.'),
    ]

    @api.depends('grievance_ids')
    def _compute_grievance_count(self):
        for rec in self:
            rec.grievance_count = len(rec.grievance_ids)

    @api.onchange('rating')
    def _onchange_rating(self):
        if self.rating:
            self.incentive_allowance_pct = INCENTIVE_ALLOWANCE_BY_RATING.get(self.rating, 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.performance.appraisal') or '/'
        return super().create(vals_list)

    def action_submit(self):
        for rec in self:
            if not rec.rating:
                raise UserError(_('لازم تحدد التقدير قبل تقديم التقييم.'))
        self.write({'state': 'submitted'})

    def action_review(self):
        self.write({'state': 'reviewed'})

    def action_finalize(self):
        for rec in self:
            if rec.state != 'reviewed':
                raise UserError(_('لازم التقييم يكون في حالة "تمت المراجعة" أولاً.'))
        self.write({'state': 'finalized'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
