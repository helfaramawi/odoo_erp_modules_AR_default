from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class StocktakingSession(models.Model):
    """
    جلسة الجرد — Stocktaking Session (FR-I5)
    Wraps Odoo's stock.inventory with government Form 6 requirements.
    Computes surplus (زيادة) and deficit (عجز) per item.
    """
    _name = 'stock.stocktaking.session'
    _description = 'جرد أصناف - Stocktaking Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'stocktaking_date desc'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='رقم محضر الجرد', required=True, copy=False,
        readonly=True, default='/', tracking=True,
    )
    stocktaking_date = fields.Date(
        string='تاريخ الجرد', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    fiscal_year = fields.Char(
        string='السنة المالية', tracking=True,
        default=lambda self: str(fields.Date.context_today(self).year),
    )

    # ── Location ──────────────────────────────────────────────────────────────
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='المستودع', required=True, tracking=True,
    )
    location_id = fields.Many2one(
        'stock.location', string='الموقع',
        domain="[('usage','=','internal')]", tracking=True,
    )

    # ── Committee ─────────────────────────────────────────────────────────────
    committee_chairman_id = fields.Many2one(
        'hr.employee', string='رئيس لجنة الجرد', tracking=True,
    )
    committee_members = fields.Text(
        string='أعضاء اللجنة', tracking=True,
        help='أسماء أعضاء لجنة الجرد مفصولة بفاصلة',
    )
    storekeeper_id = fields.Many2one(
        'hr.employee', string='أمين المخزن', tracking=True,
    )

    # ── Lines ─────────────────────────────────────────────────────────────────
    line_ids = fields.One2many(
        'stock.stocktaking.line', 'session_id', string='أصناف الجرد',
    )

    # ── Computed Totals ───────────────────────────────────────────────────────
    total_items = fields.Integer(
        string='إجمالي الأصناف', compute='_compute_totals', store=True,
    )
    total_surplus_items = fields.Integer(
        string='أصناف بزيادة', compute='_compute_totals', store=True,
    )
    total_deficit_items = fields.Integer(
        string='أصناف بعجز', compute='_compute_totals', store=True,
    )
    total_surplus_value = fields.Float(
        string='إجمالي قيمة الزيادة', compute='_compute_totals',
        store=True, digits='Account',
    )
    total_deficit_value = fields.Float(
        string='إجمالي قيمة العجز', compute='_compute_totals',
        store=True, digits='Account',
    )

    # ── State ─────────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',    'مسودة'),
        ('counting', 'جاري الجرد'),
        ('done',     'منتهي'),
        ('validated','معتمد'),
    ], default='draft', tracking=True)

    notes = fields.Text(string='ملاحظات')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'رقم محضر الجرد يجب أن يكون فريداً'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.stocktaking') or '/'
        return super().create(vals_list)

    @api.depends('line_ids', 'line_ids.difference_qty', 'line_ids.difference_value')
    def _compute_totals(self):
        for rec in self:
            lines = rec.line_ids
            rec.total_items = len(lines)
            surplus = lines.filtered(lambda l: l.difference_qty > 0)
            deficit = lines.filtered(lambda l: l.difference_qty < 0)
            rec.total_surplus_items = len(surplus)
            rec.total_deficit_items = len(deficit)
            rec.total_surplus_value = sum(surplus.mapped('difference_value'))
            rec.total_deficit_value = abs(sum(deficit.mapped('difference_value')))

    def action_load_stock(self):
        """Load current stock quantities into lines from Odoo quants."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('يمكن تحميل المخزون في مرحلة المسودة فقط'))
            domain = [
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0),
            ]
            if rec.warehouse_id:
                wh_locations = self.env['stock.location'].search([
                    ('complete_name', 'like', rec.warehouse_id.name),
                    ('usage', '=', 'internal'),
                ])
                domain.append(('location_id', 'in', wh_locations.ids))
            if rec.location_id:
                domain = [
                    ('location_id', '=', rec.location_id.id),
                    ('quantity', '>', 0),
                ]
            quants = self.env['stock.quant'].search(domain)
            existing = {l.product_id.id: l for l in rec.line_ids}
            new_lines = []
            for quant in quants:
                if quant.product_id.id not in existing:
                    new_lines.append({
                        'session_id': rec.id,
                        'product_id': quant.product_id.id,
                        'system_qty': quant.quantity,
                        'physical_qty': quant.quantity,
                        'standard_cost': quant.product_id.standard_price,
                    })
                else:
                    existing[quant.product_id.id].write({
                        'system_qty': quant.quantity,
                        'standard_cost': quant.product_id.standard_price,
                    })
            if new_lines:
                self.env['stock.stocktaking.line'].create(new_lines)
            rec.write({'state': 'counting'})
            rec.message_post(body=_('📦 تم تحميل %d صنف من المخزون الحالي') % len(quants))

    def action_post(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('يجب إضافة أصناف الجرد قبل الترحيل'))
            rec.write({'state': 'done'})
            rec.message_post(
                body=_('✅ تم الجرد: %d صنف — زيادة: %d — عجز: %d') % (
                    rec.total_items, rec.total_surplus_items, rec.total_deficit_items
                )
            )

    def action_validate(self):
        for rec in self:
            if rec.state != 'done':
                raise UserError(_('يجب ترحيل الجرد أولاً'))
            rec.write({'state': 'validated'})
            rec.message_post(body=_('🔒 تم اعتماد الجرد من رئيس اللجنة'))

    def action_print_form6(self):
        return self.env.ref('stock_stocktaking_eg.action_report_form6').report_action(self)

    def action_print_surplus_deficit(self):
        return self.env.ref('stock_stocktaking_eg.action_report_surplus_deficit').report_action(self)


class StocktakingLine(models.Model):
    """سطر الجرد — Stocktaking Line (one per item)"""
    _name = 'stock.stocktaking.line'
    _description = 'سطر جرد - Stocktaking Line'
    _order = 'session_id, product_id'

    session_id = fields.Many2one(
        'stock.stocktaking.session', string='جلسة الجرد',
        required=True, ondelete='cascade', index=True,
    )
    product_id = fields.Many2one(
        'product.product', string='الصنف', required=True,
    )
    product_code = fields.Char(related='product_id.default_code', store=True, string='كود الصنف')
    uom_id = fields.Many2one(related='product_id.uom_id', store=True, string='الوحدة')

    # Core Form 6 fields
    system_qty = fields.Float(
        string='الكمية بالسجلات (نظام)',
        digits='Product Unit of Measure',
        help='Quantity per Odoo system / accounting books',
    )
    physical_qty = fields.Float(
        string='الكمية الفعلية (جرد)',
        digits='Product Unit of Measure',
        help='Actual physical count during stocktaking',
    )
    difference_qty = fields.Float(
        string='الفرق (زيادة / عجز)',
        compute='_compute_difference', store=True,
        digits='Product Unit of Measure',
    )
    standard_cost = fields.Float(
        string='سعر الوحدة', digits='Account',
    )
    difference_value = fields.Float(
        string='قيمة الفرق', compute='_compute_difference',
        store=True, digits='Account',
    )
    difference_type = fields.Selection([
        ('none',    'لا فرق'),
        ('surplus', 'زيادة'),
        ('deficit', 'عجز'),
    ], string='نوع الفرق', compute='_compute_difference', store=True)

    notes = fields.Char(string='ملاحظات / سبب الفرق')

    _sql_constraints = [
        ('product_session_uniq', 'unique(session_id, product_id)',
         'لا يمكن إضافة نفس الصنف مرتين في جلسة جرد واحدة'),
    ]

    @api.depends('system_qty', 'physical_qty', 'standard_cost')
    def _compute_difference(self):
        for line in self:
            diff = line.physical_qty - line.system_qty
            line.difference_qty = diff
            line.difference_value = diff * line.standard_cost
            if diff > 0:
                line.difference_type = 'surplus'
            elif diff < 0:
                line.difference_type = 'deficit'
            else:
                line.difference_type = 'none'
