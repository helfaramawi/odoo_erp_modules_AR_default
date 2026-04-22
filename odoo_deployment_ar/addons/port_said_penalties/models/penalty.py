# -*- coding: utf-8 -*-
"""
قيد جزاء (Penalty Record)
==========================
النموذج الأساسي لتسجيل الجزاءات الإدارية والتعاقدية في دفتر 39.

المنطق متعدد الأشكال:
- subject_type = employee → الجزاء تأديبي على موظف (قانون الخدمة المدنية)
- subject_type = vendor → الجزاء تعاقدي على مورد/مقاول (قانون المناقصات)

دورة الحياة القانونية:
  draft → recorded → approved → executed → [appealed → (upheld/overturned)] → closed
                                         → cancelled
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Penalty(models.Model):
    _name = 'port_said.penalty'
    _description = 'قيد جزاء'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'incident_date desc, sequence_number desc'
    _rec_name = 'display_name'

    # ── الترقيم القانوني ─────────────────────────────────────────────────────
    sequence_number = fields.Char(
        string='رقم بالدفتر', readonly=True, copy=False, index=True,
        help='تسلسل دفتر 39 القانوني. يُولَّد عند الانتقال لحالة "مُسجَّل".')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ── نوع الجهة (polymorphic) ─────────────────────────────────────────────
    subject_type = fields.Selection([
        ('employee', 'موظف'),
        ('vendor',   'مورد / مقاول'),
    ], string='نوع الجهة', required=True, default='employee', index=True,
       tracking=True)

    employee_id = fields.Many2one('hr.employee',
        string='الموظف',
        ondelete='restrict',
        help='مطلوب إن كان subject_type = employee.')
    employee_department_id = fields.Many2one(
        related='employee_id.department_id', store=True,
        string='الإدارة / القسم')
    employee_job_title = fields.Char(
        related='employee_id.job_title', store=True,
        string='الوظيفة')

    vendor_id = fields.Many2one('res.partner',
        string='المورد / المقاول',
        domain="[('supplier_rank', '>', 0)]",
        ondelete='restrict',
        help='مطلوب إن كان subject_type = vendor.')

    # اسم للعرض في التقارير يعمل لكلا النوعين
    subject_display_name = fields.Char(string='اسم الجهة',
        compute='_compute_subject_display_name', store=True)

    # ── المخالفة ────────────────────────────────────────────────────────────
    violation_type_id = fields.Many2one('port_said.penalty.violation_type',
        string='نوع المخالفة', required=True, tracking=True,
        domain="[('subject_type', '=', subject_type), ('active', '=', True)]")

    incident_date = fields.Date(string='تاريخ المخالفة', required=True,
        default=fields.Date.context_today, tracking=True)
    incident_description = fields.Text(string='وصف الواقعة', required=True,
        help='وصف تفصيلي للواقعة والمخالفة كما هي في محضر الإثبات.')

    # ── الجزاء المُقترَح ─────────────────────────────────────────────────────
    penalty_type_option_id = fields.Many2one('port_said.penalty.type_option',
        string='نوع الجزاء', required=True, tracking=True)
    penalty_description = fields.Text(string='وصف الجزاء التفصيلي')

    # ── المبلغ ──────────────────────────────────────────────────────────────
    amount = fields.Monetary(string='قيمة الغرامة',
        currency_field='currency_id',
        help='0 إن كان الجزاء إنذاراً فقط أو إيقافاً بدون غرامة.')
    fine_percentage = fields.Float(string='نسبة الغرامة %', digits=(5, 2),
        help='للمراجع: نسبة الغرامة من الأساس (الأجر الشهري أو قيمة العقد).')
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    # ── الإيقاف (للموظفين) ─────────────────────────────────────────────────
    suspension_days = fields.Integer(string='أيام الإيقاف',
        help='فقط للجزاءات التي تتضمن إيقافاً.')
    suspension_from = fields.Date(string='بداية الإيقاف')
    suspension_to = fields.Date(string='نهاية الإيقاف')

    # ── السياق المرجعي ─────────────────────────────────────────────────────
    investigation_reference = fields.Char(string='رقم محضر التحقيق',
        help='مطلوب إن كان نوع المخالفة يتطلب تحقيقاً.')
    investigation_date = fields.Date(string='تاريخ التحقيق')

    purchase_order_id = fields.Many2one('purchase.order',
        string='أمر الشراء / العقد',
        help='للجزاءات التعاقدية: العقد المرتبط بالمخالفة.')
    contract_value = fields.Monetary(string='قيمة العقد',
        currency_field='currency_id')

    # ── سلاسل القرار والاعتمادات ────────────────────────────────────────────
    decision_number = fields.Char(string='رقم قرار الجزاء',
        help='رقم القرار الإداري المُصدِر للجزاء.')
    decision_date = fields.Date(string='تاريخ قرار الجزاء')
    decided_by = fields.Many2one('res.users',
        string='اتخذ القرار', readonly=True)
    approved_by = fields.Many2one('res.users',
        string='اعتمد الجزاء', readonly=True)
    approval_date = fields.Date(string='تاريخ الاعتماد', readonly=True)

    # ── دورة الحياة ──────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',     'مسودة'),
        ('recorded',  'مُسجَّل في الدفتر'),
        ('approved',  'مُعتمَد'),
        ('executed',  'مُنفَّذ'),
        ('appealed',  'مُتظلَّم عليه'),
        ('upheld',    'تأكَّد الجزاء'),
        ('overturned','أُلغي بعد التظلم'),
        ('cancelled', 'ملغي'),
        ('closed',    'مُغلَق'),
    ], string='الحالة', default='draft', tracking=True, required=True, index=True)

    cancellation_reason = fields.Text(string='سبب الإلغاء')

    # ── التنفيذ (Execution) ─────────────────────────────────────────────────
    execution_date = fields.Date(string='تاريخ التنفيذ', readonly=True)
    execution_method = fields.Selection([
        ('payroll_deduction', 'خصم من الراتب'),
        ('invoice_deduction', 'خصم من فاتورة المورد'),
        ('guarantee_deduction','خصم من خطاب الضمان'),
        ('cash_payment',      'سداد نقدي'),
        ('warning_only',      'إنذار فقط (بدون خصم مالي)'),
    ], string='طريقة التنفيذ', tracking=True)

    payroll_slip_ref = fields.Char(string='مرجع كشف الراتب',
        help='رقم كشف الراتب الذي طُبِّق عليه الخصم.')

    # ── الربط المحاسبي ──────────────────────────────────────────────────────
    move_id = fields.Many2one('account.move',
        string='القيد المحاسبي', readonly=True)
    daftar55_id = fields.Many2one('port_said.daftar55',
        string='قيد دفتر 55 المرتبط',
        help='للجزاءات المُحصَّلة عبر أذون صرف.')

    # ── التظلم (Appeal) ────────────────────────────────────────────────────
    appeal_ids = fields.One2many('port_said.penalty.appeal',
        'penalty_id', string='التظلمات')
    has_active_appeal = fields.Boolean(
        compute='_compute_has_active_appeal', store=True)

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', readonly=True, copy=False,
        index=True)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('sequence_number', 'subject_display_name',
                 'violation_type_id', 'amount')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s — %s — %s' % (
                rec.sequence_number or '(مسودة)',
                rec.subject_display_name or '—',
                rec.violation_type_id.name or '—',
            )

    @api.depends('subject_type', 'employee_id', 'vendor_id')
    def _compute_subject_display_name(self):
        for rec in self:
            if rec.subject_type == 'employee':
                rec.subject_display_name = rec.employee_id.name or ''
            else:
                rec.subject_display_name = rec.vendor_id.name or ''

    @api.depends('appeal_ids', 'appeal_ids.state')
    def _compute_has_active_appeal(self):
        for rec in self:
            rec.has_active_appeal = bool(rec.appeal_ids.filtered(
                lambda a: a.state in ('submitted', 'under_review')))

    # ── Onchange ─────────────────────────────────────────────────────────────
    @api.onchange('subject_type')
    def _onchange_subject_type(self):
        """إعادة ضبط الحقول عند تغيير نوع الجهة."""
        if self.subject_type == 'employee':
            self.vendor_id = False
            self.purchase_order_id = False
            self.contract_value = 0.0
        else:
            self.employee_id = False
            self.suspension_days = 0
            self.suspension_from = False
            self.suspension_to = False
        self.violation_type_id = False
        self.penalty_type_option_id = False

    @api.onchange('violation_type_id')
    def _onchange_violation_type(self):
        """يقترح الجزاء من قائمة المسموح به ويُبيِّن الحدود."""
        if not self.violation_type_id:
            return
        options = self.violation_type_id.allowed_penalty_types
        if self.penalty_type_option_id not in options:
            self.penalty_type_option_id = False
        return {
            'domain': {
                'penalty_type_option_id': [('id', 'in', options.ids)],
            }
        }

    # ── Constraints ──────────────────────────────────────────────────────────
    @api.constrains('subject_type', 'employee_id', 'vendor_id')
    def _check_subject_set(self):
        for rec in self:
            if rec.subject_type == 'employee' and not rec.employee_id:
                raise ValidationError(_(
                    'يجب تحديد الموظف للجزاء التأديبي.'))
            if rec.subject_type == 'vendor' and not rec.vendor_id:
                raise ValidationError(_(
                    'يجب تحديد المورد للجزاء التعاقدي.'))

    @api.constrains('amount')
    def _check_amount_non_negative(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError(_(
                    'قيمة الغرامة لا يمكن أن تكون سالبة.'))

    @api.constrains('amount', 'violation_type_id', 'contract_value',
                    'employee_id')
    def _check_amount_within_legal_limit(self):
        """تأكيد الحد الأقصى القانوني."""
        for rec in self:
            vt = rec.violation_type_id
            if not vt:
                continue
            # الحد الثابت
            if vt.max_fine_fixed and rec.amount > vt.max_fine_fixed:
                raise ValidationError(_(
                    'قيمة الغرامة (%s) تتجاوز الحد الأقصى القانوني (%s).'
                ) % (rec.amount, vt.max_fine_fixed))
            # نسبة من أساس معيَّن (للمراجعة فقط - تحذير لا يمنع)
            # اختياري: يمكن تشديدها لاحقاً إن طُلب

    @api.constrains('suspension_from', 'suspension_to', 'suspension_days')
    def _check_suspension_dates(self):
        for rec in self:
            if rec.suspension_from and rec.suspension_to:
                if rec.suspension_from > rec.suspension_to:
                    raise ValidationError(_(
                        'بداية الإيقاف يجب أن تسبق نهايته.'))

    # ── Lifecycle ────────────────────────────────────────────────────────────
    def action_record(self):
        """تسجيل في دفتر 39 — يُولَّد التسلسل القانوني."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الجزاء ليس في حالة مسودة.'))

            # التحقق من شروط التحقيق
            if rec.violation_type_id.requires_investigation and not \
               rec.investigation_reference:
                raise UserError(_(
                    'هذا النوع من المخالفات يتطلب رقم محضر تحقيق.'))

            # توليد التسلسل بعد نجاح أي فحص
            if not rec.sequence_number:
                Seq = rec.env['ir.sequence']
                seq_code = ('port_said.penalty.employee'
                           if rec.subject_type == 'employee'
                           else 'port_said.penalty.vendor')
                rec.sequence_number = Seq.next_by_code(seq_code) or '/'

            # السنة المالية
            if rec.incident_date and not rec.fiscal_year:
                m, y = rec.incident_date.month, rec.incident_date.year
                if m >= 7:
                    rec.fiscal_year = '%d/%d' % (y, y + 1)
                else:
                    rec.fiscal_year = '%d/%d' % (y - 1, y)

            rec.state = 'recorded'

    def action_approve(self):
        """اعتماد الجزاء — قد يتطلب صلاحية مدير."""
        for rec in self:
            if rec.state != 'recorded':
                raise UserError(_('الجزاء ليس في حالة "مُسجَّل".'))

            # إن كانت المخالفة تتطلب اعتماد مدير
            if rec.violation_type_id.requires_manager_approval and \
               not rec.env.user.has_group('port_said_penalties.group_penalty_manager'):
                raise UserError(_(
                    'هذه المخالفة تتطلب اعتماد مدير الجزاءات.'))

            rec.state = 'approved'
            rec.approved_by = rec.env.user.id
            rec.approval_date = fields.Date.today()

    def action_execute(self):
        """تنفيذ الجزاء محاسبياً (خصم من راتب / من فاتورة / إلخ)."""
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('يجب اعتماد الجزاء قبل التنفيذ.'))
            if not rec.execution_method:
                raise UserError(_('يجب تحديد طريقة التنفيذ.'))

            rec.state = 'executed'
            rec.execution_date = fields.Date.today()

            # القيود المحاسبية حسب الطريقة
            if rec.execution_method == 'warning_only':
                rec.message_post(body=_(
                    'جزاء إنذار — لا يتطلب قيداً محاسبياً.'))
            else:
                # Hook: الفريق المحاسبي يمدِّد هذه الدالة لإنشاء القيد المناسب
                rec._create_execution_move()

    def _create_execution_move(self):
        """Hook لإنشاء القيد المحاسبي — تُمدَّد من فريق المحاسبة."""
        self.ensure_one()
        # تصميم مقصود: لا ننشئ قيداً هنا لأنه يعتمد على دليل حسابات المحافظة
        self.message_post(body=_(
            'تم التنفيذ. يُرجى إنشاء القيد المحاسبي يدوياً حسب السياسة المحلية، '
            'أو تخصيص _create_execution_move() لإنشائه تلقائياً.'
        ))

    def action_appeal(self):
        """فتح تظلم — يُنشئ port_said.penalty.appeal."""
        for rec in self:
            if rec.state not in ('approved', 'executed'):
                raise UserError(_(
                    'التظلم متاح فقط للجزاءات المُعتمَدة أو المُنفَّذة.'))
            if rec.has_active_appeal:
                raise UserError(_('يوجد تظلم نشط بالفعل لهذا الجزاء.'))

            # أنشئ سجل تظلم جديد
            appeal = rec.env['port_said.penalty.appeal'].create({
                'penalty_id': rec.id,
                'submission_date': fields.Date.today(),
                'state': 'submitted',
            })
            rec.state = 'appealed'
            return {
                'type': 'ir.actions.act_window',
                'name': _('التظلم'),
                'res_model': 'port_said.penalty.appeal',
                'res_id': appeal.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_close(self):
        """إغلاق الملف — لا يمكن إعادة فتحه بعد ذلك."""
        for rec in self:
            if rec.state not in ('executed', 'upheld', 'overturned'):
                raise UserError(_(
                    'الإغلاق متاح فقط للجزاءات المُنفَّذة أو المحسومة بتظلم.'))
            rec.state = 'closed'

    def action_cancel(self):
        """إلغاء — يُسجَّل مع سبب."""
        for rec in self:
            if rec.state in ('executed', 'closed'):
                raise UserError(_(
                    'لا يمكن إلغاء جزاء مُنفَّذ. استخدم التظلم.'))
            if not rec.cancellation_reason:
                raise UserError(_('يجب تسجيل سبب الإلغاء.'))
            rec.state = 'cancelled'

    # ── Write Protection ────────────────────────────────────────────────────
    def write(self, vals):
        protected = {'subject_type', 'employee_id', 'vendor_id',
                    'violation_type_id', 'penalty_type_option_id',
                    'amount', 'incident_date'}
        if any(f in vals for f in protected):
            for rec in self:
                if rec.state in ('executed', 'upheld', 'closed'):
                    raise UserError(_(
                        'لا يجوز تعديل جزاء مُنفَّذ (%s).'
                    ) % rec.sequence_number)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('لا يجوز حذف جزاء بعد التسجيل.'))
        return super().unlink()
