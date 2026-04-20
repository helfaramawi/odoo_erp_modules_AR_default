# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockTransferPermitLine(models.Model):
    _name = 'stock.transfer.permit.line'
    _description = 'سطر إذن التحويل'
    _order = 'sequence, id'

    permit_id = fields.Many2one('stock.transfer.permit', ondelete='cascade')
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='الصنف', required=True)
    product_code = fields.Char(related='product_id.default_code', string='كود الصنف', store=True)
    uom_id = fields.Many2one('uom.uom', string='وحدة القياس')
    qty = fields.Float(string='الكمية', required=True, default=1.0)
    unit_price = fields.Float(string='سعر الوحدة')
    total_value = fields.Float(string='الإجمالي', compute='_compute_total', store=True)
    serial_lot = fields.Char(string='رقم السيريال / اللوت')
    condition = fields.Selection([
        ('good', 'جيد'),
        ('damaged', 'تالف'),
    ], string='الحالة', default='good')
    notes = fields.Char(string='ملاحظات')

    @api.depends('qty', 'unit_price')
    def _compute_total(self):
        for line in self:
            line.total_value = line.qty * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.unit_price = self.product_id.standard_price


class StockTransferPermit(models.Model):
    _name = 'stock.transfer.permit'
    _description = 'إذن التحويل بين المخازن'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transfer_date desc, id desc'

    name = fields.Char(string='رقم الإذن', readonly=True, default='جديد')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('submitted', 'مقدّم'),
        ('approved', 'معتمد'),
        ('posted', 'مرحّل'),
        ('received', 'مستلم'),
        ('cancelled', 'ملغي'),
    ], default='draft', string='الحالة', tracking=True)

    transfer_date = fields.Date(string='تاريخ التحويل', default=fields.Date.today)
    fiscal_year = fields.Char(string='السنة المالية')
    transfer_reason = fields.Text(string='سبب التحويل')

    from_warehouse_id = fields.Many2one('stock.warehouse', string='من المستودع', required=True)
    from_location_id = fields.Many2one('stock.location', string='من الموقع',
                                        domain="[('usage','=','internal')]")
    from_dept = fields.Char(string='من القسم')
    from_storekeeper_id = fields.Many2one('hr.employee', string='أمين مخزن المصدر')

    to_warehouse_id = fields.Many2one('stock.warehouse', string='إلى المستودع', required=True)
    to_location_id = fields.Many2one('stock.location', string='إلى الموقع',
                                      domain="[('usage','=','internal')]")
    to_dept = fields.Char(string='إلى القسم')
    to_storekeeper_id = fields.Many2one('hr.employee', string='أمين مخزن الهدف')

    fixed_asset_id = fields.Many2one('port_said.fixed.asset', string='أصل ثابت')
    custody_id = fields.Many2one('custody.assignment', string='عهدة')

    line_ids = fields.One2many('stock.transfer.permit.line', 'permit_id', string='الأصناف')
    notes = fields.Text(string='ملاحظات')

    total_lines = fields.Integer(string='عدد الأصناف', compute='_compute_totals', store=True)
    total_value = fields.Float(string='القيمة الإجمالية', compute='_compute_totals', store=True)
    picking_id = fields.Many2one('stock.picking', string='حركة المخزن', readonly=True)
    approved_by = fields.Many2one('res.users', string='معتمد بواسطة', readonly=True)
    received_by = fields.Many2one('res.users', string='مستلم بواسطة', readonly=True)

    @api.depends('line_ids', 'line_ids.total_value')
    def _compute_totals(self):
        for rec in self:
            rec.total_lines = len(rec.line_ids)
            rec.total_value = sum(rec.line_ids.mapped('total_value'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer.permit') or 'TP/NEW'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved', 'approved_by': self.env.user.id})

    def action_post(self):
        self.write({'state': 'posted'})

    def action_receive(self):
        self.write({'state': 'received', 'received_by': self.env.user.id})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_create_journal_entry(self):
        self.ensure_one()
