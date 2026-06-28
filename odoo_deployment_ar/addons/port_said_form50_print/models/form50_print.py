# -*- coding: utf-8 -*-
"""
port_said_form50_print — طبقة الطباعة الرسمية لاستمارة 50 ع.ح

يُوسِّع port_said.daftar55 بطبقة طباعة فقط.
لا يُعدِّل أي منطق محاسبي.
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from . import form50_layout as layout

_logger = logging.getLogger(__name__)



class IrActionsReportForm50Direct(models.Model):
    """Call wkhtmltopdf directly for form50 to control --encoding utf-8."""
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        if 'form50' in (report.report_name or ''):
            try:
                return self._form50_render_direct(report, res_ids, data)
            except Exception as e:
                _logger.error('Form50 direct render error: %s', e, exc_info=True)
        return super()._render_qweb_pdf(report_ref, res_ids, data)

    def _form50_render_direct(self, report, res_ids, data):
        import subprocess
        import tempfile
        import os
        from odoo.tools import find_in_path

        html_bytes, _ = self._render_qweb_html(report.report_name, res_ids, data=data)
        if not isinstance(html_bytes, bytes):
            html_bytes = html_bytes.encode('utf-8')

        import re as _re
        html_str = html_bytes.decode('utf-8', errors='replace')

        # Strip external Odoo CSS/JS assets — wkhtmltopdf can't auth to load them
        html_str = _re.sub(r'<link[^>]*>', '', html_str)
        html_str = _re.sub(r'<script[^>]*>.*?</script>', '', html_str, flags=_re.DOTALL)
        html_str = _re.sub(r'<script[^>]*/>', '', html_str)

        # Strip ALL embedded <style> blocks — Odoo injects margin rules via CSS classes
        # (e.g. .article { margin: 21mm; }) that cannot be overridden by !important
        # on individual properties. Removing every <style> block then injecting our
        # own reset is the only reliable way to get zero margins.
        html_str = _re.sub(r'<style\b[^>]*>.*?</style>', '', html_str, flags=_re.DOTALL)

        # Also strip margin/padding from any surviving inline style="..." attributes
        def _strip_margin_padding(m):
            s = m.group(1)
            s = _re.sub(r'\bmargin\s*:[^;]*;?\s*', '', s, flags=_re.I)
            s = _re.sub(r'\bpadding\s*:[^;]*;?\s*', '', s, flags=_re.I)
            return 'style="' + s.strip(' ;') + '"'

        html_str = _re.sub(r'style="([^"]*)"', _strip_margin_padding, html_str)

        # Inject our own CSS reset (only stylesheet in the document now)
        css_root_reset = (
            '<style type="text/css">'
            '@page{size:A4 portrait;margin:0!important;}'
            'html,body{margin:0!important;padding:0!important;width:210mm;height:297mm;}'
            '*{margin:0!important;padding:0!important;box-sizing:border-box;}'
            '</style>'
        )
        if '</head>' in html_str:
            html_str = html_str.replace('</head>', css_root_reset + '</head>', 1)
        else:
            html_str = css_root_reset + html_str

        # Replace HTTP URL for background image with local file:// path
        html_str = _re.sub(
            r'http://[^"\']+/port_said_form50_print/static/',
            'file:///mnt/extra-addons/port_said_form50_print/static/',
            html_str,
        )

        html_bytes = html_str.encode('utf-8')

        wk = find_in_path('wkhtmltopdf')

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as fh:
            fh.write(html_bytes)
            html_path = fh.name

        pdf_fd, pdf_path = tempfile.mkstemp(suffix='.pdf')
        os.close(pdf_fd)

        try:
            result = subprocess.run([
                wk,
                '--encoding', 'utf-8',
                '--page-size', 'A4',
                '--orientation', 'Portrait',
                '--margin-top', '0mm',
                '--margin-bottom', '0mm',
                '--margin-left', '0mm',
                '--margin-right', '0mm',
                '--disable-smart-shrinking',
                '--quiet',
                '--enable-local-file-access',
                html_path, pdf_path,
            ], capture_output=True)
            if result.returncode != 0:
                _logger.error('wkhtmltopdf stderr: %s', result.stderr.decode('utf-8', errors='replace'))
                _logger.error('wkhtmltopdf stdout: %s', result.stdout.decode('utf-8', errors='replace'))
                raise RuntimeError(f'wkhtmltopdf failed with code {result.returncode}')

            with open(pdf_path, 'rb') as f:
                return f.read(), 'pdf'
        finally:
            for p in (html_path, pdf_path):
                try:
                    os.unlink(p)
                except Exception:
                    pass

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
        """
        إرجاع مواضع الحقول كـ {id: (left%, top%)}.
        القيم مستوردة من form50_layout.py — المرجع الوحيد للإحداثيات.
        """
        self.ensure_one()
        return layout.get_all_positions()

    def _form50_positions_legacy(self):
        """نسخة احتياطية — للمرجع فقط، لا تُستخدم في الإنتاج."""
        self.ensure_one()
        return {
            # ── قسم أ — رقم مسلسل وتاريخ ────────────────────────────────────
            # blank y=9.29% x=58.5-84.4%: right-align seq (13ch*0.65=8.4%) → 84.4-8.4=76.0
            1:  (76.00,  9.29),  # رقم المسلسل  (v11: right-aligned in blank)
            2:  (85.74, 16.26),  # تاريخ الورود  (stamp circle, keep)

            # ── يسار — بيانات المصلحة والمستفيد ─────────────────────────────
            3:  (10.00,  9.20),  # مصلحة
            4:  (10.00, 10.95),  # قسم
            5:  (10.00, 12.71),  # المبلغ المستحق
            6:  (10.00, 16.19),  # بموجب
            7:  ( 0.50, 18.12),  # صار مراجعته
            8:  (10.00, 19.65),  # إذن صرف
            9:  (10.00, 21.30),  # شيك
            10: (10.00, 24.65),  # يسحب باسم
            11: (10.00, 28.13),  # ويرسل

            # ── جدول الفواتير (يمين الاستمارة) ──────────────────────────────
            # أعمدة محسوبة من separators بالصورة:
            #   رقم: بين x=986-1045px → center=1015px(81.9%)
            #   تاريخ: بين x=885-986px → center=936px(75.5%)
            #   جنيه: بين x=785-885px → center=835px(67.3%)
            #   قرش: بين x=726-785px  → center=755px(60.9%)
            # صفوف: H-lines عند y=245,305,360,421,482,517px
            #   R1: 245-305 → center=275px(15.7%)
            #   R2: 305-360 → center=332px(19.0%)
            #   R3: 360-421 → center=390px(22.3%)
            #   R4: 421-482 → center=451px(25.7%)
            #   جملة: 482-517 → center=499px(28.5%)
            12: (81.9, 15.7),  13: (72.8, 15.7),  14: (67.3, 15.7),  15: (60.9, 15.7),
            16: (81.9, 19.0),  17: (72.8, 19.0),  18: (67.3, 19.0),  19: (60.9, 19.0),
            20: (81.9, 22.3),  21: (72.8, 22.3),  22: (67.3, 22.3),  23: (60.9, 22.3),
            24: (81.9, 25.7),  25: (72.8, 25.7),  26: (67.3, 25.7),  27: (60.9, 25.7),
            28: (67.3, 28.5),  29: (60.9, 28.5),  # الجملة

            # ── قسم ب ─────────────────────────────────────────────────────────
            # pixel scan y=32.95-33.01% (px=578-579):
            #   clerk  x=17.66-30.00% (ctr=23.83%)
            #   reg    x=54.44-69.35% (ctr=62.0%) → right-align 9ch: 69.35-5.85=63.5
            #   date   x=69.52-79.35% (ctr=74.44%) → right-align 10ch: 79.35-6.5=72.85
            30: (26.5, 32.95),  # الكاتب المنوط  (v13: y=blank underline 32.95%)
            31: (63.5, 32.95),  # تقييد رقم (z)   (v13: right-align in 54.44-69.35%)
            32: (72.9, 32.95),  # التاريخ          (v13: right-align in 69.52-79.35%)

            # ── الاعتماد الإداري ──────────────────────────────────────────────
            # V-seps in admin section (y=673-843) from pixel analysis:
            #   separators at x=574(46.3%), 634(51.1%), 693(55.9%), 751(60.6%),
            #                 810(65.3%), 914(73.7%), 973(78.5%)
            #   Cell centers: 604(48.7%), 663(53.5%), 722(58.2%), 780(62.9%),
            #                 862(69.5%), 943(76.1%)
            #   RTL order (right→left): جنيه(76.1%), قرش(69.5%), قسم(62.9%),
            #                            فرع(58.2%), فصل(53.5%), بند(48.7%)
            # data row y=705-808px center=756px(43.1%) ≈ 43.2%
            # إجمالي الأصل: y=808-843px center=825px(47.1%)
            33: ( 7.7, 43.2),   # عدد المرفقات
            34: (48.7, 43.2),   # بند      (cell 1 center=604px)
            35: (53.5, 43.2),   # فصل      (cell 2 center=663px)
            36: (58.2, 43.2),   # فرع/نوع  (cell 3 center=722px)
            37: (62.9, 43.2),   # قسم/باب  (cell 4 center=780px)
            38: (76.1, 43.2),   # إجمالي — جنيه (cell 6 center=943px)
            39: (69.5, 43.2),   # إجمالي — قرش  (cell 5 center=862px)
            40: (76.1, 47.1),   # إجمالي الأصل — جنيه
            41: (69.5, 47.1),   # إجمالي الأصل — قرش

            # ── الاستقطاعات ───────────────────────────────────────────────────
            # Deduction table (y=843-1007) has 4 cells sharing admin col seps:
            #   Cell A: x=693-751, center=722px (58.2%) — header label "قرش"
            #   Cell B: x=751-810, center=780px (62.9%) — header label "جنيه"
            #   Cells C & D (x>810): empty in deduction rows
            # Header row (y=843-877) has column labels at cells A and B only
            # Row y-centers from left-side text analysis:
            #   عادية:       y=892-894 → center=893px (50.9%)
            #   إضافية:      y=916-919 → center=918px (52.3%)
            #   نسبية:       y=944-945 → center=944px (53.8%)
            #   رسم الدمغة: zone y=957-1007, label y=984-986 → center=985px (56.2%)
            42: (62.9, 50.9),   # دمغة عادية — جنيه   (cell B)
            43: (58.2, 50.9),   # دمغة عادية — قرش    (cell A)
            44: (62.9, 52.3),   # دمغة إضافية — جنيه
            45: (58.2, 52.3),   # دمغة إضافية — قرش
            46: (62.9, 53.8),   # دمغة نسبية — جنيه
            47: (58.2, 53.8),   # دمغة نسبية — قرش
            48: (76.1, 56.2),   # رسم الدمغة — جنيه  cell D (label text spans into A/B)
            49: (69.5, 56.2),   # رسم الدمغة — قرش  cell C

            # ── صافي القيمة والتفقيط ──────────────────────────────────────────
            # صافي zone y=1044-1067px center=1055px(60.1%)
            # use same cells C/D as admin monetary (label spans into A/B area)
            50: (76.1, 60.1),   # صافي — جنيه  cell D
            51: (69.5, 60.1),   # صافي — قرش   cell C
            52: (26.7, 60.5),   # التفقيط — underline at y=1067px(60.8%)

            # ── الإقرار ────────────────────────────────────────────────────────
            # pixel scan y=66.08% (px=1159): year x=31.77-45.89%(c=38.83%), date x=50.89-71.69%(c=61.29%)
            # right-align date 10ch in 50.89-71.69%: 71.69-6.5=65.19≈65.2
            53: (38.8, 66.08),  # في سنة         (v13: y=66.08% blank, x=38.83% center)
            54: (65.2, 66.08),  # تاريخ العلامة  (v13: right-align in 50.89-71.69%)

            # ── توقيعات قسم ج ─────────────────────────────────────────────────
            # pixel scan y=71.61% (px=1256): auditor x=4.76-20.65%(c=12.70%), bank x=38.47-60.16%(c=49.31%)
            # pixel scan y=73.03% (px=1281): x=18.87-22.58%(c=20.73%) ← رئيس المصلحة
            # pixel scan y=73.38% (px=1287): x=59.68-73.79%(c=66.73%) ← بتاريخ right-align 10ch: 73.79-6.5=67.3
            55: (12.7, 71.61),  # مراقب الحسابات  (v13: y=71.61% exact blank)
            56: (12.7, 73.03),  # رئيس الحسابات   (v13: y=73.03%)
            57: (49.4, 71.61),  # حساب البنك       (v13: y=71.61%, x=49.31% blank center)
            58: (67.3, 73.38),  # بتاريخ           (v13: y=73.38%, x right-align 73.79-6.5=67.3)
            59: (21.0, 73.03),  # رئيس المصلحة    (v13: y=73.03%, x=20.73%≈21.0%)
            60: (88.7, 73.03),  # الشتمذ ج         (v13: y=73.03%)

            # ── قسم ج — سجل 55 والاعتمادات ───────────────────────────────────
            # pixel scan y=76.80% (px=1347): x=43.79-55.48% (c=49.64%) ← field 61
            # pixel scan y=76.45-76.51%: x=55.97-61.77% ← small blanks for fields 62,63
            # pixel underline at y=1410px(80.4%): x=51-672(4.1-54.2%) center=29.1%
            # pixel underline at y=1427px(81.4%): x=49-367(4-29.6%) center=16.8%
            # pixel underlines at y=1439px(82.0%): 48.5%, 63.9%, 84.5%
            61: (47.0, 76.80),  # قيد في سجل رقم 55  (v13: y=76.80% exact blank)
            62: (21.9, 76.80),  # روجع في — سنة       (v13: y=76.80%)
            63: (56.7, 76.80),  # روجع في — تاريخ     (v13: y=76.80%)
            64: (29.1, 80.0),   # شيك — اسم المستفيد  underline center=29.1% @ y=80.4%
            65: (48.5, 81.8),   # يعتمد سحب           underline @ 48.5% y=82.0%
            66: (60.0, 81.8),   # وكيل الحسابات       (v9: -3.9 LTR name offset)
            67: (84.5, 81.8),   # رئيس الحسابات       underline @ 84.5% y=82.0%
            # ── قسم د — Row 1 (y=85.3%) ─────────────────────────────────────────
            # pixel scan confirmed 5 blanks at y=85.18-85.46%:
            #   x=3.7-21.2% (c=12.5%)  wide  → vendor name
            #   x=26.6-30.0% (c=28.3%) small → بمبلغ (amount)
            #   x=31.4-34.1% (c=32.7%) small → في سنة (year)
            #   x=35.0-47.4% (c=41.2%) med   → إمضاء الكاتب
            #   x=71.4-75.1% (c=73.2%) small → رقم القيد 224 (LTR, -3.7 for text width)
            68: (32.7, 85.3),   # في سنة (صرف)          blank c=32.7%  (v10: was 39.0 ← fixed)
            69: (28.3, 85.3),   # بمبلغ (رقم)            blank c=28.3%  (v10: was 24.4 ← fixed)

            # ── قسم د ─────────────────────────────────────────────────────────
            # Row 2 (y=86.9%): pixel scan blanks at x=60.2-64.3%(c=62.2%), 64.9-70.0%(c=67.5%), 92.8-95.7%(c=94.3%)
            # Row 3 (y=88.5%): blanks at 41.9-44.9%(c=43.4%), 50.6-53.4%(c=52.0%)
            70: (91.7, 86.9),   # تاريخ الشتمذ           stamp circle @ Row2 right
            71: (66.6, 85.18),  # رقم القيد دفتر 224    (v11: right-align 75.1-13*0.65=66.6)
            72: (41.2, 85.3),   # إمضاء الكاتب المنوط   blank c=41.2%  (v10: was 24.4 ← fixed)
            73: (62.2, 86.9),   # إمضاء موظفي الشطب     blank c=62.2%
            74: (65.0, 86.9),   # رقم أمر الدفع          blank left=64.9% (v10: was 64.0)
            75: (12.5, 85.3),   # سحب/شيك — اسم المستفيد wide blank c=12.5% (v10: was 39.0 ← fixed)
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
        from markupsafe import Markup

        def to_safe(text):
            return Markup(str(text))

        if not expr:
            return Markup('')

        m = re.match(r'^(?P<field>[\w_]+) \((?P<part>pounds|piasters)\)$', expr)
        if m:
            val = getattr(self, m.group('field'), 0) or 0
            pounds, piasters = self._get_amount_pounds_piasters(val)
            return to_safe(pounds if m.group('part') == 'pounds' else piasters)

        m = re.match(r"^_get_budget_parts\(\)\['(?P<key>\w+)'\]$", expr)
        if m:
            return to_safe((self._get_budget_parts() or {}).get(m.group('key'), '') or '')

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
                return Markup('')

        if hasattr(cur, 'name') and not isinstance(cur, (str, bytes)):
            try:
                return to_safe(cur.name or '')
            except Exception:
                pass
        if isinstance(cur, (date, datetime)):
            return to_safe(cur)
        return to_safe(cur or '')

    def _form50_field_text(self, field_no):
        self.ensure_one()
        expr = self._form50_field_models().get(field_no, {}).get('model', '')
        return self._form50_resolve_expr(expr)

    def _form50_render_fields(self):
        """
        إرجاع قائمة حقول جاهزة للعرض في الـQWeb template.
        إذا كان context يحتوي form50_calibration=True يُضاف overlay المعايرة.
        """
        self.ensure_one()
        calibration = self.env.context.get('form50_calibration', False)
        positions = self._form50_positions()
        right_align = {3,4,5,6,7,8,9,10,11,52,55,56,57,58,59,64,65,66,67,72,73,74,75}
        bold_fields = {1,5,14,18,22,26,28,29,38,39,40,41,50,51,65,69,71}
        small_fields = {12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,42,43,44,45,46,47,48,49}
        wide_fields  = {3,4,5,6,7,8,9,10,11,52,57,59,64,65,66,67,71,72,73,75}
        out = []
        for n in sorted(positions.keys(), key=lambda x: int(x)):
            x, y = positions[n]
            txt = self._form50_field_text(int(n))
            # وضع المعايرة: أظهر كل الحقول حتى الفارغة
            if not txt and not calibration:
                continue
            font_size  = 7.5 if n in small_fields else 9.0 if n in wide_fields else 8.0
            text_align = 'right' if n in right_align else 'center'
            font_weight = '700' if n in bold_fields else '400'
            max_width  = '70%' if n == 52 else ('34%' if n in wide_fields else '14%')
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
            entry = {'n': int(n), 'x': x, 'y': y, 'text': txt, 'style': style,
                     'calibration': calibration}
            if calibration:
                # نقطة المرجع ومعلومات الحقل
                cfg = layout.FIELD_POSITIONS.get(n, (x, y, 'A', ''))
                sec = cfg[2] if len(cfg) > 2 else 'A'
                lbl = cfg[3] if len(cfg) > 3 else str(n)
                dot_color = layout.SECTION_COLORS.get(sec, '#e53935')
                entry['calib_id'] = int(n)
                entry['calib_label'] = f"#{n} {lbl}"
                entry['calib_color'] = dot_color
                entry['calib_dot_style'] = (
                    f'position:absolute;left:{x}%;top:{y}%;'
                    f'width:5px;height:5px;border-radius:50%;'
                    f'background:{dot_color};z-index:20;'
                    'transform:translate(-50%,-50%);'
                )
                entry['calib_label_style'] = (
                    f'position:absolute;left:{x}%;top:{y}%;'
                    f'color:{dot_color};font-size:5pt;font-weight:bold;'
                    f'z-index:21;white-space:nowrap;'
                    'transform:translate(3px,-100%);'
                    'background:rgba(255,255,255,0.75);padding:0 1px;'
                    'font-family:monospace;'
                )
                entry['calib_box_style'] = (
                    f'position:absolute;left:{x}%;top:{y}%;'
                    f'border:1px solid {dot_color};z-index:19;'
                    f'max-width:{max_width};'
                    'transform:translateY(-50%);'
                    'min-width:20px;min-height:8pt;'
                    'background:rgba(255,255,255,0.25);'
                )
            out.append(entry)
        return out


def post_migrate(env):
    """تأكد من إيقاف attachment_use بعد كل upgrade."""
    env['ir.actions.report'].sudo().search([
        ('report_name', 'like', 'form50'),
    ]).write({'attachment_use': False, 'attachment': ''})
