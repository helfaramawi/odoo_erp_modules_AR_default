# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EtaRetryLog(models.Model):
    _name = 'eta.retry.agent.log'
    _description = 'سجل وكيل ETA لإعادة المحاولة الذكية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(string='رقم السجل', default='New', readonly=True, copy=False)
    eta_invoice_id = fields.Many2one('eta.invoice', string='فاتورة ETA', index=True, ondelete='cascade')
    move_id = fields.Many2one('account.move', string='الفاتورة المحاسبية', related='eta_invoice_id.move_id', store=True)
    company_id = fields.Many2one('res.company', string='الشركة', related='eta_invoice_id.company_id', store=True)
    eta_uuid = fields.Char(string='ETA UUID')
    state_before = fields.Char(string='الحالة قبل الفحص')
    state_after = fields.Char(string='الحالة بعد الفحص')

    error_category = fields.Selection([
        ('data_error', 'خطأ بيانات'),
        ('network', 'خطأ شبكة / Timeout'),
        ('signature', 'خطأ توقيع رقمي'),
        ('eta_service', 'مشكلة من هيئة الضرائب'),
        ('auth', 'مشكلة صلاحية / Token'),
        ('unknown', 'غير معروف'),
    ], string='تصنيف الخطأ', default='unknown', index=True)

    technical_error = fields.Text(string='رسالة الخطأ التقنية')
    arabic_message = fields.Text(string='الشرح العربي للمحاسب')
    suggested_fix = fields.Text(string='التصحيح المقترح')
    affected_field = fields.Char(string='الحقل المقترح مراجعته')
    retry_performed = fields.Boolean(string='تمت إعادة المحاولة')
    retry_success = fields.Boolean(string='نجحت إعادة المحاولة')
    retry_attempt_no = fields.Integer(string='رقم محاولة الإعادة')
    next_retry_at = fields.Datetime(string='الموعد المقترح للمحاولة التالية')
    decision = fields.Selection([
        ('retry', 'إعادة محاولة'),
        ('needs_correction', 'يحتاج تصحيح بيانات'),
        ('signature_review', 'مراجعة التوقيع'),
        ('wait_eta', 'انتظار / متابعة ETA'),
        ('ignore', 'لا إجراء'),
    ], string='قرار الوكيل', default='ignore', index=True)
    notes = fields.Text(string='ملاحظات')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = seq.next_by_code('eta.retry.agent.log') or 'New'
        return super().create(vals_list)

    def action_open_eta_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.eta_invoice_id.display_name,
            'res_model': 'eta.invoice',
            'res_id': self.eta_invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class EtaInvoice(models.Model):
    _inherit = 'eta.invoice'

    state = fields.Selection(selection_add=[
        ('failed', 'فشل الإرسال'),
        ('needs_correction', 'يحتاج تصحيح بيانات'),
    ], ondelete={
        'failed': 'set default',
        'needs_correction': 'set default',
    })

    eta_error_arabic = fields.Text(string='شرح الخطأ بالعربي', readonly=True, copy=False)
    eta_error_category = fields.Selection([
        ('data_error', 'خطأ بيانات'),
        ('network', 'خطأ شبكة / Timeout'),
        ('signature', 'خطأ توقيع رقمي'),
        ('eta_service', 'مشكلة من هيئة الضرائب'),
        ('auth', 'مشكلة صلاحية / Token'),
        ('unknown', 'غير معروف'),
    ], string='تصنيف خطأ ETA', copy=False, readonly=True)
    eta_suggested_fix = fields.Text(string='التصحيح المقترح', readonly=True, copy=False)
    eta_affected_field = fields.Char(string='الحقل المطلوب مراجعته', readonly=True, copy=False)
    eta_retry_count = fields.Integer(string='عدد محاولات الإعادة', copy=False, readonly=True)
    eta_next_retry_at = fields.Datetime(string='موعد إعادة المحاولة التالية', copy=False, readonly=True)
    eta_last_retry_at = fields.Datetime(string='آخر محاولة إعادة', copy=False, readonly=True)
    eta_retry_blocked = fields.Boolean(string='إيقاف إعادة المحاولة', copy=False)
    eta_retry_log_ids = fields.One2many('eta.retry.agent.log', 'eta_invoice_id', string='سجل محاولات الوكيل')

    def _eta_retry_param_bool(self, key, default=False):
        value = self.env['ir.config_parameter'].sudo().get_param(key, str(default))
        return str(value).lower() in ('1', 'true', 'yes', 'y')

    def _eta_retry_param_int(self, key, default=0):
        value = self.env['ir.config_parameter'].sudo().get_param(key, str(default))
        try:
            return int(float(value))
        except Exception:
            return default

    def _eta_retry_error_text(self):
        self.ensure_one()
        return (self.eta_error_message or self.eta_response_raw or '').strip()

    def _classify_eta_error(self):
        """Rule-based local classifier. Can be replaced later by an on-prem LLM."""
        self.ensure_one()
        raw = self._eta_retry_error_text()
        txt = raw.lower()

        category = 'unknown'
        arabic = 'تعذر تصنيف الخطأ تلقائياً. برجاء مراجعة رسالة ETA الفنية.'
        fix = 'راجع الاستجابة الفنية في حقل استجابة ETA.'
        field = ''

        data_patterns = {
            'dt002': ('رقم التسجيل الضريبي غير صحيح أو غير مقبول من ETA.', 'partner_id.vat / company_id.vat'),
            'dt015': ('تنسيق التاريخ غير مدعوم أو تاريخ الإصدار غير صحيح.', 'invoice_date'),
            'taxpayer': ('بيانات الممول أو كود النشاط الضريبي تحتاج مراجعة.', 'activity_code / company.vat'),
            'issuer': ('بيانات المُصدر غير مكتملة أو غير صحيحة.', 'company_id'),
            'receiver': ('بيانات العميل / المستلم غير مكتملة أو غير صحيحة.', 'partner_id'),
            'itemcode': ('كود الصنف غير صحيح أو غير مسجل وفق منظومة ETA.', 'product_id.l10n_eg_code'),
            'item code': ('كود الصنف غير صحيح أو غير مسجل وفق منظومة ETA.', 'product_id.l10n_eg_code'),
            'unit': ('وحدة القياس غير مقبولة أو غير مطابقة لقوائم ETA.', 'product_uom_id'),
            'tax': ('بيانات الضريبة أو Tax Type/SubType تحتاج مراجعة.', 'tax_ids'),
            'invalid document': ('هيكل المستند أو بيانات الفاتورة غير مقبولة من ETA.', 'invoice fields'),
            'validation': ('خطأ تحقق من البيانات المرسلة إلى ETA.', 'invoice fields'),
        }

        for key, (msg, affected) in data_patterns.items():
            if key in txt:
                return {
                    'category': 'data_error',
                    'arabic': msg,
                    'fix': 'صحح الحقل المشار إليه ثم أعد إرسال الفاتورة.',
                    'field': affected,
                    'decision': 'needs_correction',
                }

        if any(k in txt for k in ['timeout', 'timed out', 'connection', 'network', 'temporarily unavailable', 'gateway', '502', '503', '504', 'net']):
            return {
                'category': 'network',
                'arabic': 'خطأ شبكة أو انتهاء مهلة الاتصال مع ETA. يمكن إعادة المحاولة تلقائياً.',
                'fix': 'لا يحتاج تعديل بيانات. سيحاول الوكيل إعادة الإرسال وفق جدول Backoff.',
                'field': '',
                'decision': 'retry',
            }

        if any(k in txt for k in ['signature', 'certificate', 'token signature', 'sig', 'signing']):
            return {
                'category': 'signature',
                'arabic': 'خطأ في التوقيع الرقمي أو الشهادة المستخدمة للإرسال.',
                'fix': 'راجع شهادة التوقيع الرقمي وإعدادات التوكن والتفويض.',
                'field': 'digital_certificate / token',
                'decision': 'signature_review',
            }

        if any(k in txt for k in ['unauthorized', 'forbidden', '401', '403', 'access token', 'client secret', 'client id', 'auth']):
            return {
                'category': 'auth',
                'arabic': 'مشكلة صلاحية أو Token أو بيانات Client ID/Secret.',
                'fix': 'راجع إعدادات ETA للشركة وجدد الـ Token.',
                'field': 'eta.config',
                'decision': 'signature_review',
            }

        if any(k in txt for k in ['eta service', 'service unavailable', 'internal server error', '500']):
            return {
                'category': 'eta_service',
                'arabic': 'يبدو أن المشكلة من خدمة ETA أو استجابة مؤقتة من هيئة الضرائب.',
                'fix': 'انتظر ثم أعد المحاولة لاحقاً. لا تعدل بيانات الفاتورة قبل التأكد.',
                'field': '',
                'decision': 'wait_eta',
            }

        return {
            'category': category,
            'arabic': arabic,
            'fix': fix,
            'field': field,
            'decision': 'ignore',
        }

    def _eta_next_retry_time(self):
        self.ensure_one()
        base_hours = self._eta_retry_param_int('port_said_eta_retry_ai_agent.backoff_base_hours', 2)
        retry_no = max(self.eta_retry_count or 0, 0)
        delay_hours = min(base_hours * (2 ** retry_no), 48)
        return fields.Datetime.now() + timedelta(hours=delay_hours)

    def action_eta_agent_analyze_error(self):
        for rec in self:
            rec._eta_agent_process_invoice(manual=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم التحليل'),
                'message': _('تم تحليل خطأ ETA وتحديث شرح الوكيل.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _eta_agent_process_invoice(self, manual=False):
        self.ensure_one()

        before_state = self.state
        result = self._classify_eta_error()
        max_attempts = self._eta_retry_param_int('port_said_eta_retry_ai_agent.max_attempts', 5)
        auto_retry = self._eta_retry_param_bool('port_said_eta_retry_ai_agent.auto_retry_network', True)

        retry_performed = False
        retry_success = False
        notes = []

        vals = {
            'eta_error_category': result['category'],
            'eta_error_arabic': result['arabic'],
            'eta_suggested_fix': result['fix'],
            'eta_affected_field': result['field'],
        }

        decision = result['decision']
        next_retry = False

        if result['category'] == 'network' and auto_retry and not self.eta_retry_blocked:
            if (self.eta_retry_count or 0) < max_attempts:
                if not self.eta_next_retry_at or fields.Datetime.now() >= self.eta_next_retry_at or manual:
                    retry_performed = True
                    try:
                        # Original action_submit accepts draft/invalid only.
                        if self.state not in ('draft', 'invalid'):
                            self.state = 'invalid'
                        self.action_submit()
                        retry_success = self.state in ('submitted', 'valid')
                        vals.update({
                            'eta_retry_count': (self.eta_retry_count or 0) + 1,
                            'eta_last_retry_at': fields.Datetime.now(),
                            'eta_next_retry_at': False if retry_success else self._eta_next_retry_time(),
                        })
                        notes.append('تمت إعادة المحاولة تلقائياً.')
                    except Exception as e:
                        vals.update({
                            'state': 'failed',
                            'eta_retry_count': (self.eta_retry_count or 0) + 1,
                            'eta_last_retry_at': fields.Datetime.now(),
                            'eta_next_retry_at': self._eta_next_retry_time(),
                            'eta_error_message': str(e),
                        })
                        notes.append('فشلت إعادة المحاولة: %s' % str(e))
                else:
                    next_retry = self.eta_next_retry_at
                    notes.append('لم يحن موعد إعادة المحاولة التالية بعد.')
            else:
                vals['eta_retry_blocked'] = True
                notes.append('تم بلوغ الحد الأقصى لمحاولات إعادة الإرسال.')
        elif result['category'] == 'data_error':
            vals['state'] = 'needs_correction'
            notes.append('تم تحويل الفاتورة إلى حالة تحتاج تصحيح بيانات.')
        elif result['category'] in ('signature', 'auth'):
            notes.append('تم توجيه الفاتورة لمراجعة إعدادات التوقيع/الصلاحيات.')
        elif result['category'] == 'eta_service':
            vals['eta_next_retry_at'] = self._eta_next_retry_time()
            next_retry = vals['eta_next_retry_at']
            notes.append('سيتم انتظار استقرار خدمة ETA قبل إعادة المحاولة.')
        else:
            notes.append('لا يوجد إجراء تلقائي آمن لهذه الرسالة.')

        self.write(vals)

        log = self.env['eta.retry.agent.log'].create({
            'eta_invoice_id': self.id,
            'eta_uuid': self.eta_uuid,
            'state_before': before_state,
            'state_after': self.state,
            'error_category': result['category'],
            'technical_error': self._eta_retry_error_text(),
            'arabic_message': result['arabic'],
            'suggested_fix': result['fix'],
            'affected_field': result['field'],
            'retry_performed': retry_performed,
            'retry_success': retry_success,
            'retry_attempt_no': self.eta_retry_count or 0,
            'next_retry_at': next_retry or self.eta_next_retry_at,
            'decision': decision,
            'notes': '\\n'.join(notes),
        })

        try:
            self.message_post(body='<b>🤖 وكيل ETA:</b><br/>%s<br/><b>التصحيح المقترح:</b><br/>%s' % (
                result['arabic'],
                result['fix'],
            ))
        except Exception:
            pass

        return log

    @api.model
    def _cron_eta_retry_agent(self):
        enabled = self.env['ir.config_parameter'].sudo().get_param('port_said_eta_retry_ai_agent.enabled', 'True')
        if str(enabled).lower() not in ('1', 'true', 'yes', 'y'):
            return True

        domain = [
            ('state', 'in', ['invalid', 'failed']),
            ('eta_retry_blocked', '=', False),
        ]
        invoices = self.search(domain, limit=200, order='submission_date asc, id asc')
        for inv in invoices:
            try:
                inv._eta_agent_process_invoice()
            except Exception as e:
                inv.message_post(body=_('فشل وكيل ETA أثناء المعالجة: %s') % str(e))
        return True

    @api.model
    def action_run_eta_retry_now(self):
        self._cron_eta_retry_agent()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم التشغيل'),
                'message': _('تم تشغيل وكيل ETA لإعادة المحاولة.'),
                'type': 'success',
                'sticky': False,
            }
        }
