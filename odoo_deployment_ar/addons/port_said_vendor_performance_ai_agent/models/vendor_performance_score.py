# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidVendorPerformanceScore(models.Model):
    _name = 'port_said.vendor.performance.score'
    _description = 'تقييم كفاءة المورد'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_date desc, final_score asc'

    name = fields.Char(string='المرجع', compute='_compute_name', store=True)

    partner_id = fields.Many2one(
        'res.partner',
        string='المورد',
        required=True,
        index=True,
        ondelete='cascade',
        tracking=True
    )

    period_date = fields.Date(string='شهر التقييم', required=True, index=True, tracking=True)

    quality_score = fields.Float(string='درجة جودة التوريد 40%', digits=(16, 2), tracking=True)
    delay_score = fields.Float(string='درجة الالتزام بالوقت 25%', digits=(16, 2), tracking=True)
    penalty_score = fields.Float(string='درجة سجل الجزاءات 20%', digits=(16, 2), tracking=True)
    volume_score = fields.Float(string='درجة حجم التعامل الناجح 15%', digits=(16, 2), tracking=True)

    final_score = fields.Float(string='التقييم النهائي من 100', digits=(16, 2), tracking=True)

    rating = fields.Selection([
        ('excellent', 'ممتاز'),
        ('good', 'جيد'),
        ('average', 'متوسط'),
        ('risky', 'عالي المخاطر'),
    ], string='تصنيف المورد', compute='_compute_rating', store=True, tracking=True)

    accepted_qty = fields.Float(string='الكمية المقبولة', digits=(16, 2))
    received_qty = fields.Float(string='الكمية المستلمة', digits=(16, 2))
    rejected_qty = fields.Float(string='الكمية المرفوضة/المتأخرة', digits=(16, 2))

    purchase_order_count = fields.Integer(string='عدد أوامر الشراء')
    successful_purchase_value = fields.Monetary(string='قيمة التوريدات الناجحة', currency_field='currency_id')
    total_purchase_value = fields.Monetary(string='إجمالي قيمة التعامل', currency_field='currency_id')

    delivery_count = fields.Integer(string='عدد الاستلامات')
    delayed_delivery_count = fields.Integer(string='عدد الاستلامات المتأخرة')
    average_delay_days = fields.Float(string='متوسط التأخير بالأيام', digits=(16, 2))

    penalty_count = fields.Integer(string='عدد الجزاءات')
    open_penalty_count = fields.Integer(string='عدد الجزاءات المفتوحة')

    recommendation = fields.Text(string='التوصية')
    calculation_details = fields.Text(string='تفاصيل الحساب', readonly=True)

    currency_id = fields.Many2one(
        'res.currency',
        string='العملة',
        default=lambda self: self.env.company.currency_id.id
    )

    purchase_order_ids = fields.Many2many(
        'purchase.order',
        'vendor_performance_purchase_order_rel',
        'score_id',
        'purchase_order_id',
        string='أوامر الشراء الداخلة في التقييم'
    )

    picking_ids = fields.Many2many(
        'stock.picking',
        'vendor_performance_stock_picking_rel',
        'score_id',
        'picking_id',
        string='استلامات المخزون الداخلة في التقييم'
    )

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('computed', 'محسوب'),
        ('reviewed', 'تمت المراجعة'),
        ('archived', 'مؤرشف'),
    ], string='الحالة', default='computed', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_notes = fields.Text(string='ملاحظات المراجعة')

    _sql_constraints = [
        (
            'unique_vendor_performance_period',
            'unique(partner_id, period_date)',
            'يوجد تقييم سابق لهذا المورد في نفس الفترة.'
        )
    ]

    @api.depends('partner_id', 'period_date')
    def _compute_name(self):
        for rec in self:
            rec.name = 'تقييم كفاءة المورد: %s - %s' % (
                rec.partner_id.display_name or '',
                rec.period_date or ''
            )

    @api.depends('final_score')
    def _compute_rating(self):
        for rec in self:
            if rec.final_score >= 85:
                rec.rating = 'excellent'
            elif rec.final_score >= 70:
                rec.rating = 'good'
            elif rec.final_score >= 60:
                rec.rating = 'average'
            else:
                rec.rating = 'risky'

    def action_review(self):
        self.write({
            'state': 'reviewed',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_open_vendor(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'المورد',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_recompute(self):
        for rec in self:
            self.env['port_said.vendor.performance.engine'].sudo().compute_vendor_score(
                rec.partner_id,
                rec.period_date
            )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم التحديث'),
                'message': _('تم إعادة حساب تقييم المورد.'),
                'type': 'success',
                'sticky': False,
            }
        }
