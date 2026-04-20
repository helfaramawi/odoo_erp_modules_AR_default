# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import requests
import json
import hashlib
import uuid
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class EtaInvoice(models.Model):
    """
    سجل الفواتير الإلكترونية ETA
    يتتبع حالة كل فاتورة مُرسَلة لمنظومة ETA
    SDK Reference: https://sdk.invoicing.eta.gov.eg/api/05-submit-documents/
    """
    _name = 'eta.invoice'
    _description = 'فاتورة إلكترونية ETA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'submission_ref'
    _order = 'submission_date desc'

    # ── الارتباط بالفاتورة ───────────────────────────────────────
    move_id = fields.Many2one(
        'account.move', string='الفاتورة المحاسبية',
        required=True, ondelete='cascade', index=True
    )
    company_id = fields.Many2one(
        related='move_id.company_id', store=True
    )

    # ── بيانات ETA ───────────────────────────────────────────────
    submission_ref = fields.Char(
        string='رقم التقديم', readonly=True,
        help='submissionId من ETA'
    )
    eta_uuid = fields.Char(
        string='ETA UUID', readonly=True,
        help='المعرف الفريد 64-حرف من ETA'
    )
    long_id = fields.Char(
        string='Long ID', readonly=True
    )
    internal_id = fields.Char(
        string='Internal ID',
        default=lambda self: str(uuid.uuid4()),
        readonly=True
    )
    hash_key = fields.Char(
        string='Hash', readonly=True,
        help='SHA256 hash للمستند'
    )

    # ── الحالة ───────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',     'مسودة'),
        ('submitted', 'مُرسَلة للـ ETA'),
        ('valid',     '✅ صالحة — معتمدة ETA'),
        ('invalid',   '❌ مرفوضة من ETA'),
        ('cancelled', 'ملغاة'),
    ], string='الحالة', default='draft', tracking=True)

    submission_date = fields.Datetime(
        string='تاريخ الإرسال', readonly=True
    )
    validation_date = fields.Datetime(
        string='تاريخ اعتماد ETA', readonly=True
    )

    # نوع الفاتورة وفق ETA SDK
    document_type = fields.Selection([
        ('I',  'فاتورة ضريبية — Invoice (I)'),
        ('C',  'إشعار دائن — Credit Note (C)'),
        ('D',  'إشعار مدين — Debit Note (D)'),
    ], string='نوع المستند ETA', required=True, default='I')
    document_type_version = fields.Char(
        default='1.0', string='إصدار النموذج'
    )

    # استجابة ETA
    eta_response_raw = fields.Text(
        string='استجابة ETA (JSON)', readonly=True
    )
    eta_error_message = fields.Text(
        string='رسالة الخطأ من ETA', readonly=True
    )
    eta_qr_code = fields.Char(
        string='QR Code', readonly=True
    )

    # ══════════════════════════════════════════════════════════════
    # BUILD DOCUMENT JSON — وفق ETA SDK v1.0
    # ══════════════════════════════════════════════════════════════
    def _build_eta_document(self):
        """بناء JSON المستند وفق مواصفات ETA SDK"""
        self.ensure_one()
        move = self.move_id
        company = move.company_id
        partner = move.partner_id

        # التحقق من البيانات الأساسية
        if not company.vat:
            raise ValidationError(_('يجب إدخال الرقم الضريبي للشركة أولاً'))
        if not partner.vat and not partner.l10n_eg_branch_identifier:
            raise ValidationError(_('يجب إدخال الرقم الضريبي للعميل / الرقم القومي'))

        lines = []
        for line in move.invoice_line_ids.filtered(lambda l: not l.display_type):
            tax_amount = sum(line.tax_ids.mapped('amount'))
            lines.append({
                'description': line.name or line.product_id.name or '',
                'itemType': 'GPC',
                'itemCode': line.product_id.l10n_eg_code if line.product_id else '10000000',
                'unitType': line.product_uom_id.name if line.product_uom_id else 'EA',
                'quantity': line.quantity,
                'internalCode': line.product_id.default_code or '',
                'salesTotal': round(line.price_subtotal, 5),
                'total': round(line.price_total, 5),
                'valueDifference': 0.0,
                'totalTaxableFees': 0.0,
                'netTotal': round(line.price_subtotal, 5),
                'itemsDiscount': 0.0,
                'unitValue': {
                    'currencySold': move.currency_id.name or 'EGP',
                    'amountEGP': round(line.price_unit, 5),
                    'amountSold': round(line.price_unit, 5),
                    'currencyExchangeRate': 1.0,
                },
                'discount': {
                    'rate': 0.0,
                    'amount': 0.0,
                },
                'taxableItems': [
                    {
                        'taxType': 'T1',
                        'amount': round(
                            line.price_subtotal * tax_amount / 100.0, 5
                        ),
                        'subType': 'V009',
                        'rate': tax_amount,
                    }
                ] if tax_amount else [],
            })

        doc = {
            'issuer': {
                'address': {
                    'branchID': company.l10n_eg_branch_identifier or '0',
                    'country': 'EG',
                    'governate': company.state_id.name if company.state_id else 'Port Said',
                    'regionCity': company.city or 'Port Said',
                    'street': company.street or '',
                    'buildingNumber': company.street2 or 'N/A',
                },
                'type': 'B',
                'id': company.vat.replace('-', '') if company.vat else '',
                'name': company.name,
            },
            'receiver': {
                'address': {
                    'country': partner.country_id.code or 'EG',
                    'governate': partner.state_id.name if partner.state_id else '',
                    'regionCity': partner.city or '',
                    'street': partner.street or '',
                    'buildingNumber': partner.street2 or 'N/A',
                },
                'type': 'B' if partner.vat else 'P',
                'id': partner.vat.replace('-', '') if partner.vat else (
                    partner.l10n_eg_branch_identifier or ''
                ),
                'name': partner.name,
            },
            'documentType': self.document_type,
            'documentTypeVersion': self.document_type_version,
            'dateTimeIssued': move.invoice_date.strftime('%Y-%m-%dT00:00:00Z') if move.invoice_date else datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'taxpayerActivityCode': (
                self.env['eta.config'].search([
                    ('company_id', '=', company.id)
                ], limit=1).activity_code or '9999'
            ),
            'internalID': self.internal_id,
            'purchaseOrderReference': move.ref or '',
            'purchaseOrderDescription': '',
            'salesOrderReference': '',
            'salesOrderDescription': '',
            'proformaInvoiceNumber': '',
            'payment': {
                'bankName': '',
                'bankAddress': '',
                'bankAccountNo': '',
                'bankAccountIBAN': '',
                'swiftCode': '',
                'terms': '',
            },
            'delivery': {
                'approach': '',
                'packaging': '',
                'dateValidity': '',
                'exportPort': '',
                'grossWeight': 0.0,
                'netWeight': 0.0,
                'terms': '',
            },
            'invoiceLines': lines,
            'totalDiscountAmount': round(move.invoice_cash_rounding_id and 0.0 or 0.0, 5),
            'totalSalesAmount': round(sum(l['salesTotal'] for l in lines), 5),
            'netAmount': round(move.amount_untaxed, 5),
            'taxTotals': [
                {
                    'taxType': 'T1',
                    'amount': round(move.amount_tax, 5),
                }
            ] if move.amount_tax else [],
            'totalAmount': round(move.amount_total, 5),
            'extraDiscountAmount': 0.0,
            'totalItemsDiscountAmount': 0.0,
        }
        return doc

    # ══════════════════════════════════════════════════════════════
    # SUBMIT TO ETA
    # ══════════════════════════════════════════════════════════════
    def action_submit(self):
        """إرسال الفاتورة إلى ETA"""
        self.ensure_one()
        if self.state not in ('draft', 'invalid'):
            raise UserError(_('يمكن الإرسال فقط من حالة مسودة أو مرفوضة'))

        config = self.env['eta.config'].search([
            ('company_id', '=', self.move_id.company_id.id)
        ], limit=1)
        if not config:
            raise UserError(_('لم يتم إعداد ETA لهذه الشركة. اذهب إلى: إعدادات ETA'))

        try:
            doc = self._build_eta_document()
            payload = {'documents': [doc]}

            resp = requests.post(
                config.base_url + '/api/v1/documentsubmissions',
                headers=config._get_headers(),
                json=payload,
                timeout=60,
            )
            response_json = resp.json()
            self.eta_response_raw = json.dumps(response_json, ensure_ascii=False, indent=2)

            if resp.status_code in (200, 202):
                submission_id = response_json.get('submissionId', '')
                accepted = response_json.get('acceptedDocuments', [])
                rejected = response_json.get('rejectedDocuments', [])

                if accepted:
                    doc_resp = accepted[0]
                    self.write({
                        'state':           'submitted',
                        'submission_ref':  submission_id,
                        'eta_uuid':        doc_resp.get('uuid', ''),
                        'long_id':         doc_resp.get('longId', ''),
                        'hash_key':        doc_resp.get('hashKey', ''),
                        'submission_date': fields.Datetime.now(),
                        'eta_error_message': False,
                    })
                    self.move_id.message_post(
                        body=_('✅ تم إرسال الفاتورة لـ ETA — UUID: %s') % doc_resp.get('uuid','')
                    )
                elif rejected:
                    err = rejected[0].get('error', {})
                    self.write({
                        'state': 'invalid',
                        'eta_error_message': json.dumps(err, ensure_ascii=False),
                        'submission_date': fields.Datetime.now(),
                    })
                    raise UserError(_(f'رفضت ETA الفاتورة: {json.dumps(err, ensure_ascii=False)}'))
            else:
                error_text = json.dumps(response_json, ensure_ascii=False)
                self.write({
                    'state': 'invalid',
                    'eta_error_message': error_text,
                })
                raise UserError(_(f'خطأ من ETA ({resp.status_code}): {error_text}'))

        except requests.exceptions.RequestException as e:
            self.write({'state': 'invalid', 'eta_error_message': str(e)})
            raise UserError(_(f'تعذر الاتصال بـ ETA: {str(e)}'))

    def action_get_status(self):
        """الاستعلام عن حالة الفاتورة من ETA"""
        self.ensure_one()
        if not self.eta_uuid:
            raise UserError(_('لا يوجد UUID — أرسل الفاتورة أولاً'))

        config = self.env['eta.config'].search([
            ('company_id', '=', self.move_id.company_id.id)
        ], limit=1)
        if not config:
            raise UserError(_('لم يتم إعداد ETA'))

        try:
            url = f"{config.base_url}/api/v1/documents/{self.eta_uuid}/details"
            resp = requests.get(url, headers=config._get_headers(), timeout=30)
            data = resp.json()
            self.eta_response_raw = json.dumps(data, ensure_ascii=False, indent=2)

            status = data.get('status', '').lower()
            if status in ('valid', 'submitted'):
                self.write({
                    'state': 'valid',
                    'validation_date': fields.Datetime.now(),
                    'eta_qr_code': data.get('publicUrl', ''),
                })
                self.move_id.message_post(body=_('✅ اعتمدت ETA الفاتورة'))
            elif status in ('invalid', 'rejected', 'cancelled'):
                self.state = 'invalid'

        except Exception as e:
            raise UserError(_(f'فشل الاستعلام من ETA: {str(e)}'))

    def action_cancel_at_eta(self):
        """إلغاء الفاتورة في منظومة ETA"""
        self.ensure_one()
        if not self.eta_uuid:
            raise UserError(_('لا يوجد UUID للإلغاء'))
        config = self.env['eta.config'].search([
            ('company_id', '=', self.move_id.company_id.id)
        ], limit=1)
        try:
            url = f"{config.base_url}/api/v1/documents/state/{self.eta_uuid}/state"
            resp = requests.put(url, headers=config._get_headers(),
                                json={'status': 'cancelled', 'reason': 'Cancelled by issuer'},
                                timeout=30)
            if resp.status_code in (200, 202):
                self.state = 'cancelled'
                self.move_id.message_post(body=_('تم إلغاء الفاتورة في منظومة ETA'))
        except Exception as e:
            raise UserError(_(f'فشل الإلغاء: {str(e)}'))
