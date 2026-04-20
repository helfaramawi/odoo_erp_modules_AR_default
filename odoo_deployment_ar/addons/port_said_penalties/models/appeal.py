# -*- coding: utf-8 -*-
"""
تظلم ضد جزاء (Penalty Appeal)
================================
يُنشأ عند طعن الموظف أو المورد في قرار الجزاء.

للموظفين: التظلم يُقدَّم للرئيس المباشر أولاً، ثم للمحكمة الإدارية.
للموردين: التظلم يُقدَّم للجنة البت بالعطاءات، ثم للقضاء المدني.

دورة الحياة:
  submitted → under_review → (upheld | overturned | partial_reduction) → resolved
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PenaltyAppeal(models.Model):
    _name = 'port_said.penalty.appeal'
    _description = 'تظلم ضد جزاء'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'submission_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ── الربط بالجزاء ───────────────────────────────────────────────────────
    penalty_id = fields.Many2one('port_said.penalty',
        string='الجزاء المُتظلَّم عليه', required=True,
        ondelete='cascade', index=True)
    penalty_sequence = fields.Char(
        related='penalty_id.sequence_number', store=True, readonly=True,
        string='رقم الجزاء')
    subject_display_name = fields.Char(
        related='penalty_id.subject_display_name', store=True,
        string='اسم الجهة')
    original_amount = fields.Monetary(
        related='penalty_id.amount', readonly=True,
        string='قيمة الجزاء الأصلية',
        currency_field='currency_id')

    # ── تفاصيل التقديم ──────────────────────────────────────────────────────
    submission_date = fields.Date(string='تاريخ التقديم', required=True,
        default=fields.Date.context_today)
    submission_reference = fields.Char(string='رقم محضر التقديم',
        help='مطلوب للتوثيق القانوني.')
    grounds = fields.Text(string='أسباب التظلم', required=True,
        help='الحجج القانونية والواقعية للطعن في الجزاء.')

    # ── الجهة المراجِعة ────────────────────────────────────────────────────
    appeal_venue = fields.Selection([
        ('direct_manager',       'الرئيس المباشر'),
        ('grievance_committee',  'لجنة التظلمات'),
        ('admin_court',          'المحكمة الإدارية'),
        ('civil_court',          'القضاء المدني'),
        ('arbitration',          'التحكيم'),
    ], string='الجهة المراجِعة', required=True)
    case_number = fields.Char(string='رقم القضية / التظلم',
        help='رقم محضر اللجنة أو رقم القضية أمام المحكمة.')

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('submitted',         'مُقدَّم'),
        ('under_review',      'قيد المراجعة'),
        ('upheld',            'أُيِّد الجزاء'),
        ('overturned',        'أُلغي الجزاء'),
        ('partial_reduction', 'خُفِّف الجزاء'),
        ('withdrawn',         'سُحب التظلم'),
    ], string='الحالة', default='submitted', tracking=True, required=True)

    # ── القرار ──────────────────────────────────────────────────────────────
    decision_date = fields.Date(string='تاريخ القرار', readonly=True)
    decision_reference = fields.Char(string='رقم القرار',
        help='رقم قرار اللجنة أو الحكم القضائي.')
    decision_summary = fields.Text(string='ملخص القرار')

    reduced_amount = fields.Monetary(string='القيمة المخفَّفة',
        currency_field='currency_id',
        help='إن كان القرار تخفيفاً، القيمة الجديدة للجزاء.')
    reduction_percentage = fields.Float(
        string='نسبة التخفيف %', digits=(5, 2),
        compute='_compute_reduction_percentage', store=True)

    # ── الوقت والتكاليف ────────────────────────────────────────────────────
    processing_days = fields.Integer(
        string='أيام المعالجة',
        compute='_compute_processing_days', store=True)
    legal_fees = fields.Monetary(string='رسوم قانونية',
        currency_field='currency_id',
        help='أي رسوم قانونية تحمَّلتها الإدارة في هذا التظلم.')

    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('penalty_sequence', 'state', 'appeal_venue')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = _('تظلم على جزاء %s — %s') % (
                rec.penalty_sequence or '—',
                dict(self._fields['state'].selection).get(rec.state),
            )

    @api.depends('original_amount', 'reduced_amount')
    def _compute_reduction_percentage(self):
        for rec in self:
            if rec.original_amount and rec.reduced_amount is not False:
                rec.reduction_percentage = (
                    (rec.original_amount - rec.reduced_amount)
                    / rec.original_amount * 100.0
                    if rec.original_amount > 0 else 0.0)
            else:
                rec.reduction_percentage = 0.0

    @api.depends('submission_date', 'decision_date')
    def _compute_processing_days(self):
        for rec in self:
            if rec.submission_date and rec.decision_date:
                rec.processing_days = (rec.decision_date - rec.submission_date).days
            else:
                rec.processing_days = 0

    # ── Constraints ──────────────────────────────────────────────────────────
    @api.constrains('reduced_amount', 'original_amount')
    def _check_reduced_amount(self):
        for rec in self:
            if rec.reduced_amount < 0:
                raise ValidationError(_(
                    'القيمة المخفَّفة لا يمكن أن تكون سالبة.'))
            if rec.original_amount and rec.reduced_amount > rec.original_amount:
                raise ValidationError(_(
                    'القيمة المخفَّفة لا يمكن أن تتجاوز القيمة الأصلية.'))

    # ── Lifecycle Actions ────────────────────────────────────────────────────
    def action_start_review(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('التظلم ليس في حالة "مُقدَّم".'))
            rec.state = 'under_review'

    def action_uphold(self):
        """تأكيد الجزاء — الجزاء يبقى كما هو."""
        for rec in self:
            if rec.state != 'under_review':
                raise UserError(_('التظلم ليس قيد المراجعة.'))
            if not rec.decision_reference:
                raise UserError(_('يجب تسجيل رقم القرار.'))
            rec.state = 'upheld'
            rec.decision_date = fields.Date.today()
            # عكس الأثر على الجزاء الأصلي
            rec.penalty_id.state = 'upheld'
            rec.penalty_id.message_post(body=_(
                'تأكَّد الجزاء بقرار %s بتاريخ %s.'
            ) % (rec.decision_reference, rec.decision_date))

    def action_overturn(self):
        """إلغاء الجزاء — يصبح لاغياً قانونياً."""
        for rec in self:
            if rec.state != 'under_review':
                raise UserError(_('التظلم ليس قيد المراجعة.'))
            if not rec.decision_reference or not rec.decision_summary:
                raise UserError(_(
                    'يجب تسجيل رقم القرار وملخصه قبل الإلغاء.'))
            rec.state = 'overturned'
            rec.decision_date = fields.Date.today()
            rec.penalty_id.state = 'overturned'
            rec.penalty_id.message_post(body=_(
                'أُلغي الجزاء بقرار %s بتاريخ %s. '
                'ملخص: %s'
            ) % (rec.decision_reference, rec.decision_date,
                 rec.decision_summary))
            # الإدارة المحاسبية يجب أن تُنشئ قيداً عكسياً إن كان الجزاء نُفِّذ

    def action_reduce(self):
        """تخفيف الجزاء — القيمة الجديدة تُطبَّق."""
        for rec in self:
            if rec.state != 'under_review':
                raise UserError(_('التظلم ليس قيد المراجعة.'))
            if not rec.reduced_amount:
                raise UserError(_('يجب تحديد القيمة المخفَّفة.'))
            if not rec.decision_reference:
                raise UserError(_('يجب تسجيل رقم القرار.'))
            rec.state = 'partial_reduction'
            rec.decision_date = fields.Date.today()
            rec.penalty_id.message_post(body=_(
                'خُفِّف الجزاء من %s إلى %s بقرار %s.'
            ) % (rec.original_amount, rec.reduced_amount,
                 rec.decision_reference))
            # لاحقاً: تعديل قيمة الجزاء الأصلي بمراقبة مدير

    def action_withdraw(self):
        """سحب التظلم — المتقدِّم بالتظلم يتراجع."""
        for rec in self:
            if rec.state not in ('submitted', 'under_review'):
                raise UserError(_(
                    'السحب متاح فقط قبل صدور القرار.'))
            rec.state = 'withdrawn'
            rec.penalty_id.state = 'upheld'
            rec.penalty_id.message_post(body=_(
                'سُحب التظلم. الجزاء الأصلي يبقى نافذاً.'))
