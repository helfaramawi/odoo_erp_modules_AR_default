# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _


class PortSaidPaymentCycleEngine(models.TransientModel):
    _name = 'port_said.payment.cycle.engine'
    _description = 'محرك مراقبة تأخيرات دورة الصرف'

    @api.model
    def _param_int(self, key, default):
        try:
            return int(float(self.env['ir.config_parameter'].sudo().get_param(key, default)))
        except Exception:
            return int(default)

    @api.model
    def _stage_sla(self, stage):
        defaults = {
            'dossier_creation': 5,
            'dossier_completion': 5,
            'daftar55_approval': 3,
            'payment_order': 3,
            'cheque_issue': 5,
            'cheque_delivery': 7,
            'accounting_posting': 3,
            'general': 5,
        }
        return self._param_int('port_said_payment_cycle_delay.sla_%s' % stage, defaults.get(stage, 5))

    def action_run_full_scan(self):
        count = self.sudo().cron_daily_payment_cycle_delay_scan()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تشغيل فحص تأخيرات دورة الصرف'),
                'message': _('تم إنشاء/تحديث %s تنبيه تأخير.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_daily_payment_cycle_delay_scan(self):
        count = 0
        count += self._scan_dossiers()
        count += self._scan_daftar55()
        count += self._scan_cheques()
        count += self._scan_account_moves()
        return count

    def scan_record(self, record):
        if not record:
            return 0
        if record._name == 'port_said.dossier':
            return self._scan_single_dossier(record)
        if record._name == 'port_said.daftar55':
            return self._scan_single_daftar55(record)
        if record._name == 'port_said.cheque':
            return self._scan_single_cheque(record)
        if record._name == 'account.move':
            return self._scan_single_account_move(record)
        return 0

    def _scan_dossiers(self):
        if 'port_said.dossier' not in self.env:
            return 0
        Model = self.env['port_said.dossier'].sudo()
        records = Model.search([])
        count = 0
        for rec in records:
            count += self._scan_single_dossier(rec)
        return count

    def _scan_daftar55(self):
        if 'port_said.daftar55' not in self.env:
            return 0
        Model = self.env['port_said.daftar55'].sudo()
        records = Model.search([])
        count = 0
        for rec in records:
            count += self._scan_single_daftar55(rec)
        return count

    def _scan_cheques(self):
        if 'port_said.cheque' not in self.env:
            return 0
        Model = self.env['port_said.cheque'].sudo()
        records = Model.search([])
        count = 0
        for rec in records:
            count += self._scan_single_cheque(rec)
        return count

    def _scan_account_moves(self):
        Move = self.env['account.move'].sudo()
        date_from = fields.Date.today() - timedelta(days=self._param_int('port_said_payment_cycle_delay.scan_days', 60))
        moves = Move.search([('create_date', '>=', date_from), ('state', '=', 'draft')])
        count = 0
        for move in moves:
            count += self._scan_single_account_move(move)
        return count

    def _scan_single_dossier(self, rec):
        count = 0
        state = self._state(rec)
        create_dt = rec.create_date or fields.Datetime.now()
        complete = self._bool_field(rec, ['is_complete', 'complete', 'is_completed'])

        if state in ['waiting_documents', 'draft', 'open', 'in_progress'] and not complete:
            count += self._create_delay_if_exceeded(
                rec, 'dossier_completion', create_dt,
                'الإضبارة متوقفة أو غير مكتملة المستندات منذ أكثر من حد SLA.'
            )

        if complete and state not in ['approved', 'done', 'closed', 'archived']:
            complete_dt = self._date_field_value(rec, ['complete_date', 'completion_date', 'write_date']) or rec.write_date or create_dt
            count += self._create_delay_if_exceeded(
                rec, 'daftar55_approval', complete_dt,
                'الإضبارة مكتملة ولكن لم يتم اعتماد/استكمال مرحلة دفتر 55 في الوقت المحدد.'
            )

        return count

    def _scan_single_daftar55(self, rec):
        count = 0
        state = self._state(rec)
        start_dt = self._date_field_value(rec, ['date_received', 'date', 'create_date']) or rec.create_date or fields.Datetime.now()

        if state in ['draft', 'received', 'reviewed', 'cleared']:
            count += self._create_delay_if_exceeded(
                rec, 'daftar55_approval', start_dt,
                'سجل دفتر 55 لم يصل إلى الترحيل/الأرشفة خلال حد SLA.'
            )

        if state in ['posted', 'archived']:
            # Payment/cheque should follow posted Daftar55
            posted_dt = self._date_field_value(rec, ['posting_date', 'date_posted', 'write_date']) or rec.write_date or start_dt
            if not self._has_related_cheque_or_payment(rec):
                count += self._create_delay_if_exceeded(
                    rec, 'payment_order', posted_dt,
                    'دفتر 55 مرحل ولكن لم يتم العثور على أمر دفع أو شيك مرتبط خلال حد SLA.'
                )
        return count

    def _scan_single_cheque(self, rec):
        issue_dt = self._date_field_value(rec, ['issue_date', 'date_issue', 'date', 'create_date']) or rec.create_date
        delivery_dt = self._date_field_value(rec, ['delivery_date', 'date_delivery', 'received_date', 'paid_date'])
        state = self._state(rec)

        if issue_dt and not delivery_dt and state not in ['delivered', 'paid', 'done', 'closed', 'cancelled']:
            return self._create_delay_if_exceeded(
                rec, 'cheque_delivery', issue_dt,
                'الشيك صدر ولم يتم تسليمه/إغلاقه خلال حد SLA.'
            )
        return 0

    def _scan_single_account_move(self, rec):
        if rec.state == 'draft':
            start_dt = rec.create_date or fields.Datetime.now()
            return self._create_delay_if_exceeded(
                rec, 'accounting_posting', start_dt,
                'القيد المحاسبي ما زال مسودة ولم يتم ترحيله خلال حد SLA.'
            )
        return 0

    def _has_related_cheque_or_payment(self, daftar55):
        number = self._record_number(daftar55)
        if not number:
            return False

        # Cheques
        if 'port_said.cheque' in self.env:
            Cheque = self.env['port_said.cheque'].sudo()
            domain = []
            for fname in ['name', 'number', 'ref', 'reference', 'daftar55_number']:
                if fname in Cheque._fields:
                    domain = ['|'] + domain + [(fname, 'ilike', number)] if domain else [(fname, 'ilike', number)]
            for fname in ['daftar55_id', 'port_said_daftar55_id']:
                if fname in Cheque._fields:
                    domain = ['|'] + domain + [(fname, '=', daftar55.id)] if domain else [(fname, '=', daftar55.id)]
            if domain and Cheque.search_count(domain):
                return True

        # Payment orders if model exists
        if 'port_said.payment_order' in self.env:
            Pay = self.env['port_said.payment_order'].sudo()
            domain = []
            for fname in ['name', 'number', 'ref', 'reference', 'daftar55_number']:
                if fname in Pay._fields:
                    domain = ['|'] + domain + [(fname, 'ilike', number)] if domain else [(fname, 'ilike', number)]
            for fname in ['daftar55_id', 'port_said_daftar55_id']:
                if fname in Pay._fields:
                    domain = ['|'] + domain + [(fname, '=', daftar55.id)] if domain else [(fname, '=', daftar55.id)]
            if domain and Pay.search_count(domain):
                return True

        return False

    def _create_delay_if_exceeded(self, record, stage, start_dt, reason):
        if not start_dt:
            start_dt = fields.Datetime.now()

        start_dt = fields.Datetime.to_datetime(start_dt)
        now = fields.Datetime.now()
        sla_days = self._stage_sla(stage)
        delay_days = (now.date() - start_dt.date()).days

        if delay_days <= sla_days:
            return 0

        due_date = start_dt + timedelta(days=sla_days)
        return self._create_or_update_alert(
            record=record,
            stage=stage,
            start_dt=start_dt,
            due_date=due_date,
            delay_days=delay_days,
            sla_days=sla_days,
            reason=reason
        )

    def _create_or_update_alert(self, record, stage, start_dt, due_date, delay_days, sla_days, reason):
        Alert = self.env['port_said.payment.cycle.delay'].sudo()

        vals = {
            'source_model': record._name,
            'source_res_id': record.id,
            'source_display_name': record.display_name,
            'cycle_reference': self._record_number(record),
            'document_number': self._record_number(record),
            'beneficiary_name': self._beneficiary(record),
            'department_name': self._department(record),
            'amount': self._amount(record),
            'stage': stage,
            'current_state': self._state(record),
            'start_date': start_dt,
            'due_date': due_date,
            'delay_days': delay_days,
            'sla_days': sla_days,
            'risk_level': self._risk(delay_days, sla_days),
            'delay_reason': reason,
            'recommendation': self._recommendation(stage, delay_days),
        }

        existing = Alert.search([
            ('source_model', '=', record._name),
            ('source_res_id', '=', record.id),
            ('stage', '=', stage),
        ], limit=1)

        if existing:
            existing.write(vals)
            return 0

        Alert.create(vals)
        return 1

    def _risk(self, delay_days, sla_days):
        if delay_days >= sla_days * 4:
            return 'critical'
        if delay_days >= sla_days * 3:
            return 'high'
        if delay_days >= sla_days * 2:
            return 'medium'
        return 'low'

    def _recommendation(self, stage, delay_days):
        mapping = {
            'dossier_completion': 'مراجعة الإضبارة واستكمال المستندات الناقصة أو تصعيدها لمسؤول الملفات.',
            'daftar55_approval': 'مراجعة سبب توقف دفتر 55 وتحديد المسؤول عن مرحلة الاعتماد.',
            'payment_order': 'مراجعة الربط بين دفتر 55 وأمر الدفع/الشيك وإصدار مستند الدفع المطلوب.',
            'cheque_delivery': 'متابعة الشيك مع الخزينة وتوثيق التسليم أو سبب التعطيل.',
            'accounting_posting': 'مراجعة القيد المسودة وترحيله أو إلغاؤه قبل الإقفال.',
            'general': 'مراجعة مرحلة التعطل واتخاذ إجراء تصحيحي.',
        }
        return mapping.get(stage, 'مراجعة مرحلة التعطل واتخاذ إجراء تصحيحي.') + ' مدة التأخير الحالية: %s يوم.' % delay_days

    def _state(self, rec):
        return str(rec.state) if 'state' in rec._fields and rec.state else ''

    def _bool_field(self, rec, names):
        for fname in names:
            if fname in rec._fields:
                return bool(rec[fname])
        return False

    def _date_field_value(self, rec, names):
        for fname in names:
            if fname in rec._fields and rec[fname]:
                return rec[fname]
        return False

    def _record_number(self, rec):
        for fname in ['name', 'number', 'daftar55_no', 'sequence', 'reference', 'ref']:
            if fname in rec._fields and rec[fname]:
                return str(rec[fname])
        return '%s,%s' % (rec._name, rec.id)

    def _beneficiary(self, rec):
        for fname in ['partner_id', 'beneficiary_id', 'vendor_id', 'employee_id']:
            if fname in rec._fields and rec[fname]:
                return rec[fname].display_name
        for fname in ['beneficiary_name', 'payee_name', 'partner_name']:
            if fname in rec._fields and rec[fname]:
                return str(rec[fname])
        return ''

    def _department(self, rec):
        for fname in ['department_id', 'requesting_department_id', 'issuing_entity_id']:
            if fname in rec._fields and rec[fname]:
                return rec[fname].display_name
        for fname in ['department_name', 'issuing_entity_name']:
            if fname in rec._fields and rec[fname]:
                return str(rec[fname])
        return ''

    def _amount(self, rec):
        for fname in ['amount_gross', 'amount_total', 'total_amount', 'amount', 'net_amount']:
            if fname in rec._fields:
                try:
                    return float(rec[fname] or 0.0)
                except Exception:
                    return 0.0
        return 0.0
