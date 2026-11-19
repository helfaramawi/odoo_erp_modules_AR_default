# -*- coding: utf-8 -*-
import re
from odoo import api, models, _
from odoo.exceptions import UserError


class PortSaidProcurementLegalEngine(models.TransientModel):
    _name = 'port_said.procurement.legal.engine'
    _description = 'محرك مراجعة الالتزام القانوني للمشتريات'

    REQUIRED_DOCS = {
        'tender': ['purchase_request', 'estimated_budget', 'committee_minutes', 'supplier_offers', 'terms_book', 'conflict_declaration', 'technical_report', 'financial_report', 'award_memo', 'authority_approval'],
        'practice': ['purchase_request', 'estimated_budget', 'committee_minutes', 'supplier_offers', 'conflict_declaration', 'technical_report', 'financial_report', 'award_memo', 'authority_approval'],
        'direct_order': ['purchase_request', 'justification', 'supplier_offer', 'authority_approval'],
        'simple_supply': ['purchase_request', 'supplier_offer', 'authority_approval'],
        'unknown': ['purchase_request', 'supplier_offer', 'authority_approval'],
    }

    CRITICAL_DOCS = {'purchase_request', 'authority_approval', 'award_memo', 'technical_report', 'financial_report', 'committee_minutes'}

    DOC_LABELS = {
        'purchase_request': 'طلب شراء معتمد',
        'estimated_budget': 'مذكرة تقديرية / مقايسة تقديرية',
        'committee_minutes': 'محضر لجنة',
        'supplier_offers': 'خطابات / عروض الموردين',
        'supplier_offer': 'عرض مورد',
        'terms_book': 'كراسة شروط',
        'conflict_declaration': 'إقرار تضارب مصالح',
        'technical_report': 'محضر / تقرير فني',
        'financial_report': 'محضر / تقرير مالي',
        'award_memo': 'مذكرة ترسية',
        'authority_approval': 'اعتماد السلطة المختصة',
        'justification': 'مذكرة تبرير الأمر المباشر',
    }

    KEYWORDS = {
        'purchase_request': ['طلب شراء', 'purchase request', 'requisition', 'احتياج', 'طلب توريد'],
        'estimated_budget': ['تقديرية', 'مقايسة', 'estimated', 'budget estimate', 'estimate', 'تكلفة تقديرية'],
        'committee_minutes': ['محضر لجنة', 'committee minutes', 'minutes', 'لجنة', 'محضر اجتماع'],
        'supplier_offers': ['عروض الموردين', 'supplier offers', 'offers', 'quotations', 'quotation', 'عرض سعر', 'عروض اسعار', 'عروض أسعار'],
        'supplier_offer': ['عرض مورد', 'supplier offer', 'quotation', 'عرض سعر', 'عرض أسعار'],
        'terms_book': ['كراسة شروط', 'terms book', 'tender document', 'specifications', 'الشروط والمواصفات'],
        'conflict_declaration': ['تضارب مصالح', 'conflict', 'declaration', 'إقرار عدم تعارض', 'عدم تعارض'],
        'technical_report': ['محضر فني', 'تقرير فني', 'technical report', 'technical', 'فني'],
        'financial_report': ['محضر مالي', 'تقرير مالي', 'financial report', 'financial', 'مالي'],
        'award_memo': ['ترسية', 'award memo', 'award', 'مذكرة ترسية', 'قرار ترسية'],
        'authority_approval': ['اعتماد السلطة', 'approval', 'approved', 'اعتماد', 'موافقة السلطة', 'موافقة'],
        'justification': ['تبرير', 'justification', 'justified', 'أمر مباشر', 'امر مباشر', 'سبب الاختيار'],
    }

    @api.model
    def _get_blocking_enabled(self):
        val = self.env['ir.config_parameter'].sudo().get_param('port_said_procurement_legal.block_po_confirmation', '1')
        return str(val).lower() in ['1', 'true', 'yes']

    @api.model
    def action_run_full_scan(self):
        count = self.sudo().cron_daily_procurement_legal_compliance_scan()
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('تم تشغيل فحص الالتزام القانوني للمشتريات'), 'message': _('تم إنشاء/تحديث %s مراجعة قانونية.') % count, 'type': 'success', 'sticky': False}}

    @api.model
    def cron_daily_procurement_legal_compliance_scan(self):
        count = 0
        for model_name in ['procurement.adjudication', 'procurement.committee', 'purchase.order', 'port_said.dossier']:
            if model_name not in self.env:
                continue
            for rec in self.env[model_name].sudo().search([], limit=500):
                count += self.check_procurement_record(rec, 'general')
        return count

    @api.model
    def check_procurement_record(self, record, stage='general'):
        if not record:
            return 0

        method = self._procurement_method(record)
        required = list(self.REQUIRED_DOCS.get(method, self.REQUIRED_DOCS['unknown']))
        attachments = self._collect_attachments(record)

        uploaded = set()
        unknown = []
        for att in attachments:
            doc_type = self._classify_attachment(att)
            if doc_type:
                uploaded.add(doc_type)
            else:
                unknown.append(att.name or str(att.id))

        missing = [doc for doc in required if doc not in uploaded]
        existing = [doc for doc in required if doc in uploaded]
        critical_missing = [doc for doc in missing if doc in self.CRITICAL_DOCS]

        score = (len(existing) / len(required) * 100.0) if required else 100.0

        if critical_missing:
            legal_status = 'blocked'
        elif missing:
            legal_status = 'incomplete'
        elif unknown:
            legal_status = 'needs_review'
        else:
            legal_status = 'complete'

        self._create_or_update_compliance(record, stage, method, score, legal_status, missing, existing, unknown, critical_missing, attachments)
        return 1

    @api.model
    def check_and_block_if_needed(self, record, stage='before_po'):
        self.check_procurement_record(record, stage)
        if not self._get_blocking_enabled():
            return True
        compliance = self.env['port_said.procurement.legal.compliance'].sudo().search([('source_model', '=', record._name), ('source_res_id', '=', record.id), ('stage', '=', stage)], limit=1)
        if compliance and compliance.legal_status == 'blocked':
            raise UserError(_('لا يمكن الانتقال للمرحلة التالية بسبب نقص جوهري في مستندات الشراء القانونية.\n\nنسبة الالتزام: %.2f%%\nالنواقص الجوهرية:\n%s') % (compliance.compliance_score, compliance.critical_missing_docs or compliance.missing_docs or ''))
        return True

    def _collect_attachments(self, record):
        Attachment = self.env['ir.attachment'].sudo()
        attachments = Attachment.search([('res_model', '=', record._name), ('res_id', '=', record.id)])
        for fname in ['dossier_id', 'procurement_id', 'adjudication_id', 'purchase_id', 'order_id']:
            if fname in record._fields and record[fname]:
                linked = record[fname]
                attachments |= Attachment.search([('res_model', '=', linked._name), ('res_id', '=', linked.id)])
        return attachments

    def _procurement_method(self, record):
        raw = ''
        for fname in ['method', 'procurement_method', 'purchase_method', 'tender_type', 'type']:
            if fname in record._fields and record[fname]:
                raw = str(record[fname]).lower()
                break
        if any(x in raw for x in ['tender', 'مناقصة']):
            return 'tender'
        if any(x in raw for x in ['practice', 'ممارسة']):
            return 'practice'
        if any(x in raw for x in ['direct', 'أمر مباشر', 'امر مباشر']):
            return 'direct_order'
        if any(x in raw for x in ['simple', 'توريد بسيط', 'supply']):
            return 'simple_supply'
        amount = self._amount(record)
        if amount and amount < 50000:
            return 'simple_supply'
        return 'unknown'

    def _classify_attachment(self, att):
        text = ' '.join([att.name or '', att.description or '', att.mimetype or '']).lower()
        text = re.sub(r'[_\-\.]+', ' ', text)
        for doc_type, keywords in self.KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    return doc_type
        return False

    def _amount(self, rec):
        for fname in ['amount_total', 'amount_gross', 'total_amount', 'estimated_amount', 'amount']:
            if fname in rec._fields:
                try:
                    return float(rec[fname] or 0.0)
                except Exception:
                    return 0.0
        return 0.0

    def _doc_names(self, docs):
        return '\n'.join(['- ' + self.DOC_LABELS.get(x, x) for x in docs]) if docs else 'لا يوجد'

    def _recommendation(self, legal_status, missing, critical_missing):
        if legal_status == 'complete':
            return 'ملف عملية الشراء مكتمل من ناحية قائمة الفحص القانونية الأساسية.'
        if critical_missing:
            return 'يوصى بإيقاف المرحلة التالية لحين استكمال النواقص الجوهرية: %s' % ', '.join([self.DOC_LABELS.get(x, x) for x in critical_missing])
        if missing:
            return 'يوصى باستكمال المستندات الناقصة قبل البت أو الترسية: %s' % ', '.join([self.DOC_LABELS.get(x, x) for x in missing])
        return 'يوصى بمراجعة المرفقات غير المصنفة يدويًا للتأكد من سلامة الملف.'

    def _official_note(self, record, method, stage, score, missing, existing, critical_missing):
        method_label = dict(self.env['port_said.procurement.legal.compliance']._fields['procurement_method'].selection).get(method, method)
        stage_label = dict(self.env['port_said.procurement.legal.compliance']._fields['stage'].selection).get(stage, stage)
        return """
        <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.8;">
            <h3>مذكرة مراجعة الالتزام القانوني لمستندات المشتريات</h3>
            <p><strong>السجل:</strong> %s</p>
            <p><strong>نوع العملية:</strong> %s</p>
            <p><strong>مرحلة المراجعة:</strong> %s</p>
            <p><strong>نسبة الالتزام:</strong> %.2f%%</p>
            <p><strong>المستندات الموجودة:</strong></p><pre>%s</pre>
            <p><strong>المستندات الناقصة:</strong></p><pre>%s</pre>
            <p><strong>النواقص الجوهرية:</strong></p><pre>%s</pre>
            <p><strong>تنبيه:</strong> هذه المراجعة آلية ولا تغني عن المراجعة القانونية النهائية بواسطة المختصين.</p>
        </div>
        """ % (record.display_name, method_label, stage_label, score, self._doc_names(existing), self._doc_names(missing), self._doc_names(critical_missing))

    def _create_or_update_compliance(self, record, stage, method, score, legal_status, missing, existing, unknown, critical_missing, attachments):
        Compliance = self.env['port_said.procurement.legal.compliance'].sudo()
        vals = {
            'source_model': record._name,
            'source_res_id': record.id,
            'source_display_name': record.display_name,
            'procurement_method': method,
            'stage': stage,
            'compliance_score': score,
            'legal_status': legal_status,
            'missing_docs': self._doc_names(missing),
            'existing_docs': self._doc_names(existing),
            'unknown_docs': '\n'.join(['- ' + x for x in unknown]) if unknown else 'لا يوجد',
            'critical_missing_docs': self._doc_names(critical_missing),
            'recommendation': self._recommendation(legal_status, missing, critical_missing),
            'official_note': self._official_note(record, method, stage, score, missing, existing, critical_missing),
        }
        existing_rec = Compliance.search([('source_model', '=', record._name), ('source_res_id', '=', record.id), ('stage', '=', stage)], limit=1)
        if existing_rec:
            existing_rec.write(vals)
            existing_rec.attachment_ids = [(6, 0, attachments.ids)]
            return existing_rec
        new_rec = Compliance.create(vals)
        new_rec.attachment_ids = [(6, 0, attachments.ids)]
        return new_rec
