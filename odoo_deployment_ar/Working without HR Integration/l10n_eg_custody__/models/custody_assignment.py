from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import re


class CustodyAssignment(models.Model):
    """
    إدارة العهد — Custody Assignment
    Tracks durable items (مستديم) assigned to government employees.
    GAFI-audited annually. Form 193 (ع.ح) is the legal document.
    """
    _name = 'custody.assignment'
    _description = 'إذن صرف العهدة - Custody Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, name desc'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='رقم العهدة',
        required=True,
        copy=False,
        readonly=True,
        default='/',
        tracking=True,
    )
    form_193_ref = fields.Char(
        string='رقم استمارة 193',
        required=True,
        tracking=True,
        help='Government Form 193 (ع.ح) serial number — required for GAFI audit',
    )

    # ── Employee (mandatory for GAFI) ─────────────────────────────────────────
    employee_id = fields.Many2one(
        'hr.employee',
        string='الموظف المستلم',
        required=True,
        tracking=True,
        domain="[('active', '=', True)]",
    )
    national_id = fields.Char(
        string='الرقم القومي',
        required=True,
        tracking=True,
        help='MANDATORY for GAFI audit — Egyptian National ID (14 digits)',
    )
    employee_department_id = fields.Many2one(
        'hr.department',
        string='الإدارة / القسم',
        related='employee_id.department_id',
        store=True,
        tracking=True,
    )
    employee_job_id = fields.Many2one(
        'hr.job',
        string='الوظيفة',
        related='employee_id.job_id',
        store=True,
    )

    # ── Item ──────────────────────────────────────────────────────────────────
    product_id = fields.Many2one(
        'product.product',
        string='الصنف',
        required=True,
        tracking=True,
        domain="[('type', 'in', ['product', 'consu'])]",
    )
    product_description = fields.Html(
        string='وصف الصنف',
        related='product_id.description',
        store=True,
    )
    qty = fields.Float(
        string='الكمية',
        required=True,
        default=1.0,
        tracking=True,
        digits='Product Unit of Measure',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='الوحدة',
        related='product_id.uom_id',
        store=True,
    )
    serial_number = fields.Char(
        string='الرقم التسلسلي / الكودي',
        tracking=True,
        help='Serial or asset code for durable items',
    )
    estimated_value = fields.Float(
        string='القيمة التقديرية',
        digits='Account',
        tracking=True,
        help='Estimated value for insurance purposes (GAFI requirement)',
    )

    # ── Custody Type ──────────────────────────────────────────────────────────
    custody_type = fields.Selection([
        ('sub', 'عهدة فرعية - Sub-custody'),
        ('location', 'عهدة مكانية - Location-based Custody'),
        ('personal', 'عهدة شخصية - Personal Custody'),
    ], string='نوع العهدة', required=True, default='personal', tracking=True)

    # ── Warehouse / Location ──────────────────────────────────────────────────
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='المخزن',
        required=True,
        tracking=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='موقع التخزين',
        tracking=True,
    )

    # ── Dates ─────────────────────────────────────────────────────────────────
    issue_date = fields.Date(
        string='تاريخ الصرف',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    expected_return_date = fields.Date(
        string='تاريخ الاسترداد المتوقع',
        tracking=True,
    )
    actual_return_date = fields.Date(
        string='تاريخ الاسترداد الفعلي',
        tracking=True,
    )

    # ── Responsible Officials (Form 193 mandatory signatures) ─────────────────
    storekeeper_id = fields.Many2one(
        'hr.employee',
        string='أمين المخزن',
        required=True,
        tracking=True,
        help='Storekeeper who issued the custody — signature on Form 193',
    )
    dept_manager_id = fields.Many2one(
        'hr.employee',
        string='مدير الإدارة',
        required=True,
        tracking=True,
        help='Department manager countersignature — mandatory on Form 193',
    )
    issued_by_id = fields.Many2one(
        'res.users',
        string='أصدرها',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
    )

    # ── Source Document ───────────────────────────────────────────────────────
    stock_move_id = fields.Many2one(
        'stock.move',
        string='حركة المخزن المرتبطة',
        readonly=True,
        copy=False,
    )
    issue_permit_ref = fields.Char(
        string='رقم إذن الصرف',
        tracking=True,
        help='Reference to the إذن صرف that triggered this custody',
    )

    # ── State Machine ─────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('active', 'نشطة'),
        ('transferred', 'محولة'),
        ('returned', 'مستردة'),
        ('cancelled', 'ملغية'),
    ], string='الحالة', default='draft', required=True, tracking=True, index=True)

    # ── Transfer History ──────────────────────────────────────────────────────
    transfer_ids = fields.One2many(
        'custody.transfer',
        'custody_assignment_id',
        string='سجل تحويلات العهدة',
    )
    transfer_count = fields.Integer(
        string='عدد التحويلات',
        compute='_compute_transfer_count',
    )
    current_holder_id = fields.Many2one(
        'hr.employee',
        string='الحائز الحالي',
        compute='_compute_current_holder',
        store=True,
        tracking=True,
    )

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes = fields.Text(string='ملاحظات')

    # ── SQL Constraints ───────────────────────────────────────────────────────
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'رقم العهدة يجب أن يكون فريداً'),
        ('form_193_uniq', 'unique(form_193_ref)', 'رقم استمارة 193 يجب أن يكون فريداً'),
        ('qty_positive', 'CHECK(qty > 0)', 'الكمية يجب أن تكون أكبر من الصفر'),
    ]

    # ── Computed ──────────────────────────────────────────────────────────────
    @api.depends('transfer_ids')
    def _compute_transfer_count(self):
        for rec in self:
            rec.transfer_count = len(rec.transfer_ids)

    @api.depends('transfer_ids', 'transfer_ids.state', 'employee_id')
    def _compute_current_holder(self):
        for rec in self:
            done_transfers = rec.transfer_ids.filtered(
                lambda t: t.state == 'done'
            ).sorted('transfer_date', reverse=True)
            rec.current_holder_id = done_transfers[0].to_employee_id if done_transfers else rec.employee_id

    # ── Constraints ───────────────────────────────────────────────────────────
    @api.constrains('national_id')
    def _check_national_id(self):
        for rec in self:
            if rec.national_id:
                cleaned = re.sub(r'\D', '', rec.national_id)
                if len(cleaned) != 14:
                    raise ValidationError(_(
                        'الرقم القومي يجب أن يتكون من 14 رقماً.\n'
                        'National ID must be exactly 14 digits. Got: %s'
                    ) % rec.national_id)

    @api.constrains('issue_date', 'expected_return_date')
    def _check_dates(self):
        for rec in self:
            if rec.expected_return_date and rec.issue_date:
                if rec.expected_return_date < rec.issue_date:
                    raise ValidationError(_(
                        'تاريخ الاسترداد لا يمكن أن يكون قبل تاريخ الصرف'
                    ))

    # ── ORM Overrides ─────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('custody.assignment') or '/'
            # Auto-populate national_id from employee if available
            if vals.get('employee_id') and not vals.get('national_id'):
                emp = self.env['hr.employee'].browse(vals['employee_id'])
                if emp.ssnid:
                    vals['national_id'] = emp.ssnid
        return super().create(vals_list)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            if self.employee_id.ssnid:
                self.national_id = self.employee_id.ssnid
            self.employee_department_id = self.employee_id.department_id

    # ── Actions / State Transitions ───────────────────────────────────────────
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('يمكن تأكيد العهدات في حالة المسودة فقط'))
            if not rec.national_id:
                raise ValidationError(_(
                    'GAFI REQUIREMENT: الرقم القومي مطلوب قبل تأكيد العهدة.\n'
                    'National ID is mandatory — GAFI audit will fail without it.'
                ))
            rec.write({'state': 'active'})
            rec.message_post(
                body=_('✅ تم تأكيد العهدة رقم %s للموظف %s') % (rec.name, rec.employee_id.name),
                message_type='notification',
            )

    def action_return(self):
        for rec in self:
            if rec.state not in ('active', 'transferred'):
                raise UserError(_('يمكن استرداد العهدات النشطة أو المحولة فقط'))
            rec.write({
                'state': 'returned',
                'actual_return_date': fields.Date.context_today(self),
            })
            rec.message_post(
                body=_('📦 تم استرداد العهدة في %s') % fields.Date.context_today(rec),
                message_type='notification',
            )

    def action_cancel(self):
        for rec in self:
            if rec.state == 'returned':
                raise UserError(_('لا يمكن إلغاء عهدة مستردة'))
            rec.write({'state': 'cancelled'})

    def action_draft(self):
        for rec in self:
            if rec.state not in ('cancelled',):
                raise UserError(_('يمكن إعادة العهدات الملغية فقط إلى المسودة'))
            rec.write({'state': 'draft'})

    def action_view_transfers(self):
        return {
            'name': _('تحويلات العهدة'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.transfer',
            'view_mode': 'tree,form',
            'domain': [('custody_assignment_id', '=', self.id)],
            'context': {'default_custody_assignment_id': self.id},
        }

    def action_print_form193(self):
        return self.env.ref('l10n_eg_custody.action_report_form193').report_action(self)

    def action_print_custody_sheet(self):
        return self.env.ref('l10n_eg_custody.action_report_custody_sheet').report_action(self)


class CustodyTransfer(models.Model):
    """
    نقل العهدة — Custody Transfer
    Records transfer of custody from one employee to another.
    Each transfer is logged with full audit trail.
    """
    _name = 'custody.transfer'
    _description = 'نقل العهدة - Custody Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transfer_date desc'

    name = fields.Char(
        string='رقم التحويل',
        required=True,
        copy=False,
        readonly=True,
        default='/',
    )
    custody_assignment_id = fields.Many2one(
        'custody.assignment',
        string='العهدة',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    from_employee_id = fields.Many2one(
        'hr.employee',
        string='من الموظف',
        required=True,
        tracking=True,
    )
    to_employee_id = fields.Many2one(
        'hr.employee',
        string='إلى الموظف',
        required=True,
        tracking=True,
    )
    to_national_id = fields.Char(
        string='الرقم القومي للمستلم',
        required=True,
        tracking=True,
        help='Required on Form 193 for transferred custody',
    )
    transfer_date = fields.Date(
        string='تاريخ التحويل',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    reason = fields.Text(
        string='سبب التحويل',
        tracking=True,
    )
    authorised_by_id = fields.Many2one(
        'hr.employee',
        string='المفوض بالتحويل',
        required=True,
        tracking=True,
    )
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('done', 'منفذ'),
    ], default='draft', tracking=True)
    notes = fields.Text(string='ملاحظات')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'رقم التحويل يجب أن يكون فريداً'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('custody.transfer') or '/'
            # Auto-fill from_employee from custody
            if vals.get('custody_assignment_id') and not vals.get('from_employee_id'):
                custody = self.env['custody.assignment'].browse(vals['custody_assignment_id'])
                vals['from_employee_id'] = custody.current_holder_id.id or custody.employee_id.id
        return super().create(vals_list)

    @api.onchange('to_employee_id')
    def _onchange_to_employee(self):
        if self.to_employee_id and self.to_employee_id.ssnid:
            self.to_national_id = self.to_employee_id.ssnid

    @api.constrains('from_employee_id', 'to_employee_id')
    def _check_different_employees(self):
        for rec in self:
            if rec.from_employee_id == rec.to_employee_id:
                raise ValidationError(_('موظف الإرسال والاستلام يجب أن يكونا مختلفين'))

    def action_confirm_transfer(self):
        for rec in self:
            if not rec.to_national_id:
                raise ValidationError(_(
                    'الرقم القومي للمستلم مطلوب لتنفيذ التحويل (متطلب GAFI)'
                ))
            custody = rec.custody_assignment_id
            custody.write({'state': 'transferred'})
            rec.write({'state': 'done'})
            rec.message_post(
                body=_('✅ تم تحويل العهدة من %s إلى %s بتاريخ %s') % (
                    rec.from_employee_id.name,
                    rec.to_employee_id.name,
                    rec.transfer_date,
                ),
            )
            custody.message_post(
                body=_('🔄 تم التحويل: %s → %s (تاريخ: %s)') % (
                    rec.from_employee_id.name,
                    rec.to_employee_id.name,
                    rec.transfer_date,
                ),
            )
