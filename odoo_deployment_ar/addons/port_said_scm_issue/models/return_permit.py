# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockReturnPermitLine(models.Model):
    _name = 'stock.return.permit.line'
    _description = 'سطر إذن الارتجاع'
    _order = 'sequence, id'

    permit_id = fields.Many2one('stock.return.permit', ondelete='cascade')
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='الصنف', required=True)
    product_code = fields.Char(related='product_id.default_code', string='كود الصنف', store=True)
    uom_id = fields.Many2one('uom.uom', string='وحدة القياس')
    qty_original = fields.Float(string='الكمية الأصلية')
    qty_returned = fields.Float(string='الكمية المرتجعة', required=True, default=1.0)
    unit_price = fields.Float(string='سعر الوحدة')
    total_value = fields.Float(string='الإجمالي', compute='_compute_total', store=True)
    condition = fields.Selection([
        ('good', 'جيد'),
        ('damaged', 'تالف'),
        ('partial', 'جزئي'),
    ], string='الحالة', default='good')
    serial_lot = fields.Char(string='رقم السيريال / اللوت')
    notes = fields.Char(string='ملاحظات')

    @api.depends('qty_returned', 'unit_price')
    def _compute_total(self):
        for line in self:
            line.total_value = line.qty_returned * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.unit_price = self.product_id.standard_price


class StockReturnPermit(models.Model):
    _name = 'stock.return.permit'
    _description = 'إذن الارتجاع — نموذج 8 مخازن'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'return_date desc, id desc'

    name = fields.Char(string='رقم الإذن', readonly=True, default='جديد')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('submitted', 'مقدّم'),
        ('committee', 'لجنة الفحص'),
        ('approved', 'معتمد'),
        ('posted', 'مرحّل'),
        ('cancelled', 'ملغي'),
    ], default='draft', string='الحالة', tracking=True)

    return_date = fields.Date(string='تاريخ الارتجاع', default=fields.Date.today)
    return_type = fields.Selection([
        ('consumption', 'من استهلاك'),
        ('custody', 'من عهدة'),
        ('project', 'من مشروع'),
        ('other', 'أخرى'),
    ], string='نوع الارتجاع', default='consumption', required=True)
    fiscal_year = fields.Char(string='السنة المالية')

    returning_dept = fields.Char(string='الجهة / القسم المُرتجِع')
    returning_employee_id = fields.Many2one('hr.employee', string='الموظف المُرتجِع')
    original_issue_id = fields.Many2one('stock.issue.permit', string='إذن الصرف الأصلي')

    warehouse_id = fields.Many2one('stock.warehouse', string='المستودع', required=True)
    location_id = fields.Many2one('stock.location', string='موقع المخزن',
                                   domain="[('usage','=','internal')]")
    storekeeper_id = fields.Many2one('hr.employee', string='أمين المخزن')
    return_reason = fields.Text(string='سبب الارتجاع')

    needs_committee = fields.Boolean(string='يحتاج لجنة فحص', default=False)
    committee_chairman_id = fields.Many2one('hr.employee', string='رئيس اللجنة')
    committee_member1_id = fields.Many2one('hr.employee', string='عضو 1')
    committee_member2_id = fields.Many2one('hr.employee', string='عضو 2')
    committee_decision = fields.Text(string='قرار اللجنة')

    line_ids = fields.One2many('stock.return.permit.line', 'permit_id', string='الأصناف')
    notes = fields.Text(string='ملاحظات')

    total_lines = fields.Integer(string='عدد الأصناف', compute='_compute_totals', store=True)
    total_value = fields.Float(string='القيمة الإجمالية', compute='_compute_totals', store=True)
    picking_id = fields.Many2one('stock.picking', string='حركة المخزن', readonly=True)
    approved_by = fields.Many2one('res.users', string='معتمد بواسطة', readonly=True)

    @api.depends('line_ids', 'line_ids.total_value')
    def _compute_totals(self):
        for rec in self:
            rec.total_lines = len(rec.line_ids)
            rec.total_value = sum(rec.line_ids.mapped('total_value'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.return.permit') or 'RP/NEW'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_committee_done(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved', 'approved_by': self.env.user.id})

    def action_post(self):
        self.write({'state': 'posted'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_create_journal_entry(self):
        self.ensure_one()
