# -*- coding: utf-8 -*-
"""
نموذج وثيقة قاعدة المعرفة — gov.kb.document
يخزن كل قطعة معرفة سواء من كود المصدر أو من الوثائق القانونية
"""
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class KBDocument(models.Model):
    _name = 'gov.kb.document'
    _description = 'وثيقة قاعدة المعرفة الحكومية'
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='اسم الوثيقة',
        required=True,
        help='مثال: قانون المشتريات الحكومية رقم 89 لسنة 1998'
    )
    source_type = fields.Selection(
        selection=[
            ('addon_source', 'كود المصدر'),
            ('legal_pdf', 'وثيقة قانونية PDF'),
            ('ministerial_decree', 'قرار وزاري'),
            ('procedure_manual', 'دليل إجراءات'),
            ('accounting_standard', 'معيار محاسبي'),
        ],
        string='نوع المصدر',
        required=True,
        default='legal_pdf',
        help='تصنيف مصدر هذه الوثيقة'
    )
    module_name = fields.Char(
        string='وحدة النظام',
        help='اسم وحدة Odoo المرتبطة (مثال: account, purchase, hr)',
        index=True,
    )
    model_name = fields.Char(
        string='اسم النموذج',
        help='مثال: account.move, purchase.order',
        index=True,
    )
    field_names = fields.Char(
        string='الحقول المرتبطة',
        help='أسماء الحقول مفصولة بفاصلة (مثال: invoice_date,partner_id)',
    )
    content = fields.Text(
        string='محتوى الوثيقة',
        help='النص المستخرج من المصدر',
    )
    embedding = fields.Text(
        string='المتجه الدلالي',
        help='مصفوفة JSON من float32 تمثل التضمين الدلالي للمحتوى',
    )
    law_number = fields.Char(
        string='رقم القانون / اللائحة',
        help='مثال: 89/1998 أو قرار وزاري 250/2019',
        index=True,
    )
    law_date = fields.Date(
        string='تاريخ الإصدار',
        help='تاريخ صدور القانون أو القرار',
    )
    authority = fields.Char(
        string='الجهة المصدِرة',
        help='مثال: وزارة المالية / الجهاز المركزي للمحاسبات',
        index=True,
    )
    active = fields.Boolean(
        string='نشط',
        default=True,
    )
    chunk_index = fields.Integer(
        string='رقم القطعة',
        default=0,
        help='رقم هذه القطعة داخل الوثيقة الأصلية (للوثائق الطويلة)',
    )
    source_file = fields.Char(
        string='ملف المصدر',
        help='المسار أو اسم الملف الأصلي',
    )
    pdf_file = fields.Binary(
        string='ملف PDF',
        attachment=True,
        help='ارفع ملف PDF للوثيقة القانونية هنا',
    )
    pdf_filename = fields.Char(string='اسم الملف')
    embedding_model = fields.Char(
        string='نموذج التضمين',
        default='paraphrase-multilingual-MiniLM-L12-v2',
        readonly=True,
    )
    tokens_count = fields.Integer(
        string='عدد الكلمات التقريبي',
        compute='_compute_tokens_count',
        store=True,
    )

    @api.depends('content')
    def _compute_tokens_count(self):
        for rec in self:
            if rec.content:
                # تقدير تقريبي: كل 4 أحرف = كلمة واحدة
                rec.tokens_count = len(rec.content) // 4
            else:
                rec.tokens_count = 0

    def action_index_now(self):
        """فهرسة هذه الوثيقة فوراً"""
        self.ensure_one()
        indexer = self.env['gov.kb.indexer']
        if self.pdf_file and self.source_type in ('legal_pdf', 'ministerial_decree'):
            import base64
            import tempfile
            import os
            # حفظ الملف مؤقتاً ثم فهرسته
            pdf_data = base64.b64decode(self.pdf_file)
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(pdf_data)
                tmp_path = f.name
            try:
                metadata = {
                    'name': self.name,
                    'law_number': self.law_number or '',
                    'law_date': str(self.law_date) if self.law_date else '',
                    'authority': self.authority or '',
                    'module_name': self.module_name or '',
                    'model_name': self.model_name or '',
                    'source_type': self.source_type,
                }
                indexer.index_legal_pdf(tmp_path, metadata)
            finally:
                os.unlink(tmp_path)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'تمت الفهرسة',
                'message': f'تمت فهرسة الوثيقة "{self.name}" بنجاح',
                'type': 'success',
            }
        }

    def action_reindex_all_addons(self):
        """إعادة فهرسة جميع الـ Addons المثبتة"""
        from odoo.modules.module import get_module_path
        indexer = self.env['gov.kb.indexer']
        installed_modules = self.env['ir.module.module'].search([
            ('state', '=', 'installed')
        ])
        count = 0
        for module in installed_modules:
            addon_path = get_module_path(module.name, raise_not_found=False)
            if addon_path:
                try:
                    indexer.index_addon_source(addon_path, module.name)
                    count += 1
                except Exception as e:
                    _logger.warning('فشل فهرسة %s: %s', module.name, e)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'إعادة الفهرسة',
                'message': f'تمت إعادة فهرسة {count} addon بنجاح',
                'type': 'success',
            }
        }
