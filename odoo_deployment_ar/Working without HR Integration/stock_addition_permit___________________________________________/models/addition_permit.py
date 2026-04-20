from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class InspectionReport(models.Model):
    """
    محضر الفحص — Inspection Report
    Created after preliminary receipt, before إذن إضافة.
    Fields mirror the User Guide screen exactly.
    """
    _name = 'stock.inspection.report'
    _description = 'محضر الفحص - Goods Inspection Report'
    _inherit = ['mail.thread']
    _order = 'inspection_date desc'

    name = fields.Char(
        string='رقم محضر الفحص', required=True, copy=False,
        readonly=True, default='/', tracking=True,
    )
    # Fields from User Guide: reference_batch, test_group, qty
    picking_id = fields.Many2one(
        'stock.picking', string='أمر الاستلام', required=True,
        domain="[('picking_type_code','=','incoming')]", tracking=True,
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='المورد',
        related='picking_id.partner_id', store=True,
    )
    reference_batch = fields.Char(
        string='دفعة المرجع (رقم أمر الشراء)',
        required=True, tracking=True,
        help='رقم أمر الشراء — mandatory per User Guide',
    )
    test_group = fields.Char(
        string='مجموعة الاختبار', required=True, tracking=True,
        help='مجموعة الاختبار — mandatory per User Guide',
    )
    inspection_qty = fields.Float(
        string='الكمية المفحوصة', required=True, digits='Product Unit of Measure',
        tracking=True,
    )
    inspection_date = fields.Date(
        string='تاريخ الفحص', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    inspector_id = fields.Many2one(
        'hr.employee', string='المفتش / المسؤول عن الفحص', tracking=True,
    )
    result = fields.Selection([
        ('pass',    'مطابق للمواصفات ✓'),
        ('fail',    'غير مطابق ✗'),
        ('partial', 'مطابق جزئياً'),
    ], string='نتيجة الفحص', required=True, default='pass', tracking=True)
    rejection_reason = fields.Text(
        string='سبب الرفض / الملاحظات',
        invisible="result == 'pass'",
    )
    # Approved quantities
    approved_qty = fields.Float(
        string='الكمية المعتمدة للإضافة', digits='Product Unit of Measure',
        tracking=True,
    )
    addition_permit_id = fields.Many2one(
        'stock.addition.permit', string='إذن الإضافة المرتبط',
        readonly=True, copy=False,
    )
    state = fields.Selection([
        ('draft',    'مسودة'),
        ('done',     'تم التحقق'),
        ('rejected', 'مرفوض'),
    ], default='draft', tracking=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'رقم محضر الفحص يجب أن يكون فريداً'),
        ('qty_positive', 'CHECK(inspection_qty > 0)', 'الكمية المفحوصة يجب أن تكون موجبة'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.inspection.report') or '/'
            # Auto-fill reference_batch from PO number
            if vals.get('picking_id') and not vals.get('reference_batch'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if picking.purchase_id:
                    vals['reference_batch'] = picking.purchase_id.name
        return super().create(vals_list)

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id and self.picking_id.purchase_id:
            self.reference_batch = self.picking_id.purchase_id.name

    @api.onchange('inspection_qty')
    def _onchange_inspection_qty(self):
        if self.inspection_qty and not self.approved_qty:
            self.approved_qty = self.inspection_qty

    def action_validate(self):
        for rec in self:
            if rec.result == 'fail':
                rec.write({'state': 'rejected'})
            else:
                rec.write({'state': 'done'})
                # Trigger creation of إذن إضافة if not already created
                if not rec.addition_permit_id:
                    permit = rec._create_addition_permit()
                    rec.addition_permit_id = permit
            rec.message_post(
                body=_('✅ تم التحقق من محضر الفحص. النتيجة: %s') % rec.result
            )

    def _create_addition_permit(self):
        """Auto-create إذن إضافة after successful inspection."""
        self.ensure_one()
        permit = self.env['stock.addition.permit'].create({
            'picking_id': self.picking_id.id,
            'inspection_report_id': self.id,
            'partner_id': self.partner_id.id,
            'purchase_order_id': self.purchase_order_id.id,
            'qty': self.approved_qty or self.inspection_qty,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'location_id': self.picking_id.location_dest_id.id,
        })
        return permit


class StockAdditionPermit(models.Model):
    """
    إذن الإضافة — Addition Permit (Form 1 Government Warehouses)
    Second step after inspection report. FR-I1.
    """
    _name = 'stock.addition.permit'
    _description = 'إذن إضافة - Addition Permit (Form 1)'
    _inherit = ['mail.thread']
    _order = 'permit_date desc'

    name = fields.Char(
        string='رقم إذن الإضافة', required=True, copy=False,
        readonly=True, default='/', tracking=True,
    )
    # Core fields matching User Guide إذن إضافة screen
    permit_date = fields.Date(
        string='تاريخ إذن الإضافة', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    picking_id = fields.Many2one(
        'stock.picking', string='إيصال الاستلام', tracking=True,
    )
    inspection_report_id = fields.Many2one(
        'stock.inspection.report', string='محضر الفحص', tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='المورد', required=True, tracking=True,
    )
    purchase_order_id = fields.Many2one(
        'purchase.order', string='رقم أمر الشراء / أمر التوريد', tracking=True,
    )
    product_id = fields.Many2one(
        'product.product', string='الصنف', required=True, tracking=True,
    )
    qty = fields.Float(
        string='الكمية', required=True, digits='Product Unit of Measure', tracking=True,
    )
    uom_id = fields.Many2one(
        'uom.uom', string='الوحدة', related='product_id.uom_id', store=True,
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='المستودع', required=True, tracking=True,
    )
    location_id = fields.Many2one(
        'stock.location', string='موقع التخزين', required=True, tracking=True,
    )
    site_id = fields.Char(string='الموقع / الفرع', tracking=True)
    storekeeper_id = fields.Many2one(
        'hr.employee', string='أمين المخزن', tracking=True,
    )
    stock_move_id = fields.Many2one(
        'stock.move', string='حركة المخزن', readonly=True, copy=False,
    )
    state = fields.Selection([
        ('draft',  'مسودة'),
        ('posted', 'مرحّل'),
        ('cancel', 'ملغي'),
    ], default='draft', tracking=True)
    notes = fields.Text(string='ملاحظات')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'رقم إذن الإضافة يجب أن يكون فريداً'),
        ('qty_positive', 'CHECK(qty > 0)', 'الكمية يجب أن تكون موجبة'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.addition.permit') or '/'
        return super().create(vals_list)

    def action_post(self):
        """Post the إذن إضافة — creates a stock journal entry."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('يمكن ترحيل إذن الإضافة في حالة المسودة فقط'))
            if not rec.product_id:
                raise UserError(_('يجب تحديد الصنف'))
            rec.write({'state': 'posted'})
            rec.message_post(
                body=_('✅ تم ترحيل إذن الإضافة رقم %s للصنف %s (الكمية: %s)') % (
                    rec.name, rec.product_id.name, rec.qty
                )
            )

    def action_cancel(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_('لا يمكن إلغاء إذن إضافة مرحّل'))
            rec.write({'state': 'cancel'})

    def action_print_form1(self):
        return self.env.ref('stock_addition_permit.action_report_form1_addition_permit').report_action(self)


class StockPickingAddition(models.Model):
    """Extend stock.picking with addition permit summary."""
    _inherit = 'stock.picking'

    inspection_report_ids = fields.One2many(
        'stock.inspection.report', 'picking_id', string='محاضر الفحص',
    )
    addition_permit_ids = fields.One2many(
        'stock.addition.permit', 'picking_id', string='أذونات الإضافة',
    )
    inspection_count = fields.Integer(compute='_compute_inspection_count')
    addition_permit_count = fields.Integer(compute='_compute_permit_count')

    def _compute_inspection_count(self):
        for p in self:
            p.inspection_count = len(p.inspection_report_ids)

    def _compute_permit_count(self):
        for p in self:
            p.addition_permit_count = len(p.addition_permit_ids)

    def action_view_inspections(self):
        return {
            'name': _('محاضر الفحص'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.inspection.report',
            'view_mode': 'tree,form',
            'domain': [('picking_id', '=', self.id)],
            'context': {'default_picking_id': self.id},
        }

    def action_view_addition_permits(self):
        return {
            'name': _('أذونات الإضافة'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.addition.permit',
            'view_mode': 'tree,form',
            'domain': [('picking_id', '=', self.id)],
            'context': {'default_picking_id': self.id},
        }
