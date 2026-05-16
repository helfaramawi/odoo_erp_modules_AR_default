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

    # ── CSS الخط العربي للتقارير ─────────────────────────────────────────
    def _get_amiri_font_css(self):
        """يُرجع CSS يحتوي @font-face بترميز base64 لخط Amiri — مُخزَّن مؤقتاً."""
        global _AMIRI_CSS_CACHE
        if _AMIRI_CSS_CACHE is None:
            _AMIRI_CSS_CACHE = _build_amiri_css()
        return _AMIRI_CSS_CACHE

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
        return {1: (85.24, 2.17), 2: (85.0, 3.67), 3: (29.0, 7.8), 4: (30.0, 9.6), 5: (30.0, 11.4), 6: (30.0, 15.1), 7: (3.5, 17.3), 8: (15.0, 18.8), 9: (15.0, 20.7), 10: (15.0, 18.8), 11: (6.0, 27.8), 12: (59.5, 14.0), 13: (64.2, 14.0), 14: (72.4, 14.0), 15: (80.5, 14.0), 16: (59.5, 16.0), 17: (64.2, 16.0), 18: (72.4, 16.0), 19: (80.5, 16.0), 20: (59.5, 18.0), 21: (64.2, 18.0), 22: (72.4, 18.0), 23: (80.5, 18.0), 24: (59.5, 20.0), 25: (64.2, 20.0), 26: (72.4, 20.0), 27: (80.5, 20.0), 28: (72.4, 28.8), 29: (80.2, 28.8), 30: (59.0, 31.7), 31: (26.9, 31.7), 32: (97.0, 33.2), 33: (7.1, 38.9), 34: (47.1, 41.0), 35: (51.8, 41.0), 36: (56.6, 41.0), 37: (61.3, 41.0), 38: (66.2, 41.0), 39: (74.7, 41.0), 40: (66.2, 46.9), 41: (74.7, 46.9), 42: (66.2, 49.2), 43: (74.7, 49.2), 44: (66.2, 50.4), 45: (74.7, 50.4), 46: (66.2, 51.6), 47: (74.7, 51.6), 48: (66.2, 52.4), 49: (74.7, 52.4), 50: (66.3, 56.4), 51: (74.6, 56.4), 52: (17.8, 58.4), 53: (38.0, 61.2), 54: (89.3, 59.2), 55: (8.7, 61.2), 56: (8.7, 63.2), 57: (54.3, 66.8), 58: (33.6, 66.8), 59: (8.4, 66.7), 60: (90.0, 71.5), 61: (52.0, 72.0), 62: (43.0, 74.5), 63: (59.0, 74.0), 64: (55.0, 76.5), 65: (50.0, 79.5), 66: (75.0, 83.0), 67: (30.0, 82.0), 68: (43.0, 83.5), 69: (12.0, 84.0), 70: (90.0, 87.0), 71: (40.0, 88.0), 72: (12.0, 88.0), 73: (12.0, 91.5), 74: (40.0, 95.0), 75: (61.0, 95.0)}

    def _form50_field_models(self):
        self.ensure_one()
        return {1: {'label': 'رقم المسلسل', 'model': 'sequence_number'}, 2: {'label': 'تاريخ الورود', 'model': 'date_received'}, 3: {'label': 'مصلحة', 'model': 'department_name'}, 4: {'label': 'قسم / الإدارة', 'model': 'division_name'}, 5: {'label': 'المبلغ المستحق إلى', 'model': 'vendor_id.name'}, 6: {'label': 'بموجب / رقم الارتباط', 'model': 'commitment_ref'}, 7: {'label': 'صار مراجعته', 'model': 'vendor_id.name'}, 8: {'label': 'إذن صرف على / البنك', 'model': 'bank_name'}, 9: {'label': 'شيك على الشارج', 'model': 'vendor_id.name'}, 10: {'label': 'يسحب باسم', 'model': 'vendor_id.name'}, 11: {'label': 'ويرسل إليه على العنوان', 'model': 'vendor_id.street'}, 12: {'label': 'فاتورة 1 — رقم', 'model': 'invoice_line_ids[0].invoice_ref'}, 13: {'label': 'فاتورة 1 — تاريخ', 'model': 'invoice_line_ids[0].invoice_date'}, 14: {'label': 'فاتورة 1 — جنيه', 'model': 'invoice_line_ids[0].amount_pounds'}, 15: {'label': 'فاتورة 1 — قرش', 'model': 'invoice_line_ids[0].amount_piasters'}, 16: {'label': 'فاتورة 2 — رقم', 'model': 'invoice_line_ids[1].invoice_ref'}, 17: {'label': 'فاتورة 2 — تاريخ', 'model': 'invoice_line_ids[1].invoice_date'}, 18: {'label': 'فاتورة 2 — جنيه', 'model': 'invoice_line_ids[1].amount_pounds'}, 19: {'label': 'فاتورة 2 — قرش', 'model': 'invoice_line_ids[1].amount_piasters'}, 20: {'label': 'فاتورة 3 — رقم', 'model': 'invoice_line_ids[2].invoice_ref'}, 21: {'label': 'فاتورة 3 — تاريخ', 'model': 'invoice_line_ids[2].invoice_date'}, 22: {'label': 'فاتورة 3 — جنيه', 'model': 'invoice_line_ids[2].amount_pounds'}, 23: {'label': 'فاتورة 3 — قرش', 'model': 'invoice_line_ids[2].amount_piasters'}, 24: {'label': 'فاتورة 4 — رقم', 'model': 'invoice_line_ids[3].invoice_ref'}, 25: {'label': 'فاتورة 4 — تاريخ', 'model': 'invoice_line_ids[3].invoice_date'}, 26: {'label': 'فاتورة 4 — جنيه', 'model': 'invoice_line_ids[3].amount_pounds'}, 27: {'label': 'فاتورة 4 — قرش', 'model': 'invoice_line_ids[3].amount_piasters'}, 28: {'label': 'الجملة — جنيه', 'model': 'amount_gross (pounds)'}, 29: {'label': 'الجملة — قرش', 'model': 'amount_gross (piasters)'}, 30: {'label': 'الكاتب المنوط', 'model': 'writer_assigned'}, 31: {'label': 'تقييد في سجل (ز)', 'model': 'register_z_ref'}, 32: {'label': 'تاريخ الشتمذ ب', 'model': 'date_received'}, 33: {'label': 'عدد المرفقات', 'model': 'real_attachment_count'}, 34: {'label': 'بند', 'model': "_get_budget_parts()['band']"}, 35: {'label': 'فصل', 'model': "_get_budget_parts()['fasle']"}, 36: {'label': 'فرع / نوع', 'model': "_get_budget_parts()['noa']"}, 37: {'label': 'قسم / باب', 'model': "_get_budget_parts()['bab']"}, 38: {'label': 'إجمالي — جنيه', 'model': 'amount_gross (pounds)'}, 39: {'label': 'إجمالي — قرش', 'model': 'amount_gross (piasters)'}, 40: {'label': 'إجمالي الأصل — جنيه', 'model': 'amount_gross (pounds)'}, 41: {'label': 'إجمالي الأصل — قرش', 'model': 'amount_gross (piasters)'}, 42: {'label': 'دمغة عادية — جنيه', 'model': 'deductions_stamp_normal'}, 43: {'label': 'دمغة عادية — قرش', 'model': 'deductions_stamp_normal'}, 44: {'label': 'دمغة إضافية — جنيه', 'model': 'deductions_stamp_extra'}, 45: {'label': 'دمغة إضافية — قرش', 'model': 'deductions_stamp_extra'}, 46: {'label': 'دمغة نسبية — جنيه', 'model': 'deductions_stamp_proportional'}, 47: {'label': 'دمغة نسبية — قرش', 'model': 'deductions_stamp_proportional'}, 48: {'label': 'ضريبة الأرباح — جنيه', 'model': 'deductions_commercial_tax'}, 49: {'label': 'ضريبة الأرباح — قرش', 'model': 'deductions_commercial_tax'}, 50: {'label': 'صافي القيمة — جنيه', 'model': 'amount_net (pounds)'}, 51: {'label': 'صافي القيمة — قرش', 'model': 'amount_net (piasters)'}, 52: {'label': 'التفقيط بالكلام', 'model': 'amount_words'}, 53: {'label': 'في سنة (إقرار)', 'model': 'fiscal_year'}, 54: {'label': 'علامة / تاريخ', 'model': 'date_received'}, 55: {'label': 'إمضاء 1 — مراقب الحسابات', 'model': 'auditor_id.name'}, 56: {'label': 'إمضاء 2 — رئيس الحسابات', 'model': 'accounts_head_id.name'}, 57: {'label': 'حساب البنك', 'model': 'bank_account_no'}, 58: {'label': 'بتاريخ', 'model': 'date_received'}, 59: {'label': 'إمضاء 3 — رئيس المصلحة', 'model': 'section_head_id.name'}, 60: {'label': 'تاريخ الشتمذ ج', 'model': 'date_received'}, 61: {'label': 'قيد في سجل رقم 55', 'model': 'sequence_number'}, 62: {'label': 'روجع في — سنة', 'model': 'fiscal_year'}, 63: {'label': 'روجع في — تاريخ', 'model': 'reviewer_stamp_date'}, 64: {'label': 'شيك — اسم المستفيد', 'model': 'vendor_id.name'}, 65: {'label': 'يعتمد سحب — مبلغ', 'model': 'amount_net'}, 66: {'label': 'إذن صرف — وكيل الحسابات', 'model': 'reviewer_id.name'}, 67: {'label': 'مدير / رئيس الحسابات', 'model': 'accounts_head_id.name'}, 68: {'label': 'في سنة (صرف)', 'model': 'fiscal_year'}, 69: {'label': 'بمبلغ (رقم)', 'model': 'amount_net'}, 70: {'label': 'تاريخ الشتمذ د', 'model': 'date_received'}, 71: {'label': 'رقم القيد في دفتر 224', 'model': 'daftar224_sequence'}, 72: {'label': 'إمضاء الكاتب المنوط', 'model': 'writer_assigned'}, 73: {'label': 'إمضاء موظفي الشطب', 'model': 'crossout_signed_by'}, 74: {'label': 'رقم أمر الدفع', 'model': 'payment_order_ref'}, 75: {'label': 'سحب / شيك — اسم', 'model': 'vendor_id.name'}}

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


def _build_amiri_css():
    """
    يقرأ ملفات خط Amiri ويُرجع CSS يحتوي على @font-face مُضمَّنة بترميز base64.
    إذا لم تُوجد الملفات يُرجع سلسلة فارغة.
    """
    import base64, os
    candidates = [
        '/usr/share/fonts/opentype/fonts-hosny-amiri',
        '/usr/share/fonts/truetype/fonts-hosny-amiri',
        '/usr/share/fonts/amiri',
        '/usr/local/share/fonts/amiri',
    ]
    font_dir = next((d for d in candidates if os.path.isdir(d)), None)
    if not font_dir:
        # بحث عام عن الملف
        import glob
        results = glob.glob('/usr/share/fonts/**/Amiri-Regular.ttf', recursive=True)
        if results:
            font_dir = os.path.dirname(results[0])
    if not font_dir:
        return ''
    r_path = os.path.join(font_dir, 'Amiri-Regular.ttf')
    b_path = os.path.join(font_dir, 'Amiri-Bold.ttf')
    if not os.path.exists(r_path):
        return ''
    with open(r_path, 'rb') as f:
        r_b64 = base64.b64encode(f.read()).decode()
    b_b64 = r_b64  # fallback: use regular as bold if bold not found
    if os.path.exists(b_path):
        with open(b_path, 'rb') as f:
            b_b64 = base64.b64encode(f.read()).decode()
    return (
        "@font-face{font-family:'Amiri';"
        "src:url('data:font/truetype;base64," + r_b64 + "')format('truetype');"
        "font-weight:normal;font-style:normal;}"
        "@font-face{font-family:'Amiri';"
        "src:url('data:font/truetype;base64," + b_b64 + "')format('truetype');"
        "font-weight:bold;font-style:normal;}"
        # تجاوز Lato الذي تُحقنه Odoo بخط Amiri
        "@font-face{font-family:'Lato';"
        "src:url('data:font/truetype;base64," + r_b64 + "')format('truetype');}"
        "html,body{direction:rtl!important;}"
        "html *{font-family:'Amiri',serif!important;}"
    )


_AMIRI_CSS_CACHE = None


def post_migrate(env):
    """تأكد من إيقاف attachment_use بعد كل upgrade."""
    env['ir.actions.report'].sudo().search([
        ('report_name', 'like', 'form50'),
    ]).write({'attachment_use': False, 'attachment': ''})
