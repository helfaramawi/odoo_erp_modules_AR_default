# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import date
import math


class FixedAsset(models.Model):
    """
    الأصل الثابت الحكومي — Government Fixed Asset
    متوافق مع: معيار المحاسبة المصري #10 + لوائح GAFI + الجهاز المركزي للمحاسبات
    يتكامل مع: l10n_eg_custody | port_said_daftar55 | account.move
    """
    _name = 'port_said.fixed.asset'
    _description = 'أصل ثابت حكومي — Government Fixed Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'asset_number'
    _order = 'asset_number'

    # ── هوية الأصل ───────────────────────────────────────────────
    asset_number = fields.Char(
        string='رقم الأصل', required=True, copy=False,
        readonly=True, default='/',
        tracking=True,
        help='رقم تسلسلي حكومي — لا يمكن تعديله بعد التفعيل'
    )
    name = fields.Char(
        string='اسم الأصل / الوصف', required=True, tracking=True
    )
    serial_number = fields.Char(
        string='الرقم التسلسلي', tracking=True,
        help='الرقم التسلسلي للمُصنِّع — مطلوب لـ GAFI'
    )
    asset_tag = fields.Char(string='كود الباركود / الـ Tag')
    category_id = fields.Many2one(
        'port_said.asset.category', string='الفئة',
        required=True, tracking=True, ondelete='restrict'
    )

    # ── الحالة ───────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',      'مسودة'),
        ('active',     'نشط — قيد الاستخدام'),
        ('suspended',  'موقوف مؤقتاً'),
        ('disposed',   'مُستغنى عنه / مباع'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    # ── الموقع والمسؤولية ────────────────────────────────────────
    department_id = fields.Many2one(
        'hr.department', string='الإدارة / المصلحة المسؤولة',
        tracking=True
    )
    location = fields.Char(string='الموقع التفصيلي', tracking=True)
    custodian_employee_id = fields.Many2one(
        'hr.employee', string='الموظف المسؤول (أمين العهدة)',
        tracking=True,
        help='الموظف الحاضن للأصل — يُربط بوحدة العهد تلقائياً'
    )
    custody_assignment_id = fields.Many2one(
        'custody.assignment', string='إذن العهدة المرتبط',
        readonly=True, tracking=True,
        help='الربط التلقائي بوحدة العهد عند التفعيل'
    )

    # ── القيم المالية ────────────────────────────────────────────
    purchase_value = fields.Monetary(
        string='تكلفة الاقتناء الأصلية (ج.م)', required=True,
        tracking=True,
        help='التكلفة الكاملة شاملة مصاريف التركيب والنقل'
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda s: s.env.company.currency_id
    )
    residual_value = fields.Monetary(
        string='القيمة التخريدية (ج.م)',
        compute='_compute_residual_value', store=True
    )
    book_value = fields.Monetary(
        string='القيمة الدفترية الحالية (ج.م)',
        compute='_compute_book_value', store=True
    )
    accumulated_depreciation = fields.Monetary(
        string='مجمع الإهلاك (ج.م)',
        compute='_compute_accumulated_depreciation', store=True
    )

    # ── تواريخ ───────────────────────────────────────────────────
    purchase_date = fields.Date(
        string='تاريخ الاقتناء', required=True, tracking=True
    )
    activation_date = fields.Date(
        string='تاريخ بدء الإهلاك', tracking=True,
        help='تاريخ أول قيد إهلاك — عادةً أول الشهر التالي للاقتناء'
    )
    disposal_date = fields.Date(
        string='تاريخ التصرف', tracking=True, readonly=True
    )
    end_of_life_date = fields.Date(
        string='تاريخ انتهاء العمر الإنتاجي',
        compute='_compute_end_of_life', store=True
    )

    # ── مصدر الاقتناء ────────────────────────────────────────────
    acquisition_type = fields.Selection([
        ('purchase',    'شراء — أمر توريد'),
        ('donation',    'هبة / تبرع'),
        ('transfer',    'تحويل من جهة حكومية'),
        ('manufactured','صناعة داخلية'),
    ], string='طريقة الاقتناء', default='purchase', tracking=True)

    purchase_order_id = fields.Many2one(
        'purchase.order', string='أمر الشراء المرجعي',
        help='الربط بأمر الشراء في وحدة المشتريات'
    )
    daftar55_id = fields.Many2one(
        'port_said.daftar55', string='مرجع دفتر 55 ع.ح',
        help='الصرف المالي المرتبط بالاقتناء من دفتر 55',
        tracking=True
    )
    commitment_id = fields.Many2one(
        'port_said.commitment', string='الارتباط الميزاني',
        help='الارتباط الميزاني الذي غطى عملية الاقتناء'
    )
    vendor_id = fields.Many2one('res.partner', string='المورد / المصدر')
    invoice_ref = fields.Char(string='رقم الفاتورة')

    # ── إهلاك ────────────────────────────────────────────────────
    depreciation_method = fields.Selection(
        related='category_id.method', readonly=True, string='طريقة الإهلاك'
    )
    depreciation_rate = fields.Float(
        related='category_id.depreciation_rate', readonly=True, string='معدل الإهلاك (%)'
    )
    prorata = fields.Boolean(
        string='إهلاك بالحصة الزمنية',
        default=True,
        help='احتساب الإهلاك من اليوم الفعلي للتفعيل وليس من أول الشهر'
    )
    depreciation_line_ids = fields.One2many(
        'port_said.asset.depreciation.line', 'asset_id',
        string='جدول الإهلاك'
    )
    depreciation_line_count = fields.Integer(
        string='عدد قيود الإهلاك',
        compute='_compute_dep_count'
    )

    # ── بيانات إضافية ────────────────────────────────────────────
    condition = fields.Selection([
        ('excellent', 'ممتاز'),
        ('good',      'جيد'),
        ('fair',      'مقبول'),
        ('poor',      'رديء — يحتاج صيانة'),
    ], string='الحالة الفعلية', default='good')
    notes = fields.Text(string='ملاحظات')

    # ── Smart Buttons counts ─────────────────────────────────────
    @api.depends('depreciation_line_ids')
    def _compute_dep_count(self):
        for rec in self:
            rec.depreciation_line_count = len(rec.depreciation_line_ids)

    @api.depends('category_id.residual_value_pct', 'purchase_value')
    def _compute_residual_value(self):
        for rec in self:
            rec.residual_value = (
                rec.purchase_value * (rec.category_id.residual_value_pct / 100.0)
                if rec.category_id else 0.0
            )

    @api.depends('depreciation_line_ids.amount', 'depreciation_line_ids.move_id')
    def _compute_accumulated_depreciation(self):
        for rec in self:
            posted_lines = rec.depreciation_line_ids.filtered(
                lambda l: l.move_id and l.move_id.state == 'posted'
            )
            rec.accumulated_depreciation = sum(posted_lines.mapped('amount'))

    @api.depends('purchase_value', 'accumulated_depreciation')
    def _compute_book_value(self):
        for rec in self:
            rec.book_value = rec.purchase_value - rec.accumulated_depreciation

    @api.depends('activation_date', 'category_id.useful_life_years')
    def _compute_end_of_life(self):
        for rec in self:
            if rec.activation_date and rec.category_id.useful_life_years > 0:
                rec.end_of_life_date = (
                    rec.activation_date + relativedelta(years=rec.category_id.useful_life_years)
                )
            else:
                rec.end_of_life_date = False

    # ══════════════════════════════════════════════════════════════
    # ACTIONS / WORKFLOW
    # ══════════════════════════════════════════════════════════════
    def action_activate(self):
        """تفعيل الأصل — توليد جدول الإهلاك + إنشاء قيد افتتاحي + ربط العهد"""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('لا يمكن تفعيل أصل غير في حالة مسودة'))
            if not rec.activation_date:
                rec.activation_date = rec.purchase_date
            if rec.asset_number == '/':
                rec.asset_number = self.env['ir.sequence'].next_by_code(
                    'port_said.fixed.asset'
                ) or '/'
            # توليد جدول الإهلاك
            rec._generate_depreciation_schedule()
            # ربط العهد إن وُجد موظف
            if rec.custodian_employee_id and not rec.custody_assignment_id:
                rec._link_or_create_custody()
            rec.state = 'active'
            rec.message_post(body=_('تم تفعيل الأصل الثابت وتوليد جدول الإهلاك'))
        return True

    def action_suspend(self):
        self.ensure_one()
        if self.state != 'active':
            raise UserError(_('لا يمكن إيقاف أصل غير نشط'))
        self.state = 'suspended'
        self.message_post(body=_('تم إيقاف الأصل مؤقتاً'))

    def action_reactivate(self):
        self.ensure_one()
        self.state = 'active'
        self.message_post(body=_('تم إعادة تفعيل الأصل'))

    # ══════════════════════════════════════════════════════════════
    # DEPRECIATION SCHEDULE GENERATION — القسط الثابت وفق EAS #10
    # ══════════════════════════════════════════════════════════════
    def _generate_depreciation_schedule(self):
        """توليد جدول الإهلاك السنوي وفق معيار المحاسبة المصري #10"""
        self.ensure_one()
        # حذف الجدول القديم (غير المرحَّل)
        self.depreciation_line_ids.filtered(
            lambda l: not l.move_id
        ).unlink()

        if not self.category_id.depreciation_rate or not self.activation_date:
            return

        depreciable_value = self.purchase_value - self.residual_value
        if depreciable_value <= 0:
            return

        method = self.category_id.method
        rate = self.category_id.depreciation_rate / 100.0
        years = self.category_id.useful_life_years

        lines_to_create = []
        current_date = self.activation_date
        remaining_value = depreciable_value
        book_val = self.purchase_value

        for year in range(1, years + 1):
            dep_date = current_date + relativedelta(years=1) - relativedelta(days=1)
            # لا تتجاوز نهاية العمر الإنتاجي
            if dep_date > (self.activation_date + relativedelta(years=years)):
                dep_date = self.activation_date + relativedelta(years=years)

            if method == 'straight_line':
                amount = depreciable_value / years
            elif method == 'declining':
                amount = book_val * rate * 2  # Double Declining
            elif method == 'sum_of_years':
                factor = (years - year + 1) / (years * (years + 1) / 2)
                amount = depreciable_value * factor
            else:
                amount = depreciable_value / years

            # السنة الأخيرة — صفّر المتبقي
            if year == years:
                amount = remaining_value

            amount = min(amount, remaining_value)
            if amount <= 0:
                break

            remaining_value -= amount
            book_val -= amount

            lines_to_create.append({
                'asset_id': self.id,
                'name': f'إهلاك السنة {year} — {self.asset_number}',
                'sequence': year,
                'amount': amount,
                'depreciation_date': dep_date,
                'fiscal_year': str(dep_date.year),
                'remaining_value': book_val + self.residual_value,
            })
            current_date = dep_date + relativedelta(days=1)

        if lines_to_create:
            self.env['port_said.asset.depreciation.line'].create(lines_to_create)

    def _link_or_create_custody(self):
        """ربط الأصل بإذن عهدة موجود أو إنشاء واحد جديد"""
        self.ensure_one()
        # البحث عن عهدة نشطة للموظف تحتوي نفس المنتج
        existing = self.env['custody.assignment'].search([
            ('employee_id', '=', self.custodian_employee_id.id),
            ('state', 'in', ['draft', 'active']),
        ], limit=1)
        if existing:
            self.custody_assignment_id = existing
        # لا ننشئ تلقائياً — نترك للمستخدم للتحكم

    # ══════════════════════════════════════════════════════════════
    # POSTING DEPRECIATION — ترحيل قيد الإهلاك الدوري
    # ══════════════════════════════════════════════════════════════
    def action_post_all_pending_depreciation(self):
        """ترحيل جميع قيود الإهلاك المستحقة حتى اليوم"""
        today = date.today()
        lines = self.env['port_said.asset.depreciation.line'].search([
            ('asset_id', 'in', self.ids),
            ('move_id', '=', False),
            ('depreciation_date', '<=', today),
        ])
        for line in lines:
            line.action_post()
        return True

    @api.constrains('purchase_value')
    def _check_value(self):
        for rec in self:
            if rec.purchase_value <= 0:
                raise ValidationError(_('تكلفة الاقتناء يجب أن تكون أكبر من صفر'))



    def action_view_depreciation(self):
        """عرض جدول الإهلاك"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'جدول الإهلاك — {self.asset_number}',
            'res_model': 'port_said.asset.depreciation.line',
            'view_mode': 'list',
            'domain': [('asset_id', '=', self.id)],
            'context': {'default_asset_id': self.id},
        }

    def action_open_disposal_wizard(self):
        """فتح نموذج التصرف في الأصل"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'التصرف في الأصل — {self.asset_number}',
            'res_model': 'port_said.asset.disposal',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_asset_id': self.id,
            },
        }

    def unlink(self):
        for rec in self:
            if rec.state == 'active':
                raise UserError(_(
                    'لا يمكن حذف أصل نشط. قم بالتصرف فيه أولاً.'
                ))
        return super().unlink()
