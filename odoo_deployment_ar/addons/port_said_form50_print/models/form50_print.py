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
        # مواضع الحقول على استمارة 50 ع.ح — (left%, top%) نسبة لأبعاد الصفحة
        # left% = image_x_px / 1240 * 100  ,  top% = image_y_px / 1754 * 100
        # (بعد إزالة o_report_layout_standard الصفحة = 210mm × 297mm كاملة)
        return {
            # ── قسم أ — رقم مسلسل وتاريخ (يمين أعلى داخل إطار الأقسام) ──────
            1:  (87.0,  9.3),   # رقم المسلسل  — y≈163px
            2:  (87.0, 11.2),   # تاريخ الورود — y≈197px

            # ── قسم أ — بيانات المصلحة والمستفيد (يسار) ──────────────────────
            3:  (20.8,  8.3),   # مصلحة        — y≈144px
            4:  (20.8, 10.5),   # قسم/الإدارة  — y≈184px
            5:  (19.2, 12.3),   # المبلغ المستحق إلى — y≈215px
            6:  (19.2, 14.0),   # بموجب        — y≈245px
            7:  ( 6.4, 17.4),   # صار مراجعته  — y≈305px
            8:  (14.4, 20.9),   # إذن صرف      — y≈366px
            9:  (14.4, 22.6),   # شيك           — y≈397px
            10: (14.4, 26.1),   # يسحب باسم    — y≈457px
            11: ( 6.4, 29.5),   # ويرسل         — y≈517px

            # ── جدول الفواتير (يمين — 4 صفوف) — top% = مركز الصف ────────────
            12: (41.6,  9.7),   # فاتورة 1 — رقم
            13: (49.2,  9.7),   # فاتورة 1 — تاريخ
            14: (56.8,  9.7),   # فاتورة 1 — جنيه
            15: (63.6,  9.7),   # فاتورة 1 — قرش
            16: (41.6, 11.2),   # فاتورة 2 — رقم
            17: (49.2, 11.2),   # فاتورة 2 — تاريخ
            18: (56.8, 11.2),   # فاتورة 2 — جنيه
            19: (63.6, 11.2),   # فاتورة 2 — قرش
            20: (41.6, 13.0),   # فاتورة 3 — رقم
            21: (49.2, 13.0),   # فاتورة 3 — تاريخ
            22: (56.8, 13.0),   # فاتورة 3 — جنيه
            23: (63.6, 13.0),   # فاتورة 3 — قرش
            24: (41.6, 14.8),   # فاتورة 4 — رقم
            25: (49.2, 14.8),   # فاتورة 4 — تاريخ
            26: (56.8, 14.8),   # فاتورة 4 — جنيه
            27: (63.6, 14.8),   # فاتورة 4 — قرش
            28: (56.8, 16.8),   # الجملة — جنيه
            29: (63.6, 16.8),   # الجملة — قرش

            # ── قسم ب ─────────────────────────────────────────────────────────
            30: (50.4, 30.0),   # الكاتب المنوط
            31: (22.4, 30.0),   # تقييد في سجل (ز)
            32: (70.8, 34.5),   # تاريخ الشتمذ ب

            # ── الجدول الرئيسي — الاعتماد الإداري ────────────────────────────
            33: ( 4.0, 42.0),   # عدد المرفقات
            34: (36.0, 43.5),   # بند
            35: (41.2, 43.5),   # فصل
            36: (46.0, 43.5),   # فرع/نوع
            37: (51.2, 43.5),   # قسم/باب
            38: (56.8, 43.5),   # إجمالي — جنيه
            39: (63.6, 43.5),   # إجمالي — قرش
            40: (56.8, 48.0),   # إجمالي الأصل — جنيه
            41: (63.6, 48.0),   # إجمالي الأصل — قرش

            # ── بيانات الاستقطاعات ────────────────────────────────────────────
            42: (17.6, 57.0),   # دمغة عادية — جنيه
            43: (23.6, 57.0),   # دمغة عادية — قرش
            44: (31.2, 57.0),   # دمغة إضافية — جنيه
            45: (36.8, 57.0),   # دمغة إضافية — قرش
            46: (44.0, 57.0),   # دمغة نسبية — جنيه
            47: (49.6, 57.0),   # دمغة نسبية — قرش
            48: (17.6, 61.5),   # ضريبة الأرباح — جنيه
            49: (23.6, 61.5),   # ضريبة الأرباح — قرش

            # ── صافي القيمة والتفقيط ──────────────────────────────────────────
            50: (52.8, 65.5),   # صافي القيمة — جنيه
            51: (59.2, 65.5),   # صافي القيمة — قرش
            52: ( 8.0, 68.5),   # التفقيط بالكلام

            # ── الإقرار والتواريخ ─────────────────────────────────────────────
            53: (28.0, 71.5),   # في سنة
            54: (70.8, 71.0),   # علامة/تاريخ

            # ── توقيعات قسم ج ─────────────────────────────────────────────────
            55: ( 7.2, 74.0),   # مراقب الحسابات
            56: ( 7.2, 76.0),   # رئيس الحسابات
            57: (41.6, 73.0),   # حساب البنك
            58: (26.4, 73.0),   # بتاريخ
            59: ( 7.2, 78.0),   # رئيس المصلحة
            60: (70.8, 72.5),   # تاريخ الشتمذ ج

            # ── قسم ج — سجل 55 والاعتمادات ───────────────────────────────────
            61: (39.2, 77.0),   # قيد في سجل رقم 55
            62: (32.0, 79.5),   # روجع في — سنة
            63: (44.0, 79.5),   # روجع في — تاريخ
            64: (40.0, 83.0),   # شيك — اسم المستفيد
            65: (36.0, 86.0),   # يعتمد سحب — مبلغ
            66: (57.6, 89.0),   # إذن صرف — وكيل الحسابات
            67: (22.4, 89.0),   # مدير/رئيس الحسابات
            68: (32.0, 91.5),   # في سنة (صرف)
            69: ( 8.0, 91.0),   # بمبلغ (رقم)

            # ── قسم د ─────────────────────────────────────────────────────────
            70: (70.8, 92.5),   # تاريخ الشتمذ د
            71: (28.8, 93.5),   # رقم القيد في دفتر 224
            72: ( 8.0, 93.5),   # إمضاء الكاتب المنوط
            73: ( 8.0, 96.5),   # إمضاء موظفي الشطب
            74: (28.8, 96.5),   # رقم أمر الدفع
            75: (45.6, 96.5),   # سحب/شيك — اسم
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
