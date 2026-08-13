# -*- coding: utf-8 -*-
import math
import statistics
from datetime import date, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentAnomalyLog(models.Model):
    _name = 'port_said.payment.anomaly.log'
    _description = 'سجل وكيل كشف شذوذ المدفوعات والشيكات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(string='رقم التحليل', default='New', readonly=True, copy=False)
    transaction_model = fields.Char(string='موديل المعاملة', index=True)
    transaction_res_id = fields.Integer(string='رقم المعاملة', index=True)
    transaction_display_name = fields.Char(string='المعاملة')
    transaction_type = fields.Selection([
        ('cheque', 'شيك'),
        ('payment_order', 'أمر دفع وارد'),
        ('outgoing_po', 'أمر دفع صادر'),
        ('advance', 'سلفة'),
        ('manual', 'فحص يدوي'),
    ], string='نوع المعاملة', default='manual', index=True)

    partner_id = fields.Many2one('res.partner', string='المورد / المستفيد')
    partner_name = fields.Char(string='اسم الطرف')
    amount = fields.Float(string='المبلغ')
    transaction_date = fields.Date(string='تاريخ المعاملة')
    state = fields.Char(string='الحالة وقت الفحص')

    is_flagged = fields.Boolean(string='يوجد شذوذ', index=True)
    risk_level = fields.Selection([
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
        ('critical', 'حرج'),
    ], string='مستوى الخطر', default='low', index=True)
    risk_score = fields.Float(string='درجة الخطر')
    z_score = fields.Float(string='Z-Score')
    historical_count = fields.Integer(string='عدد المعاملات التاريخية')
    historical_mean = fields.Float(string='متوسط تاريخي')
    historical_stdev = fields.Float(string='انحراف معياري')
    anomaly_codes = fields.Char(string='أكواد الشذوذ')
    explanation_ar = fields.Text(string='تفسير الوكيل')
    recommended_action_ar = fields.Text(string='الإجراء المقترح')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    def action_open_transaction(self):
        self.ensure_one()
        if not self.transaction_model or not self.transaction_res_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': self.transaction_display_name or self.transaction_model,
            'res_model': self.transaction_model,
            'res_id': self.transaction_res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_mark_reviewed(self):
        for rec in self:
            rec.message_post(body=_('تمت مراجعة تحليل الشذوذ بواسطة: %s') % self.env.user.display_name)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = seq.next_by_code('port_said.payment.anomaly.log') or 'New'
        return super().create(vals_list)

    @api.model
    def action_run_full_scan(self):
        created = 0
        models_to_scan = [
            'port_said.cheque',
            'port_said.payment_order',
            'port_said.outgoing_po',
            'port_said.advance',
        ]
        for model_name in models_to_scan:
            model = self.env.get(model_name)
            if not model:
                continue
            records = model.search([], limit=500, order='id desc')
            for rec in records:
                if hasattr(rec, '_run_payment_anomaly_detection'):
                    rec._run_payment_anomaly_detection()
                    created += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('اكتمل الفحص'),
                'message': _('تم تشغيل فحص الشذوذ على %s معاملة حديثة.') % created,
                'type': 'success',
                'sticky': False,
            }
        }


class PaymentAnomalyMixin(models.AbstractModel):
    _name = 'port_said.payment.anomaly.mixin'
    _description = 'Payment anomaly detection mixin'

    risk_flag = fields.Boolean(string='مؤشر خطر', copy=False, index=True)
    risk_score = fields.Float(string='درجة الخطر', copy=False)
    risk_level = fields.Selection([
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
        ('critical', 'حرج'),
    ], string='مستوى الخطر', default='low', copy=False)
    risk_note = fields.Text(string='ملاحظات وكيل الشذوذ', copy=False)
    anomaly_log_id = fields.Many2one('port_said.payment.anomaly.log', string='آخر تحليل شذوذ', copy=False)

    def action_run_payment_anomaly_detection(self):
        for rec in self:
            rec._run_payment_anomaly_detection(manual=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم الفحص'),
                'message': _('تم تشغيل وكيل كشف الشذوذ.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _param_bool(self, key, default=False):
        value = self.env['ir.config_parameter'].sudo().get_param(key, str(default))
        return str(value).lower() in ('1', 'true', 'yes', 'y')

    def _param_float(self, key, default=0.0):
        value = self.env['ir.config_parameter'].sudo().get_param(key, str(default))
        try:
            return float(value)
        except Exception:
            return default

    def _param_int(self, key, default=0):
        value = self.env['ir.config_parameter'].sudo().get_param(key, str(default))
        try:
            return int(float(value))
        except Exception:
            return default

    def _get_transaction_amount(self):
        self.ensure_one()
        return float(getattr(self, 'amount', 0.0) or 0.0)

    def _get_transaction_date(self):
        self.ensure_one()
        for fname in ('issue_date', 'received_date', 'registration_date', 'date', 'due_date', 'create_date'):
            if fname in self._fields and getattr(self, fname, False):
                val = getattr(self, fname)
                if hasattr(val, 'date'):
                    return val.date()
                return val
        return fields.Date.context_today(self)

    def _get_transaction_partner(self):
        self.ensure_one()
        for fname in ('partner_id', 'beneficiary_id', 'vendor_id', 'employee_id'):
            if fname in self._fields and getattr(self, fname, False):
                rec = getattr(self, fname)
                if fname == 'employee_id':
                    partner = getattr(getattr(rec, 'user_id', False), 'partner_id', False) or getattr(rec, 'address_home_id', False)
                    return partner if partner else False
                return rec
        return False

    def _get_transaction_partner_name(self):
        self.ensure_one()
        partner = self._get_transaction_partner()
        if partner:
            return partner.display_name
        for fname in ('issuing_entity_name', 'beneficiary_account', 'purpose', 'name', 'display_name'):
            if fname in self._fields and getattr(self, fname, False):
                return str(getattr(self, fname))
        return self.display_name

    def _get_transaction_type(self):
        model = self._name
        if model == 'port_said.cheque':
            return 'cheque'
        if model == 'port_said.payment_order':
            return 'payment_order'
        if model == 'port_said.outgoing_po':
            return 'outgoing_po'
        if model == 'port_said.advance':
            return 'advance'
        return 'manual'

    def _history_domain(self, since_date):
        self.ensure_one()
        domain = [('id', '!=', self.id)]
        if 'state' in self._fields:
            # Prefer final/posted states, but allow broader history if no final records exist.
            domain.append(('state', 'not in', ['draft', 'cancelled']))
        tx_date = self._get_transaction_date()
        date_field = 'issue_date' if 'issue_date' in self._fields else 'received_date' if 'received_date' in self._fields else 'due_date' if 'due_date' in self._fields else False
        if date_field:
            domain.append((date_field, '>=', since_date))
            domain.append((date_field, '<=', tx_date))
        partner = self._get_transaction_partner()
        if partner:
            partner_field = None
            for fname in ('partner_id', 'beneficiary_id', 'vendor_id', 'employee_id'):
                if fname in self._fields:
                    partner_field = fname
                    break
            if partner_field:
                domain.append((partner_field, '=', partner.id))
        else:
            pname = self._get_transaction_partner_name()
            if 'issuing_entity_name' in self._fields and pname:
                domain.append(('issuing_entity_name', '=', pname))
        return domain

    def _same_amount_domain(self, since_date):
        domain = self._history_domain(since_date)
        if 'amount' in self._fields:
            amount = self._get_transaction_amount()
            domain.append(('amount', '>=', amount - 0.01))
            domain.append(('amount', '<=', amount + 0.01))
        return domain

    def _is_weekend_or_holiday_like(self, tx_date):
        # Egypt/Gov practical weekend: Friday and Saturday.
        if not tx_date:
            return False
        return tx_date.weekday() in (4, 5)

    def _is_fiscal_year_end(self, tx_date, days_window):
        if not tx_date:
            return False
        # Egyptian public/government FY often ends Jun 30.
        fy_end = date(tx_date.year, 6, 30)
        return 0 <= (fy_end - tx_date).days <= days_window

    def _detect_payment_anomaly(self):
        self.ensure_one()
        enabled = self._param_bool('port_said_payment_anomaly_ai_agent.enabled', True)
        if not enabled:
            return False

        amount = self._get_transaction_amount()
        tx_date = self._get_transaction_date()
        partner = self._get_transaction_partner()
        partner_name = self._get_transaction_partner_name()
        z_threshold = self._param_float('port_said_payment_anomaly_ai_agent.zscore_threshold', 2.0)
        min_history = self._param_int('port_said_payment_anomaly_ai_agent.min_history', 5)
        duplicate_days = self._param_int('port_said_payment_anomaly_ai_agent.duplicate_days', 30)
        large_new_vendor_amount = self._param_float('port_said_payment_anomaly_ai_agent.large_new_vendor_amount', 100000.0)
        fy_end_days = self._param_int('port_said_payment_anomaly_ai_agent.fy_end_days', 30)

        codes = []
        notes = []
        risk_score = 0.0
        z_score = 0.0
        mean = 0.0
        stdev = 0.0

        since = tx_date - timedelta(days=365)
        history = self.search(self._history_domain(since), limit=200)
        amounts = [float(x.amount or 0.0) for x in history if 'amount' in x._fields and float(x.amount or 0.0) > 0]

        if len(amounts) >= min_history:
            mean = statistics.mean(amounts)
            stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0.0
            if stdev > 0:
                z_score = (amount - mean) / stdev
                if abs(z_score) > z_threshold:
                    codes.append('Z_SCORE')
                    risk_score += min(45.0, abs(z_score) * 15.0)
                    notes.append('المبلغ خارج البصمة التاريخية للطرف: Z-Score = %.2f، المتوسط %.2f، الانحراف %.2f.' % (z_score, mean, stdev))
        else:
            notes.append('التاريخ الإحصائي غير كافٍ للتحليل الكامل: %s معاملة فقط.' % len(amounts))

        duplicate_since = tx_date - timedelta(days=duplicate_days)
        duplicates = self.search_count(self._same_amount_domain(duplicate_since))
        if duplicates:
            codes.append('DUPLICATE_AMOUNT')
            risk_score += 25.0
            notes.append('تم العثور على %s معاملة بنفس المبلغ لنفس الطرف خلال %s يوم.' % (duplicates, duplicate_days))

        if self._is_weekend_or_holiday_like(tx_date):
            codes.append('WEEKEND_PAYMENT')
            risk_score += 15.0
            notes.append('المعاملة بتاريخ جمعة أو سبت، وهو نمط يحتاج مراجعة رقابية.')

        if self._is_fiscal_year_end(tx_date, fy_end_days):
            # Count near FY end for same party.
            fy_start = date(tx_date.year, 6, max(1, 30 - fy_end_days))
            fy_history = self.search_count(self._history_domain(fy_start))
            if fy_history >= 3:
                codes.append('FY_END_CLUSTER')
                risk_score += 20.0
                notes.append('يوجد تراكم معاملات لنفس الطرف قرب نهاية السنة المالية.')

        if len(amounts) < 2 and amount >= large_new_vendor_amount:
            codes.append('NEW_VENDOR_LARGE_AMOUNT')
            risk_score += 35.0
            notes.append('طرف جديد أو قليل التعاملات مع مبلغ كبير يتجاوز حد الرقابة.')

        if self._name == 'port_said.advance':
            due_date = getattr(self, 'due_date', False)
            state = getattr(self, 'state', '')
            amount_outstanding = float(getattr(self, 'amount_outstanding', 0.0) or 0.0)
            today = fields.Date.context_today(self)
            if due_date and due_date < today and state in ('disbursed',) and amount_outstanding > 0:
                codes.append('OVERDUE_ADVANCE')
                risk_score += 40.0
                notes.append('السلفة تجاوزت تاريخ الاستحقاق دون تسوية كاملة. الرصيد القائم %.2f.' % amount_outstanding)

        is_flagged = bool(codes)
        if risk_score >= 80:
            level = 'critical'
        elif risk_score >= 55:
            level = 'high'
        elif risk_score >= 25:
            level = 'medium'
        else:
            level = 'low'

        if not notes:
            notes.append('لم يتم اكتشاف شذوذ رقابي وفق القواعد الحالية.')

        recommended = 'مراجعة بواسطة المراجعة الداخلية قبل الاعتماد أو الصرف.' if is_flagged else 'لا يوجد إجراء رقابي إضافي مطلوب حالياً.'

        return {
            'transaction_model': self._name,
            'transaction_res_id': self.id,
            'transaction_display_name': self.display_name,
            'transaction_type': self._get_transaction_type(),
            'partner_id': partner.id if partner and partner._name == 'res.partner' else False,
            'partner_name': partner_name,
            'amount': amount,
            'transaction_date': tx_date,
            'state': getattr(self, 'state', False) or '',
            'is_flagged': is_flagged,
            'risk_level': level,
            'risk_score': risk_score,
            'z_score': z_score,
            'historical_count': len(amounts),
            'historical_mean': mean,
            'historical_stdev': stdev,
            'anomaly_codes': ','.join(codes),
            'explanation_ar': '\\n'.join(notes),
            'recommended_action_ar': recommended,
        }

    def _run_payment_anomaly_detection(self, manual=False):
        self.ensure_one()
        vals = self._detect_payment_anomaly()
        if not vals:
            return False

        # Avoid duplicate logs for the same transaction in automatic create, update the latest log.
        existing = self.env['port_said.payment.anomaly.log'].search([
            ('transaction_model', '=', self._name),
            ('transaction_res_id', '=', self.id),
        ], limit=1, order='id desc')

        if manual or not existing:
            log = self.env['port_said.payment.anomaly.log'].create(vals)
        else:
            existing.write(vals)
            log = existing

        self.write({
            'risk_flag': vals['is_flagged'],
            'risk_score': vals['risk_score'],
            'risk_level': vals['risk_level'],
            'risk_note': vals['explanation_ar'],
            'anomaly_log_id': log.id,
        })

        if vals['is_flagged']:
            body = '<b>⚠️ وكيل كشف الشذوذ:</b><br/>%s<br/><b>الإجراء المقترح:</b><br/>%s' % (
                vals['explanation_ar'].replace('\\n', '<br/>'),
                vals['recommended_action_ar'],
            )
            try:
                self.message_post(body=body)
            except Exception:
                pass

            block = self._param_bool('port_said_payment_anomaly_ai_agent.block_high_risk', False)
            if block and vals['risk_level'] in ('high', 'critical'):
                raise UserError(_('تم إيقاف المعاملة للمراجعة الرقابية بسبب شذوذ مرتفع.\\n%s') % vals['explanation_ar'])

        return log


class PortSaidCheque(models.Model):
    _name = 'port_said.cheque'
    _inherit = ['port_said.cheque', 'port_said.payment.anomaly.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._run_payment_anomaly_detection()
        return records


class PortSaidPaymentOrder(models.Model):
    _name = 'port_said.payment_order'
    _inherit = ['port_said.payment_order', 'port_said.payment.anomaly.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._run_payment_anomaly_detection()
        return records


class PortSaidOutgoingPO(models.Model):
    _name = 'port_said.outgoing_po'
    _inherit = ['port_said.outgoing_po', 'port_said.payment.anomaly.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._run_payment_anomaly_detection()
        return records


class PortSaidAdvance(models.Model):
    _name = 'port_said.advance'
    _inherit = ['port_said.advance', 'port_said.payment.anomaly.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._run_payment_anomaly_detection()
        return records

    def action_disburse(self):
        res = super().action_disburse()
        for rec in self:
            rec._run_payment_anomaly_detection()
        return res
