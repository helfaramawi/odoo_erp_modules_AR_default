# -*- coding: utf-8 -*-
"""
كتالوج المخالفات والجزاءات القانونية
=========================================
يحتفظ بقائمة المخالفات القانونية المعتمدة مع مراجعها القانونية.
كل جزاء يُنشأ على أساس نوع مخالفة محدد من هذا الكتالوج.

المرجعيات القانونية:
- قانون الخدمة المدنية 81 لسنة 2016 (موظفين)
- قانون المناقصات والمزايدات 182 لسنة 2018 (موردين)
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ViolationType(models.Model):
    _name = 'port_said.penalty.violation_type'
    _description = 'نوع مخالفة'
    _order = 'subject_type, severity, code'
    _inherit = ['mail.thread']

    # ── الهوية ───────────────────────────────────────────────────────────────
    name = fields.Char(string='اسم المخالفة', required=True, translate=False)
    code = fields.Char(string='الكود', required=True, index=True,
        help='كود فني للمخالفة، مثال: VIO-TARDY، VIO-LATE-DELIVERY')
    description = fields.Text(string='الوصف التفصيلي')

    # ── نوع الجهة المستهدفة ─────────────────────────────────────────────────
    subject_type = fields.Selection([
        ('employee', 'موظف'),
        ('vendor',   'مورد / مقاول'),
    ], string='نوع الجهة', required=True, index=True)

    # ── درجة الجسامة ────────────────────────────────────────────────────────
    severity = fields.Selection([
        ('minor',    'بسيطة'),
        ('moderate', 'متوسطة'),
        ('major',    'جسيمة'),
        ('critical', 'جسيمة جداً'),
    ], string='الدرجة', required=True, default='minor', index=True)

    # ── الجزاءات المتاحة لهذه المخالفة ──────────────────────────────────────
    allowed_penalty_types = fields.Many2many(
        'port_said.penalty.type_option',
        relation='penalty_vtype_type_option_rel',
        string='أنواع الجزاء المسموحة',
        help='الجزاءات القانونية الممكنة لهذه المخالفة. '
             'عند تسجيل جزاء جديد، الاختيار محصور بهذه القائمة.')

    # ── الحد الأقصى للجزاء (حسب القانون) ────────────────────────────────────
    max_fine_percentage = fields.Float(string='الحد الأقصى للغرامة %',
        digits=(5, 2),
        help='للموظفين: نسبة من الأجر الشهري. '
             'للموردين: نسبة من قيمة العقد.')
    max_fine_fixed = fields.Monetary(string='حد أقصى ثابت',
        currency_field='currency_id',
        help='إن وُجد حد أقصى مطلق بالجنيه.')
    max_suspension_days = fields.Integer(
        string='الحد الأقصى لأيام الإيقاف',
        help='للجزاءات التي تتضمن إيقافاً عن العمل.')

    # ── المرجع القانوني ──────────────────────────────────────────────────────
    legal_reference = fields.Char(string='المرجع القانوني',
        help='مثال: المادة 52 من قانون الخدمة المدنية 81/2016')
    legal_law_number = fields.Char(string='رقم القانون / اللائحة',
        help='مثال: 81/2016')

    # ── أحكام خاصة ──────────────────────────────────────────────────────────
    requires_investigation = fields.Boolean(
        string='يتطلب تحقيقاً',
        help='بعض الجزاءات لا يُتخذ قرارها إلا بعد تحقيق إداري رسمي.')
    requires_manager_approval = fields.Boolean(
        string='يتطلب اعتماد المدير',
        help='للجزاءات التي تتخطى صلاحية الرئيس المباشر.')

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code, company_id)',
         'كود المخالفة مكرر.'),
    ]

    @api.constrains('max_fine_percentage')
    def _check_percentage_range(self):
        for rec in self:
            if rec.max_fine_percentage < 0 or rec.max_fine_percentage > 100:
                raise ValidationError(_(
                    'النسبة المئوية يجب أن تكون بين 0 و 100.'))

    def name_get(self):
        return [(rec.id, '[%s] %s' % (rec.code, rec.name)) for rec in self]


class PenaltyTypeOption(models.Model):
    """أنواع الجزاءات المتاحة — جدول مرجعي صغير."""
    _name = 'port_said.penalty.type_option'
    _description = 'نوع جزاء متاح'
    _order = 'subject_type, sequence, code'

    name = fields.Char(string='الاسم', required=True, translate=False)
    code = fields.Char(string='الكود', required=True, index=True)
    sequence = fields.Integer(string='الترتيب', default=10)
    subject_type = fields.Selection([
        ('employee', 'موظف'),
        ('vendor',   'مورد / مقاول'),
        ('both',     'كلاهما'),
    ], string='يُطبَّق على', required=True, default='both')

    # ── طبيعة الجزاء ────────────────────────────────────────────────────────
    has_fine = fields.Boolean(string='يتضمن غرامة مالية', default=True)
    has_suspension = fields.Boolean(string='يتضمن إيقافاً عن العمل',
        help='للموظفين فقط.')
    is_warning_only = fields.Boolean(string='إنذار فقط (بدون خصم)',
        help='جزاءات ورقية لا تؤثر محاسبياً.')

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code, company_id)', 'كود الجزاء مكرر.'),
    ]
