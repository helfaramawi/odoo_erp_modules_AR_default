# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _


class PortSaidDaftar55AccountReconcileEngine(models.TransientModel):
    _name = 'port_said.daftar55.account.reconcile.engine'
    _description = 'محرك مطابقة دفتر 55 مع القيود المحاسبية'

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
        count = self.sudo().cron_daily_daftar55_reconcile_scan()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('تم تشغيل مطابقة دفتر 55'), 'message': _('تم إنشاء/تحديث %s تنبيه عدم مطابقة.') % count, 'type': 'success', 'sticky': False}
        }

    @api.model
    def cron_daily_daftar55_reconcile_scan(self):
        Model = self.env['port_said.daftar55'].sudo()
        domain = []
        if 'state' in Model._fields:
            domain.append(('state', 'in', ['posted', 'archived']))
        date_field = self._date_field(Model)
        if date_field:
            domain.append((date_field, '>=', fields.Date.today() - timedelta(days=self._param_int('port_said_daftar55_reconcile.scan_days', 60))))
        records = Model.search(domain)
        count = 0
        for rec in records:
            count += self.check_daftar55_record(rec)
        return count

    @api.model
    def check_daftar55_record(self, record):
        if not record or record._name != 'port_said.daftar55':
            return 0
        if 'state' in record._fields and record.state not in ['posted', 'archived']:
            return 0

        number = self._record_number(record)
        amount = self._record_amount(record)
        rec_date = self._record_date(record)
        budget_line = self._record_budget_line(record)
        beneficiary = self._record_beneficiary(record)
        moves = self._find_related_moves(record, number)
        created = 0

        if not moves:
            return self._create_or_update_alert(record, moves, 'missing_move', amount, number, rec_date, budget_line, beneficiary, amount, 'سجل دفتر 55 مرحل ولا يوجد قيد محاسبي منشور مرتبط به.')

        move_total_debit = sum(moves.mapped('line_ids.debit'))
        diff = abs((move_total_debit or 0.0) - (amount or 0.0))
        if diff > self._param_float('port_said_daftar55_reconcile.amount_tolerance', 1):
            created += self._create_or_update_alert(record, moves, 'amount_mismatch', amount, number, rec_date, budget_line, beneficiary, diff, 'يوجد فرق قيمة بين دفتر 55 والقيود المحاسبية. قيمة دفتر 55: %.2f، إجمالي مدين القيود: %.2f، الفرق: %.2f.' % (amount, move_total_debit, diff))

        if len(moves) > 1:
            created += self._create_or_update_alert(record, moves, 'duplicate_moves', amount, number, rec_date, budget_line, beneficiary, 0.0, 'يوجد أكثر من قيد محاسبي منشور مرتبط بنفس سجل دفتر 55.')

        if rec_date:
            tolerance = self._param_int('port_said_daftar55_reconcile.date_tolerance_days', 7)
            bad = []
            for move in moves:
                if move.date:
                    delta = abs((move.date - rec_date).days)
                    if delta > tolerance:
                        bad.append('%s = %s يوم' % (move.name or move.ref or move.id, delta))
            if bad:
                created += self._create_or_update_alert(record, moves, 'date_mismatch', amount, number, rec_date, budget_line, beneficiary, 0.0, 'فرق تاريخ غير مبرر بين دفتر 55 والقيد. ' + ', '.join(bad[:5]))

        if budget_line and self._budget_mismatch(moves, budget_line):
            created += self._create_or_update_alert(record, moves, 'budget_line_mismatch', amount, number, rec_date, budget_line, beneficiary, 0.0, 'لم يتم العثور على بند الموازنة أو كود مشابه له داخل مرجع/وصف القيد أو سطور القيد.')

        return created

    def _find_related_moves(self, record, number):
        Move = self.env['account.move'].sudo()
        moves = Move.browse()
        if number:
            moves |= Move.search([('state', '=', 'posted'), '|', ('ref', 'ilike', number), ('name', 'ilike', number)])
            lines = self.env['account.move.line'].sudo().search([
                ('move_id.state', '=', 'posted'), '|', ('name', 'ilike', number), ('ref', 'ilike', number)
            ])
            moves |= lines.mapped('move_id')
        for fname in ['daftar55_id', 'port_said_daftar55_id']:
            if fname in Move._fields:
                moves |= Move.search([('state', '=', 'posted'), (fname, '=', record.id)])
        return moves

    def _record_number(self, rec):
        for fname in ['name', 'number', 'daftar55_no', 'sequence', 'reference']:
            if fname in rec._fields and rec[fname]:
                return str(rec[fname])
        return str(rec.id)

    def _record_amount(self, rec):
        for fname in ['amount_gross', 'amount_total', 'total_amount', 'amount', 'net_amount']:
            if fname in rec._fields:
                try:
                    return float(rec[fname] or 0.0)
                except Exception:
                    return 0.0
        return 0.0

    def _date_field(self, Model):
        for fname in ['date_received', 'date', 'posting_date', 'create_date']:
            if fname in Model._fields:
                return fname
        return False

    def _record_date(self, rec):
        for fname in ['date_received', 'date', 'posting_date']:
            if fname in rec._fields and rec[fname]:
                return fields.Date.to_date(rec[fname])
        return fields.Date.to_date(rec.create_date) if rec.create_date else False

    def _record_budget_line(self, rec):
        for fname in ['budget_line', 'budget_line_code', 'budget_position_id', 'budget_item_id']:
            if fname in rec._fields and rec[fname]:
                val = rec[fname]
                return val.display_name if hasattr(val, 'display_name') else str(val)
        return ''

    def _record_beneficiary(self, rec):
        for fname in ['partner_id', 'beneficiary_id', 'vendor_id', 'employee_id']:
            if fname in rec._fields and rec[fname]:
                return rec[fname].display_name
        for fname in ['beneficiary_name', 'payee_name', 'partner_name']:
            if fname in rec._fields and rec[fname]:
                return str(rec[fname])
        return ''

    def _budget_mismatch(self, moves, budget_line):
        text = (budget_line or '').strip()
        for move in moves:
            combined = ' '.join([
                move.ref or '', move.name or '',
                ' '.join(move.line_ids.mapped('name')),
                ' '.join(move.line_ids.mapped('ref')),
                ' '.join(move.line_ids.mapped('account_id.code')),
                ' '.join(move.line_ids.mapped('account_id.name')),
            ])
            if text and text in combined:
                return False
        return True

    def _recommendation(self, alert_type):
        return {
            'missing_move': 'مراجعة عملية الترحيل وإنشاء/إعادة إنشاء القيد المحاسبي المرتبط بسجل دفتر 55.',
            'amount_mismatch': 'مراجعة قيمة القيد المحاسبي وسطور المدين/الدائن ومقارنتها بإجمالي دفتر 55 قبل الإقفال.',
            'date_mismatch': 'مراجعة تاريخ الترحيل وتوثيق سبب فرق التاريخ أو تصحيح تاريخ القيد إذا كان خطأ.',
            'budget_line_mismatch': 'مراجعة الحساب أو مركز التكلفة أو بند الموازنة المستخدم في القيد المحاسبي.',
            'duplicate_moves': 'مراجعة القيود المرتبطة وإلغاء أو عكس القيد المكرر إن ثبت التكرار.',
        }.get(alert_type, 'مراجعة عدم المطابقة بواسطة الحسابات والمراجعة الداخلية.')

    def _risk_level(self, alert_type, difference_amount):
        if alert_type in ['missing_move', 'duplicate_moves']:
            return 'critical'
        if alert_type == 'amount_mismatch':
            return 'critical' if difference_amount >= 10000 else ('high' if difference_amount >= 1000 else 'medium')
        if alert_type in ['budget_line_mismatch', 'date_mismatch']:
            return 'high'
        return 'medium'

    def _create_or_update_alert(self, record, moves, alert_type, amount, number, rec_date, budget_line, beneficiary, difference_amount, reason):
        Alert = self.env['port_said.daftar55.account.reconcile.alert'].sudo()
        vals = {
            'daftar55_id': record.id,
            'daftar55_number': number,
            'daftar55_date': rec_date,
            'budget_line': budget_line,
            'beneficiary_name': beneficiary,
            'amount_gross': amount,
            'move_count': len(moves),
            'move_total_debit': sum(moves.mapped('line_ids.debit')) if moves else 0.0,
            'move_total_credit': sum(moves.mapped('line_ids.credit')) if moves else 0.0,
            'difference_amount': difference_amount,
            'alert_type': alert_type,
            'risk_level': self._risk_level(alert_type, difference_amount),
            'reason': reason,
            'recommendation': self._recommendation(alert_type),
        }
        existing = Alert.search([('daftar55_id', '=', record.id), ('alert_type', '=', alert_type)], limit=1)
        if existing:
            existing.write(vals)
            existing.move_ids = [(6, 0, moves.ids)]
            return 0
        alert = Alert.create(vals)
        alert.move_ids = [(6, 0, moves.ids)]
        return 1
