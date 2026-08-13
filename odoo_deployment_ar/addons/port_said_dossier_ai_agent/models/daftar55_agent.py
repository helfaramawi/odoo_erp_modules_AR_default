# -*- coding: utf-8 -*-
import base64
import re
from dataclasses import dataclass

from odoo import fields, models, _
from odoo.exceptions import ValidationError


@dataclass
class AttachmentVerificationResult:
    is_matching: bool
    status: str
    discrepancy_note: str
    technical_details: str = ''
    attachment_ids: list = None


class PortSaidDaftar55DossierAgent(models.Model):
    _inherit = 'port_said.daftar55'

    def action_approve(self):
        """
        Agent integration point:
        يمنع اعتماد دفتر 55 قبل التأكد من اكتمال الإضبارة المرتبطة.
        ثم يقوم، عند التفعيل، بفحص محتوى المرفقات بشكل ذكي/قاعدي قبل السماح بالصرف.
        """
        for rec in self:
            rec._agent_validate_dossier_before_payment()
        return super().action_approve()

    def _agent_validate_dossier_before_payment(self):
        self.ensure_one()

        dossier = self._agent_get_dossier()
        if not dossier:
            self._agent_create_audit_log(
                dossier=False,
                result='skipped',
                is_complete=False,
                missing_attachments='لا توجد إضبارة مرتبطة بهذا السجل.',
                discrepancy_note='لم يتم تنفيذ فحص الإضبارة لعدم وجود إضبارة مرتبطة.',
            )
            return True

        is_complete = bool(getattr(dossier, 'is_complete', False))
        missing_attachments = self._agent_get_missing_attachments_text(dossier)

        if not is_complete:
            self._agent_create_audit_log(
                dossier=dossier,
                result='blocked_missing',
                is_complete=False,
                missing_attachments=missing_attachments,
                discrepancy_note='تم منع الاعتماد بسبب نقص مرفقات الإضبارة.',
            )
            raise ValidationError(_(
                'لا يمكن اعتماد الصرف من دفتر 55 لأن الإضبارة المرتبطة غير مكتملة.\n\n'
                'المرفقات الناقصة:\n%s\n\n'
                'برجاء استكمال المرفقات القانونية المطلوبة ثم إعادة المحاولة.'
            ) % (missing_attachments or 'غير محدد'))

        ai_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_dossier_ai_agent.ai_enabled', 'False'
        ) == 'True'
        ai_strict = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_dossier_ai_agent.ai_strict', 'False'
        ) == 'True'
        block_unreadable = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_dossier_ai_agent.block_unreadable', 'False'
        ) == 'True'

        verification = AttachmentVerificationResult(
            is_matching=True,
            status='not_configured',
            discrepancy_note='الفحص الذكي غير مفعّل من الإعدادات.',
            technical_details='',
            attachment_ids=[],
        )

        if ai_enabled:
            verification = self._agent_verify_dossier_attachments(dossier)

        result = 'passed'
        if ai_enabled and not verification.is_matching:
            result = 'blocked_ai' if ai_strict else 'warning'

        self._agent_create_audit_log(
            dossier=dossier,
            result=result,
            is_complete=True,
            missing_attachments='',
            ai_check_enabled=ai_enabled,
            ai_check_status=verification.status,
            discrepancy_note=verification.discrepancy_note,
            technical_details=verification.technical_details,
            attachment_ids=verification.attachment_ids or [],
        )

        if ai_enabled and not verification.is_matching and ai_strict:
            if verification.status == 'not_readable' and not block_unreadable:
                return True
            raise ValidationError(_(
                'لا يمكن اعتماد الصرف بسبب وجود عدم تطابق في محتوى مرفقات الإضبارة.\n\n%s'
            ) % verification.discrepancy_note)

        return True

    def _agent_get_dossier(self):
        self.ensure_one()

        if 'dossier_id' in self._fields and self.dossier_id:
            return self.dossier_id

        for field_name in ['file_id', 'dossier_file_id', 'payment_dossier_id']:
            if field_name in self._fields and self[field_name]:
                return self[field_name]

        return False

    def _agent_get_missing_attachments_text(self, dossier):
        if not dossier:
            return ''

        value = getattr(dossier, 'missing_attachments', False)
        if isinstance(value, str):
            return value

        if isinstance(value, (list, tuple)):
            return '\n'.join([str(x) for x in value])

        if value:
            try:
                return '\n'.join(value.mapped('name'))
            except Exception:
                return str(value)

        required = getattr(dossier, 'REQUIRED_ATTACHMENTS', [])
        if required:
            return '\n'.join([str(x) for x in required])

        return 'غير محدد'

    def _agent_verify_dossier_attachments(self, dossier):
        """
        Local/on-prem verification hook.
        لا يتم إرسال أي بيانات لخدمة خارجية.
        يحاول قراءة نص المرفقات إن كان متاحاً، ثم يطابق:
        - رقم أمر التوريد / المرجع
        - اسم المورد
        - المبلغ الإجمالي

        يمكن لاحقاً استبدال هذا الجزء بنداء Local LLM/OCR داخلي.
        """
        attachments = self._agent_get_dossier_attachments(dossier)
        if not attachments:
            return AttachmentVerificationResult(
                is_matching=False,
                status='not_readable',
                discrepancy_note='لم يتم العثور على مرفقات قابلة للفحص داخل الإضبارة.',
                technical_details='No attachments found for dossier.',
                attachment_ids=[],
            )

        extracted_texts = []
        unreadable = []
        for att in attachments:
            txt = self._agent_extract_attachment_text(att)
            if txt:
                extracted_texts.append(txt)
            else:
                unreadable.append(att.name)

        combined_text = '\n'.join(extracted_texts)
        if not combined_text.strip():
            return AttachmentVerificationResult(
                is_matching=False,
                status='not_readable',
                discrepancy_note='تعذر قراءة محتوى المرفقات. قد تكون المرفقات صوراً أو PDF ممسوح ضوئياً وتحتاج إلى OCR داخلي.',
                technical_details='Unreadable attachments: %s' % ', '.join(unreadable),
                attachment_ids=attachments.ids,
            )

        discrepancies = []

        expected_reference = self._agent_get_expected_reference()
        if expected_reference and expected_reference not in combined_text:
            discrepancies.append('رقم أمر التوريد/المرجع المتوقع (%s) غير موجود داخل نص المرفقات المقروءة.' % expected_reference)

        vendor_name = self._agent_get_vendor_name()
        if vendor_name and not self._agent_fuzzy_contains(combined_text, vendor_name):
            discrepancies.append('اسم المورد/المستفيد المتوقع (%s) غير ظاهر بوضوح داخل المرفقات.' % vendor_name)

        gross_amount = self._agent_get_amount_gross()
        if gross_amount:
            if not self._agent_amount_exists_in_text(combined_text, gross_amount):
                discrepancies.append('المبلغ الإجمالي المتوقع (%.2f) غير ظاهر بوضوح داخل المرفقات.' % gross_amount)

        if discrepancies:
            return AttachmentVerificationResult(
                is_matching=False,
                status='failed',
                discrepancy_note='\n'.join(discrepancies),
                technical_details='تمت قراءة النص من عدد %s مرفق. المرفقات غير المقروءة: %s' % (
                    len(extracted_texts),
                    ', '.join(unreadable) if unreadable else 'لا يوجد'
                ),
                attachment_ids=attachments.ids,
            )

        note = 'تمت مطابقة البيانات الأساسية المتاحة مع محتوى المرفقات المقروءة.'
        if unreadable:
            note += ' مع ملاحظة وجود مرفقات تعذر قراءتها: %s' % ', '.join(unreadable)

        return AttachmentVerificationResult(
            is_matching=True,
            status='passed' if not unreadable else 'warning',
            discrepancy_note=note,
            technical_details='Local text verification completed.',
            attachment_ids=attachments.ids,
        )

    def _agent_get_dossier_attachments(self, dossier):
        attachment_obj = self.env['ir.attachment'].sudo()
        attachments = attachment_obj.search([
            ('res_model', '=', dossier._name),
            ('res_id', '=', dossier.id),
        ])

        for field_name in ['attachment_ids', 'document_ids', 'invoice_attachment_ids']:
            if field_name in dossier._fields and dossier[field_name]:
                try:
                    attachments |= dossier[field_name]
                except Exception:
                    pass

        return attachments

    def _agent_extract_attachment_text(self, attachment):
        """
        Tries to extract text without requiring cloud services.
        Supports text files and PDFs if pdfminer.six is installed.
        For scanned PDFs/images, connect this method later to internal OCR/LLM.
        """
        try:
            raw = base64.b64decode(attachment.datas or b'')
        except Exception:
            return ''

        mimetype = attachment.mimetype or ''
        name = (attachment.name or '').lower()

        if mimetype.startswith('text/') or name.endswith(('.txt', '.csv', '.xml', '.html', '.htm')):
            return self._agent_decode_bytes(raw)

        if mimetype == 'application/pdf' or name.endswith('.pdf'):
            try:
                from pdfminer.high_level import extract_text
                import io
                return extract_text(io.BytesIO(raw)) or ''
            except Exception:
                return ''

        return self._agent_decode_bytes(raw)

    def _agent_decode_bytes(self, raw):
        for enc in ['utf-8', 'windows-1256', 'cp1256', 'latin-1']:
            try:
                return raw.decode(enc, errors='ignore')
            except Exception:
                continue
        return ''

    def _agent_get_expected_reference(self):
        self.ensure_one()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_dossier_ai_agent.reference_fields',
            'purchase_order_id,name,origin,reference,po_number,supply_order_no'
        )
        for field_name in [x.strip() for x in param.split(',') if x.strip()]:
            if field_name not in self._fields:
                continue
            val = self[field_name]
            if not val:
                continue
            if hasattr(val, 'display_name'):
                return val.display_name
            return str(val)
        return ''

    def _agent_get_vendor_name(self):
        self.ensure_one()
        for field_name in ['vendor_id', 'partner_id', 'supplier_id']:
            if field_name in self._fields and self[field_name]:
                return self[field_name].display_name
        return ''

    def _agent_get_amount_gross(self):
        self.ensure_one()
        for field_name in ['amount_gross', 'amount_total', 'total_amount', 'amount']:
            if field_name in self._fields and self[field_name]:
                try:
                    return float(self[field_name])
                except Exception:
                    return 0.0
        return 0.0

    def _agent_fuzzy_contains(self, text, phrase):
        if not text or not phrase:
            return False
        normalized_text = self._agent_normalize_text(text)
        normalized_phrase = self._agent_normalize_text(phrase)
        return normalized_phrase in normalized_text

    def _agent_normalize_text(self, text):
        text = str(text or '').lower()
        text = re.sub(r'[\s\u0640]+', ' ', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        return text.strip()

    def _agent_amount_exists_in_text(self, text, amount):
        if not text or not amount:
            return False

        candidates = {
            '%.2f' % amount,
            '%.0f' % amount,
            ('%,.2f' % amount),
            ('%,.0f' % amount),
        }
        clean_text = text.replace(',', '').replace('٬', '').replace('٫', '.')
        for candidate in candidates:
            if candidate.replace(',', '') in clean_text:
                return True
        return False

    def _agent_create_audit_log(
        self,
        dossier,
        result,
        is_complete=False,
        missing_attachments='',
        ai_check_enabled=False,
        ai_check_status='not_configured',
        discrepancy_note='',
        technical_details='',
        attachment_ids=None,
    ):
        self.ensure_one()
        vendor = False
        for field_name in ['vendor_id', 'partner_id', 'supplier_id']:
            if field_name in self._fields and self[field_name]:
                vendor = self[field_name]
                break

        vals = {
            'daftar55_id': self.id,
            'dossier_id': dossier.id if dossier else False,
            'vendor_id': vendor.id if vendor else False,
            'amount_gross': self._agent_get_amount_gross(),
            'reference': self._agent_get_expected_reference(),
            'is_complete': is_complete,
            'missing_attachments': missing_attachments or '',
            'result': result,
            'ai_check_enabled': ai_check_enabled,
            'ai_check_status': ai_check_status,
            'discrepancy_note': discrepancy_note or '',
            'technical_details': technical_details or '',
            'attachment_ids': [(6, 0, attachment_ids or [])],
        }
        log = self.env['port_said.dossier.audit.log'].sudo().create(vals)

        label = dict(log._fields['result'].selection).get(result, result)
        if hasattr(self, 'message_post'):
            self.message_post(body=_('تم تنفيذ فحص الإضبارة قبل الصرف. نتيجة الفحص: %s') % label)

        if dossier and hasattr(dossier, 'message_post'):
            dossier.message_post(body=_('تم تنفيذ فحص الإضبارة قبل الصرف من خلال دفتر 55. نتيجة الفحص: %s') % label)

        return log
