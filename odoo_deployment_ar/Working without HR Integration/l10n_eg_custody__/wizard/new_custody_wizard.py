from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class NewCustodyWizard(models.TransientModel):
    """
    ويزارد تسجيل عهدة جديدة — New Custody Registration Wizard
    يرشد المستخدم خطوة بخطوة لتسجيل عهدة جديدة بشكل صحيح.
    """
    _name = 'new.custody.wizard'
    _description = 'تسجيل عهدة جديدة - New Custody Wizard'

    # ── الخطوة 1: بيانات الموظف ────────────────────────────────────────────
    employee_id = fields.Many2one(
        'hr.employee',
        string='الموظف المستلم',
        required=True,
        domain="[('active', '=', True)]",
    )
    national_id = fields.Char(
        string='الرقم القومي',
        required=True,
        help='14 رقم — إلزامي لمتطلبات GAFI',
    )
    employee_department_id = fields.Many2one(
        'hr.department',
        string='الإدارة',
        related='employee_id.department_id',
        readonly=True,
    )
    employee_job_id = fields.Many2one(
        'hr.job',
        string='الوظيفة',
        related='employee_id.job_id',
        readonly=True,
    )

    # ── الخطوة 2: بيانات الصنف ────────────────────────────────────────────
    product_id = fields.Many2one(
        'product.product',
        string='الصنف (المستديم)',
        required=True,
        domain="[('type', 'in', ['product', 'consu'])]",
    )
    qty = fields.Float(
        string='الكمية',
        required=True,
        default=1.0,
    )
    serial_number = fields.Char(
        string='الرقم التسلسلي / الكودي',
    )
    estimated_value = fields.Float(
        string='القيمة التقديرية (جنيه)',
        digits='Account',
    )
    custody_type = fields.Selection([
        ('personal',  'عهدة شخصية - Personal'),
        ('sub',       'عهدة فرعية - Sub-custody'),
        ('location',  'عهدة مكانية - Location-based'),
    ], string='نوع العهدة', required=True, default='personal')

    # ── الخطوة 3: بيانات المخزن والمسؤولين ──────────────────────────────
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='المخزن',
        required=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='موقع التخزين',
        domain="[('usage', '=', 'internal')]",
    )
    storekeeper_id = fields.Many2one(
        'hr.employee',
        string='أمين المخزن',
        required=True,
        default=lambda self: self.env.user.employee_id,
    )
    dept_manager_id = fields.Many2one(
        'hr.employee',
        string='مدير الإدارة (للتوقيع)',
        required=True,
    )

    # ── الخطوة 4: بيانات الاستمارة ──────────────────────────────────────
    form_193_ref = fields.Char(
        string='رقم استمارة 193',
        required=True,
        help='الرقم التسلسلي للاستمارة الحكومية',
    )
    issue_date = fields.Date(
        string='تاريخ الصرف',
        required=True,
        default=fields.Date.context_today,
    )
    issue_permit_ref = fields.Char(
        string='رقم إذن الصرف المرتبط',
    )
    expected_return_date = fields.Date(
        string='تاريخ الاسترداد المتوقع',
    )
    notes = fields.Text(string='ملاحظات')

    # ── onchange ──────────────────────────────────────────────────────────
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            # Auto-fill national_id from HR employee record
            if self.employee_id.ssnid:
                self.national_id = self.employee_id.ssnid
            # Auto-suggest dept manager (employee's direct manager)
            if self.employee_id.parent_id:
                self.dept_manager_id = self.employee_id.parent_id

    @api.constrains('national_id')
    def _check_national_id(self):
        import re
        for rec in self:
            if rec.national_id:
                cleaned = re.sub(r'\D', '', rec.national_id)
                if len(cleaned) != 14:
                    raise ValidationError(_(
                        'الرقم القومي يجب أن يتكون من 14 رقماً بالضبط.\n'
                        'الرقم المُدخل: %s'
                    ) % rec.national_id)

    @api.constrains('qty')
    def _check_qty(self):
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError(_('الكمية يجب أن تكون أكبر من الصفر'))

    def action_create_custody(self):
        """إنشاء سجل العهدة وفتح الفورم للمراجعة والطباعة."""
        self.ensure_one()
        custody = self.env['custody.assignment'].create({
            'employee_id':      self.employee_id.id,
            'national_id':      self.national_id,
            'product_id':       self.product_id.id,
            'qty':              self.qty,
            'serial_number':    self.serial_number,
            'estimated_value':  self.estimated_value,
            'custody_type':     self.custody_type,
            'warehouse_id':     self.warehouse_id.id,
            'location_id':      self.location_id.id if self.location_id else False,
            'storekeeper_id':   self.storekeeper_id.id,
            'dept_manager_id':  self.dept_manager_id.id,
            'form_193_ref':     self.form_193_ref,
            'issue_date':       self.issue_date,
            'issue_permit_ref': self.issue_permit_ref,
            'expected_return_date': self.expected_return_date,
            'notes':            self.notes,
        })
        # Auto-confirm the custody
        custody.action_confirm()

        # Open the created record
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'custody.assignment',
            'res_id': custody.id,
            'view_mode': 'form',
            'target': 'current',
        }
