# -*- coding: utf-8 -*-
import re
from difflib import SequenceMatcher
from datetime import timedelta
from odoo import api, fields, models, _


class PortSaidDuplicateClaimEngine(models.TransientModel):
    _name = 'port_said.duplicate.claim.engine'
    _description = 'محرك كشف تكرار المستندات والمطالبات'

    @api.model
    def _param_float(self, key, default):
        try:
            return float(self.env['ir.config_parameter'].sudo().get_param(key, default))
        except Exception:
            return float(default)

    @api.model
    def _param_int(self, key, default):
        try:
            return int(float(self.env['ir.config_parameter'].sudo().get_param(key, default)))
        except Exception:
            return int(default)

    def action_run_full_scan(self):
        count = self.sudo().cron_daily_duplicate_claim_scan()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تشغيل فحص تكرار المستندات والمطالبات'),
                'message': _('تم إنشاء/تحديث %s تنبيه تكرار.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_daily_duplicate_claim_scan(self):
        count = 0
        scan_days = self._param_int('port_said_duplicate_claim.scan_days', 90)
        dt_from = fields.Datetime.now() - timedelta(days=scan_days)

        attachments = self.env['ir.attachment'].sudo().search([
            ('create_date', '>=', dt_from),
            ('checksum', '!=', False),
            ('res_model', 'in', ['port_said.dossier', 'port_said.daftar55', 'account.move', 'purchase.order']),
        ])
        for att in attachments:
            count += self.scan_attachment(att)

        if 'port_said.daftar55' in self.env:
            records = self.env['port_said.daftar55'].sudo().search([])
            for rec in records:
                count += self.scan_claim_record(rec)

        moves = self.env['account.move'].sudo().search([
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '!=', 'cancel'),
            ('create_date', '>=', dt_from),
        ])
        for move in moves:
            count += self.scan_claim_record(move)

        return count

    @api.model
    def scan_attachment(self, attachment):
        if not attachment or attachment._name != 'ir.attachment':
            return 0
        if not attachment.checksum:
            return 0
        if attachment.res_model not in ['port_said.dossier', 'port_said.daftar55', 'account.move', 'purchase.order']:
            return 0

        duplicates = self.env['ir.attachment'].sudo().search([
            ('checksum', '=', attachment.checksum),
            ('id', '!=', attachment.id),
            ('res_model', '!=', False),
        ], limit=20)

        count = 0
        for dup in duplicates:
            if dup.res_model == attachment.res_model and dup.res_id == attachment.res_id:
                continue
            count += self._create_attachment_alert(attachment, dup, 'same_file', 100.0)

        # Filename fuzzy similarity only for same business object area
        similar = self.env['ir.attachment'].sudo().search([
            ('id', '!=', attachment.id),
            ('res_model', 'in', ['port_said.dossier', 'port_said.daftar55', 'account.move', 'purchase.order']),
            ('create_date', '>=', fields.Datetime.now() - timedelta(days=self._param_int('port_said_duplicate_claim.scan_days', 90))),
        ], limit=200)

        for other in similar:
            if not attachment.name or not other.name:
                continue
            ratio = self._similarity(attachment.name, other.name)
            if ratio >= self._param_float('port_said_duplicate_claim.filename_similarity_threshold', 85):
                count += self._create_attachment_alert(attachment, other, 'similar_filename', ratio)

        return count

    @api.model
    def scan_claim_record(self, record):
        if not record:
            return 0

        if record._name == 'port_said.daftar55':
            return self._scan_daftar55(record)
        if record._name == 'account.move':
            return self._scan_account_move(record)
        return 0

    def _scan_daftar55(self, rec):
        if 'port_said.daftar55' not in self.env:
            return 0

        partner = self._partner(rec)
        amount = self._amount(rec)
        inv_no = self._invoice_number(rec)
        rec_date = self._record_date(rec)

        if not partner and not amount and not inv_no:
            return 0

        Model = self.env['port_said.daftar55'].sudo()
        domain = [('id', '!=', rec.id)]
        if partner:
            # Try partner fields dynamically.
            partner_domain = []
            for fname in ['partner_id', 'beneficiary_id', 'vendor_id']:
                if fname in Model._fields:
                    partner_domain = ['|'] + partner_domain + [(fname, '=', partner.id)] if partner_domain else [(fname, '=', partner.id)]
            if partner_domain:
                domain += partner_domain

        count = 0
        candidates = Model.search(domain, limit=200)

        for other in candidates:
            other_amount = self._amount(other)
            other_inv = self._invoice_number(other)
            other_date = self._record_date(other)

            if inv_no and other_inv and self._clean(inv_no) == self._clean(other_inv):
                count += self._create_record_alert(rec, other, 'same_invoice', 98.0, partner, inv_no, rec_date, amount, 'نفس رقم الفاتورة/المرجع لنفس المورد أو مطالبة مشابهة في دفتر 55.')
                continue

            if amount and other_amount and abs(amount - other_amount) <= self._param_float('port_said_duplicate_claim.amount_tolerance', 1):
                if rec_date and other_date and abs((rec_date - other_date).days) <= self._param_int('port_said_duplicate_claim.date_tolerance_days', 3):
                    count += self._create_record_alert(rec, other, 'duplicate_daftar55_claim', 90.0, partner, inv_no, rec_date, amount, 'مطالبة صرف في دفتر 55 بنفس القيمة ونفس التاريخ تقريبًا.')
                elif self._similarity(self._record_number(rec), self._record_number(other)) >= 80:
                    count += self._create_record_alert(rec, other, 'same_amount_date', 80.0, partner, inv_no, rec_date, amount, 'مطالبة صرف مشابهة من حيث المبلغ والمرجع.')

        return count

    def _scan_account_move(self, move):
        if move.move_type not in ['in_invoice', 'in_refund'] or move.state == 'cancel':
            return 0

        partner = move.partner_id
        amount = abs(move.amount_total or 0.0)
        inv_no = move.ref or move.name
        rec_date = move.invoice_date or move.date

        if not partner or not amount:
            return 0

        domain = [
            ('id', '!=', move.id),
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '!=', 'cancel'),
        ]
        candidates = self.env['account.move'].sudo().search(domain, limit=200)

        count = 0
        for other in candidates:
            other_amount = abs(other.amount_total or 0.0)
            other_ref = other.ref or other.name
            other_date = other.invoice_date or other.date

            if inv_no and other_ref and self._clean(inv_no) == self._clean(other_ref):
                count += self._create_record_alert(move, other, 'duplicate_account_bill', 98.0, partner, inv_no, rec_date, amount, 'فاتورة مورد مكررة بنفس رقم الفاتورة/المرجع.')
                continue

            if abs(amount - other_amount) <= self._param_float('port_said_duplicate_claim.amount_tolerance', 1):
                if rec_date and other_date and abs((rec_date - other_date).days) <= self._param_int('port_said_duplicate_claim.date_tolerance_days', 3):
                    count += self._create_record_alert(move, other, 'same_amount_date', 88.0, partner, inv_no, rec_date, amount, 'فاتورة/مطالبة بنفس المورد ونفس القيمة ونفس التاريخ تقريبًا.')

        return count

    def _create_attachment_alert(self, att, dup, alert_type, similarity):
        partner = False
        amount = 0.0
        inv_no = ''
        claim_date = False

        source_rec = self._safe_record(att.res_model, att.res_id)
        if source_rec:
            partner = self._partner(source_rec)
            amount = self._amount(source_rec)
            inv_no = self._invoice_number(source_rec)
            claim_date = self._record_date(source_rec)

        reason = 'تم رصد مستند مكرر بنفس بصمة الملف checksum.' if alert_type == 'same_file' else 'تم رصد تشابه كبير في اسم الملف مع مستند آخر.'

        return self._create_or_update_alert(
            alert_type=alert_type,
            similarity_score=similarity,
            source_model=att.res_model,
            source_res_id=att.res_id,
            source_display_name=self._display(att.res_model, att.res_id),
            duplicate_model=dup.res_model,
            duplicate_res_id=dup.res_id,
            duplicate_display_name=self._display(dup.res_model, dup.res_id),
            original_attachment_id=att.id,
            duplicate_attachment_id=dup.id,
            checksum=att.checksum,
            partner=partner,
            invoice_number=inv_no,
            claim_date=claim_date,
            amount=amount,
            difference_amount=0.0,
            reason=reason,
        )

    def _create_record_alert(self, rec, other, alert_type, similarity, partner, inv_no, claim_date, amount, reason):
        diff = abs((amount or 0.0) - (self._amount(other) or 0.0))
        return self._create_or_update_alert(
            alert_type=alert_type,
            similarity_score=similarity,
            source_model=rec._name,
            source_res_id=rec.id,
            source_display_name=rec.display_name,
            duplicate_model=other._name,
            duplicate_res_id=other.id,
            duplicate_display_name=other.display_name,
            original_attachment_id=False,
            duplicate_attachment_id=False,
            checksum='',
            partner=partner,
            invoice_number=inv_no,
            claim_date=claim_date,
            amount=amount,
            difference_amount=diff,
            reason=reason,
        )

    def _create_or_update_alert(self, alert_type, similarity_score, source_model, source_res_id, source_display_name,
                                duplicate_model, duplicate_res_id, duplicate_display_name, original_attachment_id,
                                duplicate_attachment_id, checksum, partner, invoice_number, claim_date, amount,
                                difference_amount, reason):
        Alert = self.env['port_said.duplicate.claim.alert'].sudo()

        vals = {
            'alert_type': alert_type,
            'similarity_score': similarity_score,
            'risk_level': self._risk(alert_type, similarity_score, amount),
            'source_model': source_model,
            'source_res_id': source_res_id or 0,
            'source_display_name': source_display_name or '',
            'duplicate_model': duplicate_model,
            'duplicate_res_id': duplicate_res_id or 0,
            'duplicate_display_name': duplicate_display_name or '',
            'original_attachment_id': original_attachment_id or False,
            'duplicate_attachment_id': duplicate_attachment_id or False,
            'checksum': checksum or '',
            'partner_id': partner.id if partner else False,
            'invoice_number': invoice_number or '',
            'claim_date': claim_date,
            'amount': amount or 0.0,
            'difference_amount': difference_amount or 0.0,
            'reason': reason,
            'recommendation': self._recommendation(alert_type),
        }

        domain = [
            ('alert_type', '=', alert_type),
            ('source_model', '=', source_model),
            ('source_res_id', '=', source_res_id or 0),
            ('duplicate_model', '=', duplicate_model),
            ('duplicate_res_id', '=', duplicate_res_id or 0),
            ('original_attachment_id', '=', original_attachment_id or False),
            ('duplicate_attachment_id', '=', duplicate_attachment_id or False),
        ]

        existing = Alert.search(domain, limit=1)
        if existing:
            existing.write(vals)
            return 0

        Alert.create(vals)
        return 1

    def _risk(self, alert_type, similarity, amount):
        if alert_type in ['same_file', 'same_invoice', 'duplicate_account_bill'] and similarity >= 95:
            return 'critical'
        if alert_type == 'duplicate_daftar55_claim':
            return 'critical' if amount and amount >= 10000 else 'high'
        if similarity >= 90:
            return 'high'
        if similarity >= 80:
            return 'medium'
        return 'low'

    def _recommendation(self, alert_type):
        if alert_type == 'same_file':
            return 'إيقاف الصرف مؤقتًا ومراجعة المستند الأصلي والمكرر قبل اعتماد العملية.'
        if alert_type in ['same_invoice', 'duplicate_account_bill', 'duplicate_daftar55_claim']:
            return 'مراجعة المطالبة مع الحسابات والمراجعة الداخلية للتحقق من عدم وجود صرف مزدوج.'
        if alert_type in ['same_amount_date', 'similar_filename']:
            return 'مراجعة التشابه يدويًا وربط المستندات بالسجلات الصحيحة قبل الاستكمال.'
        return 'مراجعة التكرار المحتمل واتخاذ الإجراء الرقابي المناسب.'

    def _safe_record(self, model, res_id):
        try:
            if model and res_id and model in self.env:
                rec = self.env[model].sudo().browse(res_id)
                return rec if rec.exists() else False
        except Exception:
            return False
        return False

    def _display(self, model, res_id):
        rec = self._safe_record(model, res_id)
        return rec.display_name if rec else '%s,%s' % (model or '', res_id or '')

    def _partner(self, rec):
        if not rec:
            return False
        for fname in ['partner_id', 'vendor_id', 'supplier_id', 'beneficiary_id']:
            if fname in rec._fields and rec[fname] and rec[fname]._name == 'res.partner':
                return rec[fname]
        return False

    def _amount(self, rec):
        for fname in ['amount_gross', 'amount_total', 'total_amount', 'amount', 'net_amount']:
            if fname in rec._fields:
                try:
                    return float(rec[fname] or 0.0)
                except Exception:
                    return 0.0
        return 0.0

    def _invoice_number(self, rec):
        for fname in ['invoice_number', 'invoice_no', 'vendor_bill_no', 'supplier_invoice_number', 'ref', 'reference', 'name', 'number']:
            if fname in rec._fields and rec[fname]:
                return str(rec[fname])
        return ''

    def _record_date(self, rec):
        for fname in ['invoice_date', 'date', 'date_received', 'posting_date', 'create_date']:
            if fname in rec._fields and rec[fname]:
                return fields.Date.to_date(rec[fname])
        return False

    def _record_number(self, rec):
        for fname in ['name', 'number', 'ref', 'reference', 'invoice_number', 'invoice_no']:
            if fname in rec._fields and rec[fname]:
                return str(rec[fname])
        return str(rec.id)

    def _clean(self, text):
        return re.sub(r'[^0-9a-zA-Zأ-ي]+', '', (text or '').lower())

    def _similarity(self, a, b):
        return SequenceMatcher(None, self._clean(a), self._clean(b)).ratio() * 100.0
