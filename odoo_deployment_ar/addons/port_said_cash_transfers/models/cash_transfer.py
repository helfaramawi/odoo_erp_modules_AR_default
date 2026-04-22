# -*- coding: utf-8 -*-
"""
حركة نقدية (Cash Transfer)
=============================
النموذج الأساسي لتسجيل حركة النقد الفعلي بين عهدة وأخرى.

الفارق عن account.bank.statement.line:
- هذه حركة نقد مادي (أوراق، سبائك، عملات أجنبية ورقية)
- تحتاج تتبع سلسلة العهدة (chain of custody)
- تنتهي بتأكيد مادي من المستلم (لا تقاص بنكي)

دورة الحياة:
  draft → prepared → in_transit → delivered → confirmed → closed
                                           → disputed (اختلاف في العد)
                                           → lost (فقدان/سرقة)
  cancelled (يمكن من أي حالة قبل delivered مع سبب)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CashTransfer(models.Model):
    _name = 'port_said.cash_transfer'
    _description = 'حركة نقدية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transfer_date desc, sequence_number desc'
    _rec_name = 'display_name'

    # ── الهوية ───────────────────────────────────────────────────────────────
    sequence_number = fields.Char(
        string='رقم بالدفتر', readonly=True, copy=False, index=True,
        help='تسلسل دفتر 39 القانوني (39-OUT/... أو 39-IN/...).')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ── الاتجاه (polymorphic) ──────────────────────────────────────────────
    direction = fields.Selection([
        ('outgoing', 'نقود مرسلة (صادرة)'),
        ('incoming', 'نقود واردة (مستلمة)'),
    ], string='الاتجاه', required=True, index=True, tracking=True)

    # ── المبلغ ──────────────────────────────────────────────────────────────
    amount = fields.Monetary(string='المبلغ', required=True,
        currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)
    denomination_notes = fields.Text(string='تفصيل الفئات',
        help='تفصيل العدّ حسب الفئات، مثال: 200×50 = 10,000 / 500×20 = 10,000')

    # ── التواريخ ─────────────────────────────────────────────────────────────
    transfer_date = fields.Date(string='تاريخ التحويل', required=True,
        default=fields.Date.context_today, tracking=True)
    preparation_date = fields.Datetime(string='تاريخ الإعداد', readonly=True)
    dispatch_datetime = fields.Datetime(string='تاريخ/وقت المغادرة')
    arrival_datetime = fields.Datetime(string='تاريخ/وقت الوصول')
    confirmation_date = fields.Datetime(string='تاريخ التأكيد', readonly=True)

    # ── سلسلة العهدة (Chain of Custody) ────────────────────────────────────
    # المرسل
    sender_employee_id = fields.Many2one('hr.employee',
        string='المُرسِل (موظف مسؤول)', required=True, tracking=True,
        help='الموظف الذي يُخرج النقدية من عهدته ويُسلِّمها للناقل.')
    sender_unit = fields.Char(string='الجهة المُرسِلة',
        help='اسم الخزينة أو الوحدة المُرسِلة (للعرض في التقارير).')

    # الناقل (اختياري — قد يكون الموظف نفسه)
    transporter_id = fields.Many2one('hr.employee',
        string='الناقل / المُرافِق',
        help='الموظف الموكَّل بنقل النقد (قد يكون هو المرسل نفسه).')
    transport_vehicle_plate = fields.Char(string='رقم لوحة السيارة')
    escort_security = fields.Boolean(string='مرافقة أمنية',
        help='هل تم النقل بمرافقة أمنية رسمية؟')

    # المستلم
    receiver_unit_type = fields.Selection([
        ('internal_branch',  'فرع داخلي بالمحافظة'),
        ('other_governorate','محافظة أخرى'),
        ('mof_central',      'وزارة المالية المركزية'),
        ('cbe',              'البنك المركزي المصري'),
        ('other_entity',     'جهة حكومية أخرى'),
    ], string='نوع الجهة المستلمة', required=True)
    receiver_unit_name = fields.Char(string='اسم الجهة المستلمة', required=True)
    receiver_employee_id = fields.Many2one('hr.employee',
        string='المستلم (لو داخلي)',
        help='للتحويلات داخل المحافظة: الموظف الذي استلم النقد.')
    receiver_external_name = fields.Char(string='اسم المستلم الخارجي',
        help='للجهات الخارجية: اسم ممثل الجهة المستلمة.')
    receiver_id_number = fields.Char(string='رقم قومي للمستلم',
        help='توثيقاً للاستلام.')

    # ── الغرض والمرجع ───────────────────────────────────────────────────────
    purpose = fields.Text(string='الغرض من التحويل', required=True)
    daftar55_id = fields.Many2one('port_said.daftar55',
        string='قيد دفتر 55 المرتبط',
        help='للتحويلات الناتجة عن إذن صرف معتمَد.')
    source_cash_book_id = fields.Many2one('port_said.cash.book',
        string='دفتر النقدية المصدر',
        help='للتحويلات الصادرة: الدفتر الذي يُخصَم منه.')

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',      'مسودة'),
        ('prepared',   'مُعدَّة للإرسال'),
        ('in_transit', 'في الطريق'),
        ('delivered',  'سُلِّمت'),
        ('confirmed',  'مُؤكَّدة'),
        ('disputed',   'متنازَع فيها'),
        ('lost',       'مفقودة / مسروقة'),
        ('cancelled',  'ملغاة'),
        ('closed',     'مغلقة'),
    ], string='الحالة', default='draft', tracking=True, required=True, index=True)

    # ── التنازع ─────────────────────────────────────────────────────────────
    disputed_amount = fields.Monetary(string='المبلغ المُتنازَع فيه',
        currency_field='currency_id',
        help='الفرق بين المبلغ المُرسَل والمُستلَم فعلياً.')
    dispute_reason = fields.Text(string='سبب التنازع')
    dispute_resolution = fields.Text(string='قرار تسوية التنازع')

    # ── الفقدان ─────────────────────────────────────────────────────────────
    police_report_number = fields.Char(string='رقم محضر الشرطة',
        help='مطلوب للتحويلات المفقودة أو المسروقة.')
    police_report_date = fields.Date(string='تاريخ محضر الشرطة')
    loss_description = fields.Text(string='وصف حادثة الفقدان/السرقة')

    # ── الإلغاء ─────────────────────────────────────────────────────────────
    cancellation_reason = fields.Text(string='سبب الإلغاء')

    # ── الربط بالفولية ──────────────────────────────────────────────────────
    folio_id = fields.Many2one('port_said.cash_transfer.folio',
        string='الفولية', readonly=True, index=True)

    # ── المرجعيات المحاسبية ─────────────────────────────────────────────────
    move_id = fields.Many2one('account.move',
        string='القيد المحاسبي', readonly=True)

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', readonly=True, copy=False,
        index=True)

    # ── التواقيع ────────────────────────────────────────────────────────────
    prepared_by = fields.Many2one('res.users',
        string='أعدَّ التحويل', readonly=True)
    approved_by = fields.Many2one('res.users',
        string='اعتمد الإرسال', readonly=True)
    closed_by = fields.Many2one('res.users',
        string='أغلق الملف', readonly=True)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('sequence_number', 'direction', 'amount', 'receiver_unit_name')
    def _compute_display_name(self):
        for rec in self:
            dir_label = 'مرسل' if rec.direction == 'outgoing' else 'وارد'
            rec.display_name = '%s [%s] — %s — %s' % (
                rec.sequence_number or '(مسودة)',
                dir_label,
                rec.receiver_unit_name or '—',
                rec.amount or 0,
            )

    # ── Constraints ──────────────────────────────────────────────────────────
    @api.constrains('amount')
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('مبلغ التحويل يجب أن يكون موجباً.'))

    @api.constrains('disputed_amount', 'amount')
    def _check_disputed_amount(self):
        for rec in self:
            if rec.disputed_amount < 0:
                raise ValidationError(_(
                    'المبلغ المُتنازَع فيه لا يمكن أن يكون سالباً.'))
            if rec.disputed_amount > rec.amount:
                raise ValidationError(_(
                    'المبلغ المُتنازَع فيه لا يتجاوز المبلغ الأصلي.'))

    @api.constrains('dispatch_datetime', 'arrival_datetime')
    def _check_dispatch_before_arrival(self):
        for rec in self:
            if rec.dispatch_datetime and rec.arrival_datetime:
                if rec.arrival_datetime < rec.dispatch_datetime:
                    raise ValidationError(_(
                        'تاريخ الوصول يجب أن يكون بعد المغادرة.'))

    @api.constrains('receiver_unit_type', 'receiver_employee_id', 'receiver_external_name')
    def _check_receiver_identity(self):
        for rec in self:
            if rec.receiver_unit_type == 'internal_branch' and not rec.receiver_employee_id:
                raise ValidationError(_(
                    'التحويل الداخلي يتطلب تحديد الموظف المستلم.'))
            if rec.receiver_unit_type != 'internal_branch' and \
               not rec.receiver_external_name:
                raise ValidationError(_(
                    'للجهات الخارجية، يجب ذكر اسم المستلم الخارجي.'))

    # ── Lifecycle ────────────────────────────────────────────────────────────
    def action_prepare(self):
        """انتقال من مسودة إلى مُعدَّة للإرسال — يُولَّد التسلسل القانوني."""
        Seq = self.env['ir.sequence']
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('التحويل ليس في حالة مسودة.'))
            if not rec.sequence_number:
                seq_code = ('port_said.cash_transfer.outgoing'
                           if rec.direction == 'outgoing'
                           else 'port_said.cash_transfer.incoming')
                rec.sequence_number = Seq.next_by_code(seq_code) or '/'
            # السنة المالية
            if rec.transfer_date and not rec.fiscal_year:
                m, y = rec.transfer_date.month, rec.transfer_date.year
                if m >= 7:
                    rec.fiscal_year = '%d/%d' % (y, y + 1)
                else:
                    rec.fiscal_year = '%d/%d' % (y - 1, y)
            rec.state = 'prepared'
            rec.preparation_date = fields.Datetime.now()
            rec.prepared_by = self.env.user.id

    def action_dispatch(self):
        """اعتماد الإرسال وخروج النقد من الخزينة."""
        for rec in self:
            if rec.state != 'prepared':
                raise UserError(_('التحويل ليس مُعدَّاً للإرسال.'))
            rec.state = 'in_transit'
            if not rec.dispatch_datetime:
                rec.dispatch_datetime = fields.Datetime.now()
            rec.approved_by = self.env.user.id

    def action_mark_delivered(self):
        """تأكيد الوصول المادي — تُضاف الشهادة من المستلم."""
        for rec in self:
            if rec.state != 'in_transit':
                raise UserError(_('التحويل ليس في الطريق.'))
            rec.state = 'delivered'
            if not rec.arrival_datetime:
                rec.arrival_datetime = fields.Datetime.now()

    def action_confirm(self):
        """تأكيد رسمي من المستلم بعد عدّ النقد."""
        for rec in self:
            if rec.state != 'delivered':
                raise UserError(_('التحويل لم يُسلَّم بعد.'))
            rec.state = 'confirmed'
            rec.confirmation_date = fields.Datetime.now()

    def action_dispute(self):
        """فتح ملف تنازع — اختلاف في العد."""
        for rec in self:
            if rec.state not in ('delivered',):
                raise UserError(_(
                    'التنازع يُفتَح فقط عند التسليم قبل التأكيد.'))
            if not rec.dispute_reason:
                raise UserError(_('يجب تسجيل سبب التنازع.'))
            if not rec.disputed_amount:
                raise UserError(_(
                    'يجب تسجيل قيمة المبلغ المُتنازَع فيه.'))
            rec.state = 'disputed'

    def action_resolve_dispute(self):
        """تسوية التنازع وإغلاقه."""
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('التسوية تتطلب صلاحية مدير حسابات.'))
        for rec in self:
            if rec.state != 'disputed':
                raise UserError(_('ليس هناك تنازع قيد الحل.'))
            if not rec.dispute_resolution:
                raise UserError(_('يجب تسجيل قرار تسوية التنازع.'))
            rec.state = 'confirmed'
            rec.confirmation_date = fields.Datetime.now()

    def action_report_lost(self):
        """إبلاغ رسمي عن فقدان/سرقة — يتطلب محضر شرطة."""
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('الإبلاغ يتطلب صلاحية مدير حسابات.'))
        for rec in self:
            if rec.state not in ('in_transit', 'disputed'):
                raise UserError(_(
                    'الفقدان يُسجَّل فقط للتحويلات في الطريق أو المتنازَع فيها.'))
            if not rec.police_report_number or not rec.loss_description:
                raise UserError(_(
                    'يجب إدخال رقم محضر الشرطة ووصف الحادثة قبل الإبلاغ.'))
            rec.state = 'lost'
            rec.message_post(body=_(
                '⚠ تم الإبلاغ عن فقدان/سرقة التحويل. محضر: %s. الوصف: %s'
            ) % (rec.police_report_number, rec.loss_description))

    def action_close(self):
        """إغلاق الملف نهائياً."""
        for rec in self:
            if rec.state not in ('confirmed', 'lost', 'cancelled'):
                raise UserError(_(
                    'الإغلاق متاح فقط للتحويلات المُؤكَّدة أو المفقودة أو الملغاة.'))
            rec.state = 'closed'
            rec.closed_by = self.env.user.id

    def action_cancel(self):
        """إلغاء — متاح فقط قبل التسليم."""
        for rec in self:
            if rec.state in ('delivered', 'confirmed', 'closed'):
                raise UserError(_(
                    'لا يمكن إلغاء تحويل مُسَلَّم. استخدم "تنازع" بدلاً منه.'))
            if not rec.cancellation_reason:
                raise UserError(_('يجب تسجيل سبب الإلغاء.'))
            rec.state = 'cancelled'

    # ── Write Protection ────────────────────────────────────────────────────
    def write(self, vals):
        protected = {'direction', 'amount', 'transfer_date',
                    'sender_employee_id', 'receiver_unit_name'}
        if any(f in vals for f in protected):
            for rec in self:
                if rec.state in ('confirmed', 'closed', 'lost'):
                    raise UserError(_(
                        'لا يجوز تعديل تحويل نهائي (%s).'
                    ) % rec.sequence_number)
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('لا يجوز حذف تحويل بعد الإعداد.'))
        return super().unlink()
