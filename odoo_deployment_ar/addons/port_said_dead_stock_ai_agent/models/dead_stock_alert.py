# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidDeadStockAlert(models.Model):
    _name = 'port_said.dead.stock.alert'
    _description = 'تنبيه مخزون راكد أو بطيء الحركة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'stock_value desc, days_no_movement desc'

    name = fields.Char(
        string='رقم التنبيه',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    product_id = fields.Many2one('product.product', string='الصنف', required=True, index=True, tracking=True)
    product_tmpl_id = fields.Many2one('product.template', string='قالب الصنف', related='product_id.product_tmpl_id', store=True)
    categ_id = fields.Many2one('product.category', string='الفئة', related='product_id.categ_id', store=True)

    default_code = fields.Char(string='الكود الداخلي', related='product_id.default_code', store=True)
    uom_id = fields.Many2one('uom.uom', string='وحدة القياس', related='product_id.uom_id', store=True)

    qty_available = fields.Float(string='الرصيد الحالي', digits=(16, 2), tracking=True)
    standard_price = fields.Float(string='تكلفة الوحدة', digits=(16, 2), tracking=True)
    stock_value = fields.Monetary(string='القيمة المالية المجمدة', currency_field='currency_id', tracking=True)

    last_outgoing_move_id = fields.Many2one('stock.move', string='آخر حركة صرف', readonly=True)
    last_outgoing_date = fields.Datetime(string='تاريخ آخر صرف', tracking=True)
    last_incoming_date = fields.Datetime(string='تاريخ آخر إضافة')
    days_no_movement = fields.Integer(string='عدد أيام بدون صرف', tracking=True)

    movement_count_6m = fields.Integer(string='عدد حركات الصرف آخر 6 أشهر')
    movement_count_12m = fields.Integer(string='عدد حركات الصرف آخر 12 شهر')
    outgoing_qty_12m = fields.Float(string='كمية الصرف آخر 12 شهر', digits=(16, 2))

    alert_type = fields.Selection([
        ('slow_6m', 'بطيء الحركة - بلا صرف 6 أشهر'),
        ('dead_12m', 'راكد - بلا صرف 12 شهر'),
        ('high_value_dead', 'راكد عالي القيمة'),
        ('duplicate_name', 'أصناف مكررة بأسماء متقاربة'),
        ('overstock', 'تجاوز الحد الاقتصادي للتخزين'),
    ], string='نوع التنبيه', required=True, tracking=True)

    risk_level = fields.Selection([
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'مرتفعة'),
        ('critical', 'حرجة'),
    ], string='مستوى الخطورة', compute='_compute_risk_level', store=True, tracking=True)

    recommendation_type = fields.Selection([
        ('redistribute', 'إعادة توزيع'),
        ('sell', 'بيع / تصرف'),
        ('reduce_purchase', 'تخفيض الشراء'),
        ('review_need', 'مراجعة الاحتياج'),
        ('merge_duplicate', 'دمج/مراجعة الأصناف المكررة'),
    ], string='نوع التوصية', tracking=True)

    reason = fields.Text(string='سبب التنبيه', readonly=True)
    recommendation = fields.Text(string='التوصية', readonly=True)

    duplicate_product_ids = fields.Many2many(
        'product.product',
        'dead_stock_duplicate_product_rel',
        'alert_id',
        'product_id',
        string='أصناف متشابهة محتملة'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='العملة',
        default=lambda self: self.env.company.currency_id.id
    )

    state = fields.Selection([
        ('new', 'جديد'),
        ('under_review', 'تحت المراجعة'),
        ('action_planned', 'تم وضع إجراء'),
        ('resolved', 'تمت المعالجة'),
        ('ignored', 'تم التجاهل'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='new', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_notes = fields.Text(string='ملاحظات المراجعة')

    _sql_constraints = [
        (
            'unique_dead_stock_alert',
            'unique(product_id, alert_type)',
            'يوجد تنبيه سابق لنفس الصنف ونفس نوع التنبيه.'
        )
    ]

    @api.depends('alert_type', 'stock_value', 'days_no_movement')
    def _compute_risk_level(self):
        for rec in self:
            if rec.alert_type == 'high_value_dead' or rec.stock_value >= 100000:
                rec.risk_level = 'critical'
            elif rec.days_no_movement >= 365:
                rec.risk_level = 'high'
            elif rec.days_no_movement >= 180:
                rec.risk_level = 'medium'
            else:
                rec.risk_level = 'low'

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('port_said.dead.stock.alert') or _('New')
        return super().create(vals_list)

    def action_review(self):
        self.write({
            'state': 'under_review',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_plan(self):
        self.write({
            'state': 'action_planned',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_resolve(self):
        self.write({
            'state': 'resolved',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_ignore(self):
        self.write({
            'state': 'ignored',
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Datetime.now(),
        })

    def action_open_product(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'الصنف',
            'res_model': 'product.product',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_last_move(self):
        self.ensure_one()
        if not self.last_outgoing_move_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'آخر حركة صرف',
            'res_model': 'stock.move',
            'res_id': self.last_outgoing_move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
