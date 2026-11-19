# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidBudgetReallocationRecommendation(models.Model):
    _name = 'port_said.budget.reallocation.recommendation'
    _description = 'توصية إعادة توزيع الاعتمادات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'recommended_amount desc, create_date desc'

    name = fields.Char(string='رقم التوصية', required=True, copy=False, readonly=True, default=lambda self: _('New'))

    source_type = fields.Selection([
        ('forecast', 'من تقرير توقع الانحرافات'),
        ('direct_budget_analysis', 'تحليل مباشر من الموازنة'),
    ], string='مصدر التوصية', default='direct_budget_analysis', tracking=True)

    source_forecast_model = fields.Char(string='موديل تقرير التوقع')
    source_forecast_id = fields.Integer(string='رقم تقرير التوقع')

    budget_plan_id = fields.Many2one('port_said.budget.plan', string='خطة الموازنة', index=True, tracking=True)

    from_budget_line_id = fields.Many2one('port_said.budget.line', string='من بند فائض', index=True, tracking=True)
    to_budget_line_id = fields.Many2one('port_said.budget.line', string='إلى بند عجز', index=True, tracking=True)

    from_budget_code = fields.Char(string='كود بند الفائض', tracking=True)
    from_budget_name = fields.Char(string='اسم بند الفائض')
    from_budget_category = fields.Char(string='تصنيف بند الفائض')

    to_budget_code = fields.Char(string='كود بند العجز', tracking=True)
    to_budget_name = fields.Char(string='اسم بند العجز')
    to_budget_category = fields.Char(string='تصنيف بند العجز')

    surplus_amount = fields.Monetary(string='الفائض المتوقع في البند المحول منه', currency_field='currency_id')
    deficit_amount = fields.Monetary(string='العجز المتوقع في البند المحول إليه', currency_field='currency_id')
    transferable_amount = fields.Monetary(string='الحد الآمن للتحويل', currency_field='currency_id')
    recommended_amount = fields.Monetary(string='القيمة المقترحة للتحويل', currency_field='currency_id', tracking=True)

    confidence_score = fields.Float(string='درجة الثقة %', digits=(16, 2), tracking=True)
    priority = fields.Selection([
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'مرتفعة'),
        ('critical', 'حرجة'),
    ], string='الأولوية', tracking=True)

    reason = fields.Text(string='سبب التوصية', readonly=True)
    official_memo = fields.Html(string='مذكرة إعادة توزيع رسمية', readonly=True)
    recommendation_notes = fields.Text(string='ملاحظات داخلية')

    currency_id = fields.Many2one('res.currency', string='العملة', default=lambda self: self.env.company.currency_id.id)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('to_review', 'للمراجعة'),
        ('accepted', 'مقبولة'),
        ('rejected', 'مرفوضة'),
        ('cancelled', 'ملغية'),
    ], string='الحالة', default='draft', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_decision_notes = fields.Text(string='ملاحظات قرار المراجعة')

    _sql_constraints = [
        ('unique_budget_reallocation_pair', 'unique(budget_plan_id, from_budget_line_id, to_budget_line_id, recommended_amount)', 'يوجد توصية سابقة لنفس خطة الموازنة ونفس البنود ونفس القيمة.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('port_said.budget.reallocation.recommendation') or _('New')
        return super().create(vals_list)

    def action_to_review(self):
        self.write({'state': 'to_review'})

    def action_accept(self):
        self.write({'state': 'accepted', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_reject(self):
        self.write({'state': 'rejected', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_open_budget_plan(self):
        self.ensure_one()
        if not self.budget_plan_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'خطة الموازنة',
            'res_model': 'port_said.budget.plan',
            'res_id': self.budget_plan_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
