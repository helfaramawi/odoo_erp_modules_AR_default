# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidProcurementSplittingAlert(models.Model):
    _name = 'port_said.procurement.splitting.alert'
    _description = 'تنبيه تجزئة مشتريات محتملة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'risk_score desc, create_date desc'

    name = fields.Char(
        string='رقم التنبيه',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    supplier_id = fields.Many2one('res.partner', string='المورد', index=True, tracking=True)
    department_name = fields.Char(string='الإدارة / الجهة الطالبة', tracking=True)

    source_model = fields.Char(string='النموذج المصدر', readonly=True)
    source_res_id = fields.Integer(string='رقم السجل المصدر', readonly=True)
    source_display_name = fields.Char(string='اسم السجل المصدر', readonly=True)

    threshold_amount = fields.Monetary(string='حد الاعتماد', currency_field='currency_id', tracking=True)
    lower_limit_amount = fields.Monetary(string='بداية نطاق الاشتباه', currency_field='currency_id')
    total_amount = fields.Monetary(string='إجمالي العمليات المشابهة', currency_field='currency_id', tracking=True)
    order_count = fields.Integer(string='عدد العمليات المشابهة', tracking=True)

    date_from = fields.Date(string='من تاريخ', tracking=True)
    date_to = fields.Date(string='إلى تاريخ', tracking=True)
    window_days = fields.Integer(string='نافذة الفحص بالأيام', default=30)

    currency_id = fields.Many2one(
        'res.currency',
        string='العملة',
        default=lambda self: self.env.company.currency_id.id
    )

    purchase_order_ids = fields.Many2many(
        'purchase.order',
        'procurement_splitting_alert_purchase_order_rel',
        'alert_id',
        'purchase_order_id',
        string='أوامر الشراء المرتبطة'
    )

    suspected_product_names = fields.Text(string='الأصناف / التصنيفات المتكررة', readonly=True)

    detection_type = fields.Selection([
        ('same_supplier_near_threshold', 'نفس المورد ومبالغ قريبة من حد الاعتماد'),
        ('same_product_near_threshold', 'نفس الصنف أو التصنيف يتكرر بأوامر متعددة'),
        ('same_department_near_threshold', 'نفس الإدارة والغرض خلال فترة قصيرة'),
        ('year_end_pattern', 'تجزئة محتملة قرب نهاية السنة المالية'),
        ('combined', 'مؤشرات متعددة'),
    ], string='نوع الاشتباه', required=True, tracking=True)

    risk_score = fields.Integer(string='درجة الخطورة', default=0, tracking=True)

    risk_level = fields.Selection([
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'مرتفعة'),
        ('critical', 'حرجة'),
    ], string='مستوى الخطورة', compute='_compute_risk_level', store=True, tracking=True)

    reason = fields.Text(string='سبب الاشتباه', readonly=True)
    recommendation = fields.Text(string='التوصية الرقابية', readonly=True)

    state = fields.Selection([
        ('new', 'جديد'),
        ('under_review', 'تحت المراجعة'),
        ('justified', 'مبرر'),
        ('escalated', 'تم التصعيد'),
        ('closed', 'مغلق'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='new', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_notes = fields.Text(string='ملاحظات المراجعة')

    _sql_constraints = [
        (
            'unique_procurement_splitting_alert',
            'unique(supplier_id, date_from, date_to, detection_type)',
            'يوجد تنبيه سابق لنفس المورد ونفس فترة الفحص ونوع الاشتباه.'
        )
    ]

    @api.depends('risk_score')
    def _compute_risk_level(self):
        for rec in self:
            if rec.risk_score >= 85:
                rec.risk_level = 'critical'
            elif rec.risk_score >= 65:
                rec.risk_level = 'high'
            elif rec.risk_score >= 45:
                rec.risk_level = 'medium'
            else:
                rec.risk_level = 'low'

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('port_said.procurement.splitting.alert') or _('New')
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

    def action_review(self):
        self.write({
            'state': 'under_review',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_justify(self):
        self.write({
            'state': 'justified',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_escalate(self):
        self.write({
            'state': 'escalated',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_close(self):
        self.write({
            'state': 'closed',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })
