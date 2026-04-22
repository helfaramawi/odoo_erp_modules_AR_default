# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockIssuePermitLine(models.Model):
    _name = 'stock.issue.permit.line'
    _description = 'سطر إذن الصرف'
    _order = 'sequence, id'

    permit_id = fields.Many2one('stock.issue.permit', ondelete='cascade')
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='الصنف', required=True)
    product_code = fields.Char(related='product_id.default_code', string='كود الصنف', store=True)
    uom_id = fields.Many2one('uom.uom', string='وحدة القياس')
    qty_available = fields.Float(string='المتاح', compute='_compute_qty_available')
    qty_requested = fields.Float(string='الكمية المطلوبة', required=True, default=1.0)
    qty_issued = fields.Float(string='الكمية المصروفة', default=0.0)
    unit_price = fields.Float(string='سعر الوحدة')
    total_value = fields.Float(string='الإجمالي', compute='_compute_total', store=True)
    custody_assignment_id = fields.Many2one('custody.assignment', string='عهدة')
    fixed_asset_id = fields.Many2one('port_said.fixed.asset', string='أصل ثابت')
    notes = fields.Char(string='ملاحظات')

    @api.depends('product_id', 'permit_id.location_id')
    def _compute_qty_available(self):
        for line in self:
            if line.product_id and line.permit_id.location_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.permit_id.location_id.id),
                ])
                line.qty_available = sum(quants.mapped('quantity'))
            else:
                line.qty_available = 0.0

    @api.depends('qty_issued', 'qty_requested', 'unit_price')
    def _compute_total(self):
        for line in self:
            qty = line.qty_issued if line.qty_issued else line.qty_requested
            line.total_value = qty * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.unit_price = self.product_id.standard_price


class StockIssueRegisterLine(models.Model):
    """
    سجل حركات الصرف المخزوني
    يُنشأ تلقائياً عند ترحيل إذن الصرف — يُمثِّل قيداً في سجل حركات الصرف.
    هذا النموذج منفصل تماماً عن دفتر 55 ع.ح (port_said.daftar55)
    الذي هو سجل مدفوعات للموردين وليس سجل صرف مخزوني.
    """
    _name = 'stock.issue.register.line'
    _description = 'سجل حركات الصرف المخزوني'
    _order = 'sequence_number desc'
    _rec_name = 'sequence_number'
    _inherit = ['mail.thread']

    sequence_number = fields.Char(
        string='رقم المسلسل',
        readonly=True, copy=False, index=True,
    )
    fiscal_year = fields.Char(string='السنة المالية', readonly=True, copy=False)

    issue_permit_id = fields.Many2one(
        'stock.issue.permit', string='إذن الصرف المصدر',
        readonly=True, ondelete='restrict',
    )
    issue_date = fields.Date(string='تاريخ الصرف', readonly=True)
    issue_type = fields.Char(string='نوع الصرف', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='المستودع', readonly=True)
    requesting_dept = fields.Char(string='الإدارة الطالبة', readonly=True)
    form50_ref = fields.Char(string='رقم استمارة 50', readonly=True)
    purpose = fields.Char(string='الغرض', readonly=True)
    storekeeper_id = fields.Many2one('hr.employee', string='أمين المخزن', readonly=True)

    total_value = fields.Monetary(
        string='القيمة الإجمالية', readonly=True,
        currency_field='currency_id',
    )
    journal_entry_id = fields.Many2one(
        'account.move', string='القيد المحاسبي',
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id,
    )
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
    )
    notes = fields.Text(string='ملاحظات')

    _sql_constraints = [
        ('unique_permit', 'UNIQUE(issue_permit_id)',
         'يوجد قيد سجل مسبق لهذا الإذن — لا يمكن إنشاء قيدين لنفس إذن الصرف.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence_number'):
                vals['sequence_number'] = (
                    self.env['ir.sequence'].next_by_code('stock.issue.register') or '/'
                )
                vals['fiscal_year'] = str(fields.Date.today().year)
        return super().create(vals_list)

    def unlink(self):
        raise UserError(_('لا يمكن حذف سجلات الصرف — لائحة المالية المصرية.'))

    def write(self, vals):
        if 'sequence_number' in vals:
            raise ValidationError(_('لا يمكن تعديل رقم المسلسل بعد الإنشاء.'))
        return super().write(vals)


class StockIssuePermit(models.Model):
    _name = 'stock.issue.permit'
    _description = 'إذن الصرف — نموذج 2 مخازن'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, id desc'

    name = fields.Char(string='رقم الإذن', readonly=True, default='جديد')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('submitted', 'مقدّم'),
        ('approved', 'معتمد'),
        ('posted', 'مرحّل'),
        ('cancelled', 'ملغي'),
    ], default='draft', string='الحالة', tracking=True)

    issue_date = fields.Date(string='تاريخ الإذن', default=fields.Date.today)
    issue_type = fields.Selection([
        ('consumption', 'استهلاك'),
        ('custody', 'عهدة'),
        ('project', 'مشروع'),
        ('maintenance', 'صيانة'),
        ('other', 'أخرى'),
    ], string='نوع الصرف', default='consumption', required=True)
    fiscal_year = fields.Char(string='السنة المالية')

    # ── استمارة 50 — المرجع الإلزامي ────────────────────────────────────────
    # reference_no: رقم استمارة 50 المعتمدة — إلزامي قبل التقديم للاعتماد
    reference_no = fields.Char(string='رقم استمارة 50')

    requesting_dept = fields.Char(string='الجهة / القسم الطالب')
    requesting_employee_id = fields.Many2one('hr.employee', string='الموظف الطالب')
    receiving_employee_id = fields.Many2one('hr.employee', string='الموظف المستلم')
    purpose = fields.Char(string='الغرض')

    warehouse_id = fields.Many2one('stock.warehouse', string='المستودع', required=True)
    location_id = fields.Many2one('stock.location', string='موقع المخزن',
                                   domain="[('usage','=','internal')]")
    location_dest_id = fields.Many2one('stock.location', string='موقع الوجهة',
                                        domain="[('usage','in',['internal','customer'])]")
    storekeeper_id = fields.Many2one('hr.employee', string='أمين المخزن')
    commitment_id = fields.Many2one('port_said.commitment', string='الارتباط المرتبط')
    # daftar55_id: محتفظ به مؤقتاً لتجنب خطأ الـ view القديمة في الـ DB
    # هذا الحقل لا يُستخدم وظيفياً — سيُحذف بعد تنظيف الـ DB
    daftar55_id = fields.Many2one(
        'port_said.daftar55', string='دفتر 55 (قديم)',
        readonly=True, copy=False,
    )

    # ── سجل الصرف المخزوني — يُنشأ تلقائياً عند الترحيل ────────────────────
    # ملاحظة: هذا ليس دفتر 55 ع.ح — دفتر 55 هو سجل مدفوعات للموردين
    # هذا الحقل يُشير لسجل حركات الصرف المخزوني (stock.issue.register.line)
    issue_register_line_id = fields.Many2one(
        'stock.issue.register.line',
        string='قيد سجل الصرف',
        readonly=True, copy=False,
        help='يُملأ تلقائياً عند ترحيل إذن الصرف — رقم مسلسل في سجل حركات الصرف المخزوني',
    )
    issue_register_serial = fields.Char(
        string='رقم مسلسل سجل الصرف',
        related='issue_register_line_id.sequence_number',
        store=False, readonly=True,
    )

    line_ids = fields.One2many('stock.issue.permit.line', 'permit_id', string='الأصناف')
    notes = fields.Text(string='ملاحظات')

    total_lines = fields.Integer(string='عدد الأصناف', compute='_compute_totals', store=True)
    total_value = fields.Float(string='القيمة الإجمالية', compute='_compute_totals', store=True)

    picking_id = fields.Many2one('stock.picking', string='حركة المخزن', readonly=True)
    journal_entry_id = fields.Many2one('account.move', string='القيد المحاسبي', readonly=True, copy=False)
    journal_entry_state = fields.Selection(related='journal_entry_id.state', string='حالة القيد')
    approved_by = fields.Many2one('res.users', string='معتمد بواسطة', readonly=True)
    approval_date = fields.Datetime(string='تاريخ الاعتماد', readonly=True)

    @api.depends('line_ids', 'line_ids.total_value')
    def _compute_totals(self):
        for rec in self:
            rec.total_lines = len(rec.line_ids)
            rec.total_value = sum(rec.line_ids.mapped('total_value'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.issue.permit') or 'IP/NEW'
        return super().create(vals_list)

    def action_submit(self):
        """تقديم للاعتماد — مع التحقق من الحقول الإلزامية"""
        for rec in self:
            if not rec.reference_no:
                raise UserError(_(
                    'يجب إدخال رقم استمارة 50 قبل تقديم إذن الصرف للاعتماد.\n'
                    'استمارة 50 هي طلب الصرف المعتمد الذي يُخوِّل عملية الصرف.'
                ))
            if not rec.requesting_dept:
                raise UserError(_('يجب تحديد الجهة / القسم الطالب.'))
            if not rec.purpose:
                raise UserError(_('يجب تحديد الغرض من الصرف.'))
            if not rec.line_ids:
                raise UserError(_('لا يمكن تقديم إذن الصرف بدون أصناف.'))
            for line in rec.line_ids:
                if line.qty_requested <= 0:
                    raise UserError(_(
                        f'الكمية المطلوبة للصنف "{line.product_id.name}" يجب أن تكون أكبر من صفر.'
                    ))
        self.write({'state': 'submitted'})

    def action_approve(self):
        """الاعتماد — مع التحقق من توافر المخزون"""
        for rec in self:
            for line in rec.line_ids:
                if line.qty_available < line.qty_requested:
                    raise UserError(_(
                        f'الكمية المتاحة للصنف "{line.product_id.name}" '
                        f'({line.qty_available:.2f}) أقل من الكمية المطلوبة ({line.qty_requested:.2f}).\n'
                        'يرجى مراجعة المخزون أو تعديل الكمية المطلوبة.'
                    ))
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })

    def action_post(self):
        """
        ترحيل إذن الصرف — تنفيذ الصرف الفعلي.
        عند الترحيل:
          1. يتحقق من الحقول الإلزامية
          2. يُنشئ سطراً تلقائياً في سجل حركات الصرف المخزوني
        ملاحظة: القيد المحاسبي يُنشأ لاحقاً بشكل منفصل من زر "إنشاء قيد محاسبي"
        """
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('لا يمكن الترحيل بدون أصناف.'))
            if not rec.receiving_employee_id:
                raise UserError(_('يجب تحديد الموظف المستلم قبل الترحيل.'))
            for line in rec.line_ids:
                if line.unit_price <= 0:
                    raise UserError(_(
                        f'سعر الوحدة للصنف "{line.product_id.name}" يجب أن يكون أكبر من صفر.\n'
                        'يرجى تحديث سعر الصنف في دليل الأصناف.'
                    ))
            # التحقق من عدم وجود قيد سجل مسبق (حماية من التكرار)
            if rec.issue_register_line_id:
                raise UserError(_(
                    'يوجد قيد سجل صرف مسبق لهذا الإذن. لا يمكن الترحيل مرتين.'
                ))

            # إنشاء سطر سجل الصرف تلقائياً
            issue_type_label = dict(rec._fields['issue_type'].selection).get(rec.issue_type, rec.issue_type)
            register_line = self.env['stock.issue.register.line'].create({
                'issue_permit_id': rec.id,
                'issue_date': rec.issue_date,
                'issue_type': issue_type_label,
                'warehouse_id': rec.warehouse_id.id if rec.warehouse_id else False,
                'requesting_dept': rec.requesting_dept,
                'form50_ref': rec.reference_no,
                'purpose': rec.purpose,
                'storekeeper_id': rec.storekeeper_id.id if rec.storekeeper_id else False,
                'total_value': rec.total_value,
            })

            rec.write({
                'state': 'posted',
                'issue_register_line_id': register_line.id,
            })
            rec.message_post(body=_(
                f'تم ترحيل إذن الصرف وإنشاء قيد سجل الصرف رقم: {register_line.sequence_number}'
            ))

    def action_cancel(self):
        for rec in self:
            if rec.state == 'posted' and rec.journal_entry_id:
                raise UserError(_(
                    'لا يمكن إلغاء إذن صرف مرحَّل بعد إنشاء قيده المحاسبي.\n'
                    'يرجى إلغاء القيد المحاسبي أولاً.'
                ))
        self.write({'state': 'cancelled'})

    def action_create_journal_entry(self):
        """Placeholder — الميثود الحقيقية في port_said_stock_finance_bridge/bridge_engine.py"""
        from odoo.exceptions import UserError
        raise UserError(_('وحدة ربط المخزون بالحسابات غير مثبتة'))

    def action_view_journal_entry(self):
        self.ensure_one()
        if self.journal_entry_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': self.journal_entry_id.id,
                'view_mode': 'form',
            }

    def action_view_register_line(self):
        """فتح قيد سجل الصرف المرتبط"""
        self.ensure_one()
        if self.issue_register_line_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.issue.register.line',
                'res_id': self.issue_register_line_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
