# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import os
import requests
import json
import logging

_logger = logging.getLogger(__name__)

ETA_PROD_URL  = 'https://api.invoicing.eta.gov.eg'
ETA_PREPR_URL = 'https://api.preprod.invoicing.eta.gov.eg'
ETA_TOKEN_PATH = '/connect/token'
ETA_SUBMIT_PATH = '/api/v1/documentsubmissions'
ETA_DOC_PATH    = '/api/v1/documents/{uuid}/details'


class EtaConfig(models.Model):
    """
    إعدادات الفاتورة الإلكترونية ETA
    التكامل مع منظومة الفاتورة الإلكترونية — هيئة الضرائب المصرية
    SDK: https://sdk.invoicing.eta.gov.eg
    """
    _name = 'eta.config'
    _description = 'إعدادات ETA — الفاتورة الإلكترونية'
    _rec_name = 'company_id'

    company_id = fields.Many2one(
        'res.company', string='الشركة / الجهة',
        required=True, default=lambda s: s.env.company,
        ondelete='cascade'
    )
    environment = fields.Selection([
        ('preproduction', 'بيئة الاختبار (Pre-production)'),
        ('production',    'بيئة الإنتاج (Production)'),
    ], string='البيئة', required=True, default='preproduction',
       help='اختبر على Pre-production قبل الانتقال للإنتاج')

    # بيانات الاعتماد — ETA Portal → Representatives → Register ERP
    client_id = fields.Char(
        string='Client ID', required=True,
        help='يُستخرج من بوابة ETA: Taxpayer Profile → Representatives → Register ERP'
    )
    client_secret = fields.Char(
        string='Client Secret', required=True,
        help='احتفظ بهذه البيانات سرية — لا تشاركها'
    )

    # بيانات الشركة للـ ETA
    branch_id = fields.Char(
        string='Branch ID', default='0',
        help='استخدم 0 إذا كان فرع واحد فقط'
    )
    activity_code = fields.Char(
        string='ETA Activity Code',
        help='كود النشاط الاقتصادي من بوابة ETA'
    )

    # حالة الاتصال
    is_connected = fields.Boolean(string='متصل بـ ETA', default=False, readonly=True)
    last_token_date = fields.Datetime(string='آخر توكن', readonly=True)
    _token_cache = {}  # في الذاكرة فقط

    active = fields.Boolean(default=True)

    @property
    def base_url(self):
        return ETA_PROD_URL if self.environment == 'production' else ETA_PREPR_URL

    def _is_demo_environment(self):
        if os.environ.get('APP_ENV') == 'demo':
            return True
        try:
            return self.env['demo.branding'].sudo().is_demo_environment()
        except KeyError:
            # demo_branding not installed alongside this module - default safe
            return False

    def _get_access_token(self):
        """الحصول على OAuth2 token من ETA"""
        self.ensure_one()
        if self._is_demo_environment():
            # Demo Edition never calls the real Egyptian Tax Authority API,
            # in test (preproduction) or production mode.
            raise ValidationError(_(
                'تكامل ETA معطّل في بيئة العرض التجريبي — لا يتم الاتصال '
                'بأي خادم حقيقي لهيئة الضرائب المصرية. '
                '(ETA integration is simulated in the Demo Edition — no '
                'real Egyptian Tax Authority server is contacted.)'
            ))
        cache_key = f'{self.id}_{self.environment}'
        if cache_key in EtaConfig._token_cache:
            return EtaConfig._token_cache[cache_key]

        url = self.base_url + ETA_TOKEN_PATH
        try:
            resp = requests.post(url, data={
                'grant_type':    'client_credentials',
                'client_id':     self.client_id,
                'client_secret': self.client_secret,
                'scope':         'InvoicingAPI',
            }, timeout=30)
            resp.raise_for_status()
            token = resp.json().get('access_token', '')
            EtaConfig._token_cache[cache_key] = token
            self.write({'is_connected': True, 'last_token_date': fields.Datetime.now()})
            return token
        except Exception as e:
            self.write({'is_connected': False})
            raise ValidationError(_(f'فشل الاتصال بـ ETA: {str(e)}'))

    def action_test_connection(self):
        """اختبار الاتصال بـ ETA"""
        self.ensure_one()
        EtaConfig._token_cache.clear()
        token = self._get_access_token()
        if token:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('نجاح'),
                    'message': _('✅ تم الاتصال بـ ETA بنجاح'),
                    'type': 'success',
                }
            }

    def action_clear_token_cache(self):
        """مسح الـ token من الذاكرة (للتجديد)"""
        EtaConfig._token_cache.clear()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'تم', 'message': 'تم مسح الـ Token Cache', 'type': 'info'}
        }

    def _get_headers(self):
        token = self._get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept-Language': 'ar',
        }
