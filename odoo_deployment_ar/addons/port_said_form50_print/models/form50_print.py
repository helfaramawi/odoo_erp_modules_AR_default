# -*- coding: utf-8 -*-
"""
port_said_form50_print — طبقة الطباعة الرسمية لاستمارة 50 ع.ح

يُوسِّع port_said.daftar55 بطبقة طباعة فقط.
لا يُعدِّل أي منطق محاسبي.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# حقول التاريخ تُعرَض باللون الأزرق
DATE_FIELDS_F50 = {2, 13, 17, 21, 25, 32, 54, 58, 60, 63, 70}

# ── أنواع العمليات ──────────────────────────────────────────────────────────
TRANSACTION_TYPES = [
    ('inventory_purchase', 'شراء أصناف مخزنية'),
    ('service',            'خدمات وتعاقدات'),
    ('contract',           'عقود طويلة الأمد'),
    ('maintenance',        'صيانة وإصلاح'),
    ('salary',             'مرتبات واستحقاقات'),
    ('refund',             'رد تأمين'),
    ('other',              'أخرى'),
]

# ── قوالب المرفقات حسب نوع العملية ─────────────────────────────────────────
ATTACHMENT_TEMPLATES = {
    'inventory_purchase': [
        ('national_id',       'صورة بطاقة الرقم القومي / السجل التجاري'),
        ('bank_letter',       'خطاب معتمد من البنك'),
        ('commitment_form',   'نموذج طلب الارتباط'),
        ('purchase_memo',     'مذكرة الشراء'),
        ('supply_order',      'أمر التوريد'),
        ('invoices',          'الفواتير الأصلية'),
        ('store_declaration', 'إقرار أمين المخازن بالاستلام'),
        ('committee_report',  'محضر لجنة الفحص (نموذج 12 مخازن)'),
        ('addition_permit',   'إذن الإضافة (نموذج 1 مخازن حكومية)'),
        ('tender_docs',       'مستندات إجراءات الشراء / كراسة الشروط'),
    ],
    'service': [
        ('national_id',    'صورة بطاقة الرقم القومي / السجل التجاري'),
        ('bank_letter',    'خطاب معتمد من البنك'),
        ('commitment_form','نموذج طلب الارتباط'),
        ('contract',       'العقد أو الاتفاقية'),
        ('invoices',       'الفواتير / المطالبات'),
        ('delivery_proof', 'إثبات تقديم الخدمة'),
        ('tender_docs',    'مستندات الإجراءات'),
    ],
    'contract': [
        ('national_id',    'صورة السجل التجاري'),
        ('bank_letter',    'خطاب ضمان أو اعتماد بنكي'),
        ('commitment_form','نموذج الارتباط'),
        ('contract',       'العقد الأصلي'),
        ('invoices',       'المستخلصات / الفواتير'),
        ('guarantee',      'خطاب الضمان الابتدائي/النهائي'),
        ('delivery_proof', 'محضر التسليم'),
    ],
    'maintenance': [
        ('national_id',       'صورة بطاقة الرقم القومي / السجل التجاري'),
        ('bank_letter',       'خطاب معتمد من البنك'),
        ('commitment_form',   'نموذج طلب الارتباط'),
        ('work_order',        'أمر العمل'),
        ('invoices',          'الفواتير'),
        ('completion_report', 'تقرير إتمام الأعمال'),
    ],
    'salary': [
        ('payroll_list',  'كشف المرتبات'),
        ('bank_letter',   'خطاب البنك'),
        ('commitment_form','نموذج الارتباط'),
    ],
    'refund': [
        ('national_id',      'صورة بطاقة الرقم القومي'),
        ('bank_letter',      'خطاب البنك'),
        ('refund_request',   'طلب رد التأمين'),
        ('original_receipt', 'إيصال الإيداع الأصلي'),
    ],
    'other': [
        ('national_id',      'صورة بطاقة الرقم القومي'),
        ('bank_letter',      'خطاب معتمد من البنك'),
        ('commitment_form',  'نموذج طلب الارتباط'),
        ('invoices',         'الفواتير / المستندات'),
        ('supporting_docs',  'مستندات داعمة أخرى'),
    ],
}


class Form50InvoiceLine(models.Model):
    """سطر فاتورة في جدول بيانات الفواتير."""
    _name        = 'port_said.form50.invoice.line'
    _description = 'سطر فاتورة — استمارة 50 ع.ح'
    _order       = 'sequence, id'

    daftar55_id     = fields.Many2one('port_said.daftar55', ondelete='cascade', required=True, index=True)
    sequence        = fields.Integer(default=10)
    invoice_ref     = fields.Char(string='رقم الفاتورة', required=True)
    invoice_date    = fields.Date(string='التاريخ', required=True)
    description     = fields.Char(string='البيان', required=True)
    amount_pounds   = fields.Integer(string='جنيه', required=True)
    amount_piasters = fields.Integer(string='قرش', default=0)
    attachment_id   = fields.Many2one('ir.attachment', string='ملف الفاتورة')


class Form50PrintLayer(models.Model):
    """طبقة الطباعة الرسمية — تُوسِّع port_said.daftar55."""
    _inherit = 'port_said.daftar55'

    # ── نوع العملية ──────────────────────────────────────────────────────────
    transaction_type = fields.Selection(
        TRANSACTION_TYPES, string='نوع العملية',
        default='inventory_purchase', tracking=True,
    )

    # ── سطور الفواتير ─────────────────────────────────────────────────────
    invoice_line_ids = fields.One2many(
        'port_said.form50.invoice.line', 'daftar55_id', string='بيانات الفواتير',
    )
    invoices_total_pounds   = fields.Integer(compute='_compute_invoices_total', store=True)
    invoices_total_piasters = fields.Integer(compute='_compute_invoices_total', store=True)
    invoices_match_gross    = fields.Boolean(
        string='الفواتير مطابقة للإجمالي',
        compute='_compute_invoices_total', store=True,
    )

    @api.depends('invoice_line_ids.amount_pounds', 'invoice_line_ids.amount_piasters', 'amount_gross')
    def _compute_invoices_total(self):
        for rec in self:
            total = sum(l.amount_pounds + l.amount_piasters / 100.0 for l in rec.invoice_line_ids)
            rec.invoices_total_pounds   = int(total)
            rec.invoices_total_piasters = round((total - int(total)) * 100)
            rec.invoices_match_gross    = bool(rec.invoice_line_ids) and abs(total - (rec.amount_gross or 0)) < 0.01

    # ── حقول طباعة المعاينة ──────────────────────────────────────────────
    preview_print_count = fields.Integer(default=0, readonly=True)
    last_preview_at     = fields.Datetime(readonly=True)
    last_preview_by     = fields.Many2one('res.users', readonly=True)

    # ── حقول الطباعة النهائية ────────────────────────────────────────────
    final_pdf_attachment_id = fields.Many2one('ir.attachment', readonly=True, tracking=True, copy=False)
    final_print_count       = fields.Integer(default=0, readonly=True, tracking=True)
    last_printed_at         = fields.Datetime(readonly=True, tracking=True)
    last_printed_by         = fields.Many2one('res.users', readonly=True, tracking=True)
    reprint_reason          = fields.Text(copy=False)
    official_template_version = fields.Char(default='Form-50-AH-v1.0-2024', readonly=True, tracking=True)
    is_final_printed = fields.Boolean(compute='_compute_is_final_printed', store=True)

    @api.depends('final_print_count')
    def _compute_is_final_printed(self):
        for rec in self:
            rec.is_final_printed = rec.final_print_count > 0

    # ── المرفقات الديناميكية ─────────────────────────────────────────────
    required_attachments_info = fields.Text(compute='_compute_required_attachments_info')
    missing_attachments_count = fields.Integer(compute='_compute_attachment_readiness', store=True)
    attachments_complete      = fields.Boolean(compute='_compute_attachment_readiness', store=True)

    @api.depends('transaction_type')
    def _compute_required_attachments_info(self):
        for rec in self:
            template = ATTACHMENT_TEMPLATES.get(rec.transaction_type or 'other', [])
            rec.required_attachments_info = '\n'.join(f'• {label}' for _, label in template)

    @api.depends('transaction_type', 'invoice_line_ids')
    def _compute_attachment_readiness(self):
        for rec in self:
            # البحث عن الاضبارة المرتبطة
            dossier = self.env['port_said.dossier'].search(
                [('daftar55_id', '=', rec.id)], limit=1
            )
            if dossier:
                # عدّ سطور المرفقات الفعلية التي لها ملف مرفوع
                actual_cnt = self.env['port_said.dossier.attachment'].search_count([
                    ('dossier_id', '=', dossier.id),
                    ('attachment_id', '!=', False),
                ])
                rec.missing_attachments_count = 0
                rec.attachments_complete      = actual_cnt > 0
            else:
                template     = ATTACHMENT_TEMPLATES.get(rec.transaction_type or 'other', [])
                rec.missing_attachments_count = len(template)
                rec.attachments_complete      = False

    # ── جاهزية الطباعة ───────────────────────────────────────────────────
    print_readiness_notes = fields.Text(compute='_compute_print_readiness')
    can_final_print       = fields.Boolean(compute='_compute_print_readiness')

    def _compute_print_readiness(self):
        for rec in self:
            issues = []
            if rec.state not in ('cleared', 'posted', 'archived'):
                issues.append('❌ الحالة يجب أن تكون: مُسمَّح أو مرحَّل أو محفوظ')
            if not rec.invoice_line_ids:
                issues.append('❌ يجب إضافة سطور الفواتير في تبويب "بيانات الفواتير"')
            if rec.invoice_line_ids and not rec.invoices_match_gross:
                issues.append('❌ إجمالي الفواتير لا يتطابق مع إجمالي الأصل')
            # للشراء المخزني — التحقق من إذن الإضافة عبر purchase_order_id
            if rec.transaction_type == 'inventory_purchase':
                po_id = getattr(rec, 'purchase_order_id', False)
                if po_id:
                    additions = self.env['stock.addition.permit'].search([
                        ('purchase_order_id', '=', po_id.id),
                        ('state', '=', 'posted'),
                    ], limit=1)
                    if not additions:
                        issues.append('❌ لم يُرحَّل إذن الإضافة — مطلوب للشراء المخزني')
            if not rec.attachments_complete:
                dossier = self.env['port_said.dossier'].search([('daftar55_id', '=', rec.id)], limit=1)
                if not dossier:
                    issues.append('❌ لا توجد اضبارة مرتبطة — أنشئ اضبارة وأضف المرفقات')
                else:
                    real_count = self.env['port_said.dossier.attachment'].search_count([
                        ('dossier_id', '=', dossier.id),
                        ('attachment_id', '!=', False),
                    ])
                    if real_count == 0:
                        issues.append('❌ الاضبارة موجودة لكن لم يُرفع أي ملف بعد')
            if not rec.daftar224_sequence:
                issues.append('⚠ رقم مسلسل دفتر 224 غير مُسجَّل (يُنشأ عند الترحيل)')
            if rec.final_print_count > 0 and not rec.reprint_reason:
                issues.append('❌ إعادة الطباعة تستلزم إدخال سبب في حقل "سبب إعادة الطباعة"')
            rec.print_readiness_notes = '\n'.join(issues) if issues else '✅ الاستمارة جاهزة للطباعة النهائية'
            rec.can_final_print       = not bool(issues)

    # ── الإجراءات ─────────────────────────────────────────────────────────
    def action_print_preview(self):
        self.ensure_one()
        self.sudo().write({
            'preview_print_count': self.preview_print_count + 1,
            'last_preview_at':     fields.Datetime.now(),
            'last_preview_by':     self.env.uid,
        })
        self.message_post(body=_('🖨 معاينة استمارة 50 — بواسطة %s') % self.env.user.name)
        return self.env.ref('port_said_form50_print.action_report_form50_preview').report_action(self)

    def action_print_final(self):
        self.ensure_one()
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('الطباعة النهائية للمدير المالي فقط.'))
        if not self.can_final_print:
            raise UserError(_('لا يمكن الطباعة النهائية:\n%s') % self.print_readiness_notes)
        self.write({
            'final_print_count': self.final_print_count + 1,
            'last_printed_at':   fields.Datetime.now(),
            'last_printed_by':   self.env.uid,
        })
        msg = _('✅ طباعة نهائية رقم %(n)s لاستمارة %(seq)s — بواسطة: %(u)s') % {
            'n': self.final_print_count,
            'seq': self.sequence_number,
            'u': self.env.user.name,
        }
        if self.final_print_count > 1 and self.reprint_reason:
            msg += _('\nسبب إعادة الطباعة: %s') % self.reprint_reason
        self.message_post(body=msg)
        return self.env.ref('port_said_form50_print.action_report_form50_final').report_action(self)

    def action_open_reprint_wizard(self):
        self.ensure_one()
        if not self.is_final_printed:
            raise UserError(_('استخدم "طباعة نهائية" للطباعة الأولى.'))
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('إعادة الطباعة للمدير المالي فقط.'))
        return {
            'type':      'ir.actions.act_window',
            'name':      'سبب إعادة الطباعة',
            'res_model': 'form50.reprint.wizard',
            'view_mode': 'form',
            'target':    'new',
            'context':   {'default_daftar55_id': self.id},
        }

    def action_validate_for_print(self):
        self.ensure_one()
        if self.can_final_print:
            return {
                'type': 'ir.actions.client',
                'tag':  'display_notification',
                'params': {
                    'title':   'جاهز للطباعة',
                    'message': '✅ الاستمارة مستوفية جميع شروط الطباعة النهائية.',
                    'type':    'success',
                    'sticky':  False,
                }
            }
        raise UserError(_('الاستمارة غير جاهزة:\n\n%s') % self.print_readiness_notes)

    # ── helpers للـ QWeb ─────────────────────────────────────────────────
    def _get_amount_pounds_piasters(self, amount):
        if not amount:
            return 0, 0
        amount = round(float(amount), 2)
        return int(amount), round((amount - int(amount)) * 100)

    def _get_budget_parts(self):
        self.ensure_one()
        parts = (self.budget_line or '').split('/')
        return {
            'bab':   parts[0] if len(parts) > 0 else '',
            'fasle': parts[1] if len(parts) > 1 else '',
            'band':  parts[2] if len(parts) > 2 else '',
            'noa':   parts[3] if len(parts) > 3 else '',
        }


    # ── محرك الطباعة الديناميكي من ملف المواضع ─────────────────────────────
    def _form50_positions(self):
        self.ensure_one()
        # مواضع الحقول — (left%, top%) نسبة لأبعاد الصورة 1240×1754px
        # left% = image_x_px / 1240 * 100  |  top% = image_y_px / 1754 * 100
        # محسوبة بتحليل pixel لمناطق التعبئة والحدود العمودية الفعلية في الخلفية
        return {
            # ── قسم أ — رقم مسلسل وتاريخ (x=1046-1240) ─────────────────────
            # صفوف: y=162-196 center=179(10.2%), y=196-230 center=213(12.1%)
            1:  (86.0, 10.2),   # رقم المسلسل
            2:  (86.0, 12.1),   # تاريخ الورود

            # ── يسار — بيانات المصلحة والمستفيد ─────────────────────────────
            # مراكز مناطق التعبئة من تحليل الصورة
            3:  (21.7,  8.2),   # مصلحة         y=144  center_x=269
            4:  (26.0, 10.5),   # قسم            y=184  center_x=323
            5:  (26.8, 12.1),   # المبلغ المستحق y=213  center_x=333
            6:  (25.0, 14.0),   # بموجب          y=245  center_x=310
            7:  (25.0, 17.4),   # صار مراجعته    y=305  center_x=310
            8:  (24.0, 20.9),   # إذن صرف        y=366  center_x=297
            9:  (22.7, 22.6),   # شيك             y=397  center_x=282
            10: (24.7, 26.1),   # يسحب باسم      y=457  center_x=306
            11: (29.2, 29.5),   # ويرسل           y=517  center_x=362

            # ── جدول الفواتير ─────────────────────────────────────────────────
            # حدود عمودية فعلية: x=726,785,886,986,1046
            # أعمدة: قرش=60.9%(x=729-782), جنيه=67.3%(x=788-883),
            #         تاريخ=75.5%(x=889-984), رقم=81.9%(x=989-1043)
            # صفوف (مراكز بين الحدود الأفقية):
            # R1=10.2%(y=179), R2=12.1%(y=213), R3=13.5%(y=238),
            # R4=15.7%(y=275), جملة=18.0%(y=316)
            12: (81.9, 10.2), 13: (75.5, 10.2), 14: (67.3, 10.2), 15: (60.9, 10.2),
            16: (81.9, 12.1), 17: (75.5, 12.1), 18: (67.3, 12.1), 19: (60.9, 12.1),
            20: (81.9, 13.5), 21: (75.5, 13.5), 22: (67.3, 13.5), 23: (60.9, 13.5),
            24: (81.9, 15.7), 25: (75.5, 15.7), 26: (67.3, 15.7), 27: (60.9, 15.7),
            28: (67.3, 18.0), 29: (60.9, 18.0),  # الجملة

            # ── قسم ب ─────────────────────────────────────────────────────────
            30: (26.4, 32.6),   # كاتب المنوط    y=573 c=328(26.4%)
            31: (65.6, 32.6),   # تقييد سجل ز    y=573 c=814(65.6%)
            32: (80.2, 31.9),   # الشتمذ ب        y=560 c=995(80.2%)

            # ── الاعتماد الإداري ──────────────────────────────────────────────
            # صف البيانات: y≈757(43.1%) — أعمدة ثابتة y=715-800
            # 7.7%, 29.7%, 48.7%, 53.5%, 58.2%, 63.0%, 69.6%, 76.1%, 82.7%, 90.9%
            33: ( 7.7, 43.1),   # عدد المرفقات
            34: (48.7, 43.1),   # بند
            35: (53.5, 43.1),   # فصل
            36: (58.2, 43.1),   # فرع/نوع
            37: (63.0, 43.1),   # قسم/باب
            38: (76.1, 43.1),   # إجمالي — جنيه
            39: (90.9, 43.1),   # إجمالي — قرش
            40: (76.1, 47.9),   # إجمالي الأصل — جنيه  y=840(47.9%)
            41: (90.9, 47.9),   # إجمالي الأصل — قرش

            # ── الاستقطاعات ───────────────────────────────────────────────────
            # صف 1 (f42-47): y=1013(57.7%) — مراكز: 16.5%,19.6%,34.0%,40.3%,55.1%,59.9%
            42: (16.5, 57.7),   # دمغة عادية    — جنيه
            43: (19.6, 57.7),   # دمغة عادية    — قرش
            44: (34.0, 57.7),   # دمغة إضافية   — جنيه
            45: (40.3, 57.7),   # دمغة إضافية   — قرش
            46: (55.1, 57.7),   # دمغة نسبية    — جنيه
            47: (59.9, 57.7),   # دمغة نسبية    — قرش
            # صف 2 (f48-49): y=1038(59.2%) — ضريبة الأرباح
            48: (19.0, 59.2),   # ضريبة الأرباح — جنيه
            49: (37.4, 59.2),   # ضريبة الأرباح — قرش

            # ── صافي القيمة والتفقيط ──────────────────────────────────────────
            # y=1148(65.5%): c=11.0%,36.9%,61.0%,75.6%,93.5%
            50: (61.0, 65.5),   # صافي — جنيه
            51: (36.9, 65.5),   # صافي — قرش
            52: (26.7, 67.8),   # التفقيط بالكلام  y=1188(67.8%)

            # ── الإقرار ────────────────────────────────────────────────────────
            53: (49.0, 71.3),   # في سنة  y=1250(71.3%) c=610(49%)
            54: (85.0, 71.3),   # الشتمذ

            # ── توقيعات قسم ج ─────────────────────────────────────────────────
            # y=1284(73.2%): c=8.8%,44.0%,55.5%,83.4%,91.4%
            55: ( 8.8, 73.2),   # مراقب الحسابات
            56: ( 8.8, 75.0),   # رئيس الحسابات   y=1324(75.0%)
            57: (44.0, 73.2),   # حساب البنك
            58: (55.5, 73.2),   # بتاريخ
            59: (24.4, 74.1),   # رئيس المصلحة    y=1300(74.1%)
            60: (91.3, 74.1),   # الشتمذ ج

            # ── قسم ج — سجل 55 والاعتمادات ───────────────────────────────────
            61: (27.9, 76.4),   # قيد رقم 55     y=1340(76.4%) c=27.9%
            62: (21.9, 77.0),   # روجع سنة        y=1350(77.0%) c=21.9%
            63: (59.4, 77.0),   # روجع تاريخ      y=1350(77.0%) c=59.4%
            64: (38.7, 82.1),   # شيك اسم         y=1440(82.1%) c=38.7%
            65: (41.2, 84.9),   # يعتمد سحب       y=1490(84.9%) c=41.2%
            66: (61.8, 87.2),   # وكيل الحسابات   y=1530(87.2%) c=61.8%
            67: (17.5, 87.2),   # رئيس الحسابات   y=1530(87.2%) c=17.5%
            68: (43.5, 89.5),   # في سنة صرف      y=1570(89.5%) c=43.5%
            69: (27.6, 90.1),   # بمبلغ            y=1580(90.1%) c=27.6%

            # ── قسم د ─────────────────────────────────────────────────────────
            70: (67.7, 92.4),   # الشتمذ د         y=1620(92.4%) c=67.7%
            71: (42.2, 91.8),   # رقم قيد 224      y=1610(91.8%) c=42.2%
            72: (11.0, 91.8),   # كاتب منوط         y=1610(91.8%) c=11.0%
            73: (20.5, 88.4),   # موظفي الشطب       y=1550(88.4%) c=20.5%
            74: (63.4, 91.8),   # رقم أمر الدفع     y=1610(91.8%) c=63.4%
            75: (83.8, 91.8),   # اسم سحب/شيك       y=1610(91.8%) c=83.8%
        }

    def _form50_field_models(self):
        self.ensure_one()
        return {
            1:  {'label': 'رقم المسلسل',              'model': 'sequence_number'},
            2:  {'label': 'تاريخ الورود',              'model': 'date_received'},
            3:  {'label': 'مصلحة',                     'model': 'department_name'},
            4:  {'label': 'قسم / الإدارة',             'model': 'division_name'},
            5:  {'label': 'المبلغ المستحق إلى',        'model': 'vendor_id.name'},
            6:  {'label': 'بموجب / رقم الارتباط',     'model': 'commitment_ref'},
            7:  {'label': 'صار مراجعته',               'model': 'vendor_id.name'},
            8:  {'label': 'إذن صرف على / البنك',      'model': 'bank_name'},
            9:  {'label': 'شيك على الشارج',            'model': 'vendor_id.name'},
            10: {'label': 'يسحب باسم',                 'model': 'vendor_id.name'},
            11: {'label': 'ويرسل إليه على العنوان',   'model': 'vendor_id.street'},
            # جدول الفواتير
            12: {'label': 'فاتورة 1 — رقم',           'model': 'invoice_line_ids[0].invoice_ref'},
            13: {'label': 'فاتورة 1 — تاريخ',         'model': 'invoice_line_ids[0].invoice_date'},
            14: {'label': 'فاتورة 1 — جنيه',          'model': 'invoice_line_ids[0].amount_pounds'},
            15: {'label': 'فاتورة 1 — قرش',           'model': 'invoice_line_ids[0].amount_piasters'},
            16: {'label': 'فاتورة 2 — رقم',           'model': 'invoice_line_ids[1].invoice_ref'},
            17: {'label': 'فاتورة 2 — تاريخ',         'model': 'invoice_line_ids[1].invoice_date'},
            18: {'label': 'فاتورة 2 — جنيه',          'model': 'invoice_line_ids[1].amount_pounds'},
            19: {'label': 'فاتورة 2 — قرش',           'model': 'invoice_line_ids[1].amount_piasters'},
            20: {'label': 'فاتورة 3 — رقم',           'model': 'invoice_line_ids[2].invoice_ref'},
            21: {'label': 'فاتورة 3 — تاريخ',         'model': 'invoice_line_ids[2].invoice_date'},
            22: {'label': 'فاتورة 3 — جنيه',          'model': 'invoice_line_ids[2].amount_pounds'},
            23: {'label': 'فاتورة 3 — قرش',           'model': 'invoice_line_ids[2].amount_piasters'},
            24: {'label': 'فاتورة 4 — رقم',           'model': 'invoice_line_ids[3].invoice_ref'},
            25: {'label': 'فاتورة 4 — تاريخ',         'model': 'invoice_line_ids[3].invoice_date'},
            26: {'label': 'فاتورة 4 — جنيه',          'model': 'invoice_line_ids[3].amount_pounds'},
            27: {'label': 'فاتورة 4 — قرش',           'model': 'invoice_line_ids[3].amount_piasters'},
            28: {'label': 'الجملة — جنيه',             'model': 'amount_gross (pounds)'},
            29: {'label': 'الجملة — قرش',              'model': 'amount_gross (piasters)'},
            # قسم ب
            30: {'label': 'الكاتب المنوط',             'model': 'writer_assigned'},
            31: {'label': 'تقييد في سجل (ز)',          'model': 'register_z_ref'},
            32: {'label': 'تاريخ الشتمذ ب',           'model': 'date_received'},
            # الجدول الرئيسي
            33: {'label': 'عدد المرفقات',              'model': 'real_attachment_count'},
            34: {'label': 'بند',                        'model': "_get_budget_parts()['band']"},
            35: {'label': 'فصل',                        'model': "_get_budget_parts()['fasle']"},
            36: {'label': 'فرع / نوع',                 'model': "_get_budget_parts()['noa']"},
            37: {'label': 'قسم / باب',                 'model': "_get_budget_parts()['bab']"},
            38: {'label': 'إجمالي — جنيه',             'model': 'amount_gross (pounds)'},
            39: {'label': 'إجمالي — قرش',              'model': 'amount_gross (piasters)'},
            40: {'label': 'إجمالي الأصل — جنيه',      'model': 'amount_gross (pounds)'},
            41: {'label': 'إجمالي الأصل — قرش',       'model': 'amount_gross (piasters)'},
            # الاستقطاعات — جنيه وقرش منفصلَين
            42: {'label': 'دمغة عادية — جنيه',        'model': 'deductions_stamp_normal (pounds)'},
            43: {'label': 'دمغة عادية — قرش',         'model': 'deductions_stamp_normal (piasters)'},
            44: {'label': 'دمغة إضافية — جنيه',       'model': 'deductions_stamp_extra (pounds)'},
            45: {'label': 'دمغة إضافية — قرش',        'model': 'deductions_stamp_extra (piasters)'},
            46: {'label': 'دمغة نسبية — جنيه',        'model': 'deductions_stamp_proportional (pounds)'},
            47: {'label': 'دمغة نسبية — قرش',         'model': 'deductions_stamp_proportional (piasters)'},
            48: {'label': 'ضريبة الأرباح — جنيه',     'model': 'deductions_commercial_tax (pounds)'},
            49: {'label': 'ضريبة الأرباح — قرش',      'model': 'deductions_commercial_tax (piasters)'},
            # الصافي والتفقيط
            50: {'label': 'صافي القيمة — جنيه',       'model': 'amount_net (pounds)'},
            51: {'label': 'صافي القيمة — قرش',        'model': 'amount_net (piasters)'},
            52: {'label': 'التفقيط بالكلام',           'model': 'amount_words'},
            # الإقرار
            53: {'label': 'في سنة (إقرار)',            'model': 'fiscal_year'},
            54: {'label': 'علامة / تاريخ',             'model': 'date_received'},
            # توقيعات قسم ج
            55: {'label': 'إمضاء 1 — مراقب الحسابات', 'model': 'auditor_id.name'},
            56: {'label': 'إمضاء 2 — رئيس الحسابات',  'model': 'accounts_head_id.name'},
            57: {'label': 'حساب البنك',                'model': 'bank_account_no'},
            58: {'label': 'بتاريخ',                    'model': 'date_received'},
            59: {'label': 'إمضاء 3 — رئيس المصلحة',  'model': 'section_head_id.name'},
            60: {'label': 'تاريخ الشتمذ ج',           'model': 'date_received'},
            # قسم ج — سجل 55
            61: {'label': 'قيد في سجل رقم 55',        'model': 'sequence_number'},
            62: {'label': 'روجع في — سنة',             'model': 'fiscal_year'},
            63: {'label': 'روجع في — تاريخ',           'model': 'reviewer_stamp_date'},
            64: {'label': 'شيك — اسم المستفيد',       'model': 'vendor_id.name'},
            65: {'label': 'يعتمد سحب — مبلغ',         'model': 'amount_net (pounds)'},
            66: {'label': 'إذن صرف — وكيل الحسابات', 'model': 'reviewer_id.name'},
            67: {'label': 'مدير / رئيس الحسابات',     'model': 'accounts_head_id.name'},
            68: {'label': 'في سنة (صرف)',              'model': 'fiscal_year'},
            69: {'label': 'بمبلغ (رقم)',               'model': 'amount_net (pounds)'},
            # قسم د
            70: {'label': 'تاريخ الشتمذ د',           'model': 'date_received'},
            71: {'label': 'رقم القيد في دفتر 224',    'model': 'daftar224_sequence'},
            72: {'label': 'إمضاء الكاتب المنوط',      'model': 'writer_assigned'},
            73: {'label': 'إمضاء موظفي الشطب',        'model': 'crossout_signed_by'},
            74: {'label': 'رقم أمر الدفع',             'model': 'payment_order_ref'},
            75: {'label': 'سحب / شيك — اسم',          'model': 'vendor_id.name'},
        }

    def _form50_resolve_expr(self, expr):
        self.ensure_one()
        import re
        from datetime import date, datetime

        if not expr:
            return ''

        m = re.match(r'^(?P<field>[\w_]+) \((?P<part>pounds|piasters)\)$', expr)
        if m:
            val = getattr(self, m.group('field'), 0) or 0
            pounds, piasters = self._get_amount_pounds_piasters(val)
            return str(pounds if m.group('part') == 'pounds' else piasters)

        m = re.match(r"^_get_budget_parts\(\)\['(?P<key>\w+)'\]$", expr)
        if m:
            return str((self._get_budget_parts() or {}).get(m.group('key'), '') or '')

        cur = self
        for token in expr.split('.'):
            m = re.match(r'^(?P<name>\w+)\[(?P<idx>\d+)\]$', token)
            if m:
                cur = getattr(cur, m.group('name'), [])
                idx = int(m.group('idx'))
                cur = cur[idx] if len(cur) > idx else False
            else:
                cur = getattr(cur, token, False)
            if cur in (False, None):
                return ''

        if hasattr(cur, 'name') and not isinstance(cur, (str, bytes)):
            try:
                return str(cur.name or '')
            except Exception:
                pass
        if isinstance(cur, (date, datetime)):
            return str(cur)
        return str(cur or '')

    def _form50_field_text(self, field_no):
        self.ensure_one()
        expr = self._form50_field_models().get(field_no, {}).get('model', '')
        return self._form50_resolve_expr(expr)

    def _form50_render_fields(self):
        self.ensure_one()
        positions = self._form50_positions()
        right_align = {3,4,5,6,7,8,9,10,11,52,55,56,57,58,59,64,65,66,67,72,73,74,75}
        bold_fields = {1,5,14,18,22,26,28,29,38,39,40,41,50,51,65,69,71}
        small_fields = {12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,42,43,44,45,46,47,48,49}
        wide_fields = {3,4,5,6,7,8,9,10,11,52,57,59,64,65,66,67,71,72,73,75}
        out = []
        for n in sorted(positions.keys(), key=lambda x: int(x)):
            x, y = positions[n]
            txt = self._form50_field_text(int(n))
            if not txt:
                continue
            font_size = 7.5 if n in small_fields else 9.0 if n in wide_fields else 8.0
            text_align = 'right' if n in right_align else 'center'
            font_weight = '700' if n in bold_fields else '400'
            max_width = '70%' if n == 52 else ('34%' if n in wide_fields else '14%')
            style = ';'.join([
                'position:absolute',
                f'left:{x}%',
                f'top:{y}%',
                'transform:translateY(-50%)',
                'line-height:1.25',
                'white-space:nowrap',
                'overflow:hidden',
                'text-overflow:clip',
                f'color:{"#0033cc" if n in DATE_FIELDS_F50 else "#111"}',
                'direction:rtl',
                'z-index:10',
                "font-family:Amiri,'Noto Naskh Arabic','DejaVu Sans',Arial,sans-serif",
                f'font-size:{font_size}pt',
                f'font-weight:{font_weight}',
                f'text-align:{text_align}',
                f'max-width:{max_width}',
            ])
            out.append({'n': int(n), 'x': x, 'y': y, 'text': txt, 'style': style})
        return out


def post_migrate(env):
    """تأكد من إيقاف attachment_use بعد كل upgrade."""
    env['ir.actions.report'].sudo().search([
        ('report_name', 'like', 'form50'),
    ]).write({'attachment_use': False, 'attachment': ''})
