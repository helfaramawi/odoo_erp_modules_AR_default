# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PortSaidInspectionCommitteePenaltyAgent(models.Model):
    _inherit = 'port_said.inspection.committee'

    agent_penalty_id = fields.Many2one('port_said.penalty', string='جزاء المورد الناتج من الوكيل', readonly=True, copy=False)
    agent_penalty_created = fields.Boolean(string='تم إنشاء جزاء بواسطة الوكيل', readonly=True, copy=False)
    agent_penalty_amount = fields.Float(string='قيمة الجزاء المحسوبة بواسطة الوكيل', readonly=True, copy=False)
    agent_penalty_rate = fields.Float(string='نسبة الجزاء بواسطة الوكيل', readonly=True, copy=False)
    agent_penalty_notification = fields.Text(string='إخطار المورد بالجزاء', readonly=True, copy=False)
    agent_penalty_last_check = fields.Datetime(string='آخر فحص بواسطة وكيل الجزاءات', readonly=True, copy=False)

    agent_penalty_log_ids = fields.One2many(
        'port_said.vendor.penalty.agent.log',
        'inspection_id',
        string='سجل وكيل الجزاءات',
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._agent_check_and_create_vendor_penalty(trigger='create')
        return records

    def write(self, vals):
        res = super().write(vals)
        trigger_fields = {'result', 'specs_conformity', 'quantity_rejected', 'quantity_received', 'quantity_accepted', 'purchase_order_id'}
        if trigger_fields.intersection(vals.keys()):
            for rec in self:
                rec._agent_check_and_create_vendor_penalty(trigger='write')
        return res

    def action_sign(self):
        res = super().action_sign()
        for rec in self:
            rec._agent_check_and_create_vendor_penalty(trigger='action_sign')
        return res

    def action_finalize_and_attach_to_dossier(self):
        res = super().action_finalize_and_attach_to_dossier()
        for rec in self:
            rec._agent_check_and_create_vendor_penalty(trigger='action_finalize_and_attach_to_dossier')
        return res

    def action_agent_run_penalty_now(self):
        for rec in self:
            rec._agent_check_and_create_vendor_penalty(trigger='manual')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('وكيل جزاءات الموردين'),
                'message': _('تم تنفيذ فحص الجزاءات لهذا المحضر.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _agent_is_enabled(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'port_said_vendor_penalty_ai_agent.enabled', 'True'
        ) == 'True'

    def _agent_check_and_create_vendor_penalty(self, trigger='write'):
        if not self._agent_is_enabled():
            return True

        for rec in self:
            rec.sudo().write({'agent_penalty_last_check': fields.Datetime.now()})

            if rec.agent_penalty_id:
                rec._agent_create_log(
                    decision='duplicate',
                    reason='يوجد جزاء مرتبط بالفعل بهذا المحضر، لذلك لم يتم إنشاء جزاء مكرر.',
                    trigger=trigger,
                    penalty=rec.agent_penalty_id,
                )
                continue

            if not rec._agent_requires_penalty():
                rec._agent_create_log(
                    decision='skipped',
                    reason='نتيجة الفحص لا تستدعي إنشاء جزاء تلقائي.',
                    trigger=trigger,
                )
                continue

            if not rec.purchase_order_id:
                rec._agent_create_log(
                    decision='skipped',
                    reason='لا يوجد أمر توريد مرتبط بمحضر الفحص.',
                    trigger=trigger,
                )
                continue

            vendor = rec.purchase_order_id.partner_id
            if not vendor:
                rec._agent_create_log(
                    decision='skipped',
                    reason='لا يوجد مورد مرتبط بأمر التوريد.',
                    trigger=trigger,
                )
                continue

            duplicate = rec._agent_find_duplicate_penalty(vendor)
            if duplicate:
                rec.sudo().write({
                    'agent_penalty_id': duplicate.id,
                    'agent_penalty_created': True,
                    'agent_penalty_amount': duplicate.amount if 'amount' in duplicate._fields else 0.0,
                })
                rec._agent_create_log(
                    decision='duplicate',
                    reason='تم العثور على جزاء سابق لنفس المورد ونفس محضر الفحص.',
                    trigger=trigger,
                    penalty=duplicate,
                )
                continue

            try:
                penalty, calc = rec._agent_create_vendor_penalty(vendor)
                rec.sudo().write({
                    'agent_penalty_id': penalty.id,
                    'agent_penalty_created': True,
                    'agent_penalty_amount': calc['penalty_amount'],
                    'agent_penalty_rate': calc['rate'],
                    'agent_penalty_notification': calc['notification'],
                })

                rec._agent_create_log(
                    decision='created',
                    reason='تم إنشاء الجزاء تلقائياً بسبب رفض أو مطابقة جزئية في محضر لجنة الفحص.',
                    trigger=trigger,
                    penalty=penalty,
                    calc=calc,
                )

                message = Markup('<p>🤖 تم إنشاء جزاء تلقائي للمورد <b>%s</b> بقيمة <b>%.2f</b>.</p><p>%s</p>') % (
                    vendor.display_name, calc['penalty_amount'], calc['notification']
                )
                rec.message_post(body=message)
                if hasattr(penalty, 'message_post'):
                    penalty.message_post(body=Markup('<p>تم إنشاء هذا الجزاء تلقائياً من محضر لجنة الفحص: <b>%s</b>.</p>') % (rec.committee_number or rec.display_name))

                rec._agent_auto_approve_penalty_if_enabled(penalty)

            except Exception as exc:
                rec._agent_create_log(
                    decision='error',
                    reason='حدث خطأ أثناء إنشاء الجزاء.',
                    trigger=trigger,
                    technical_details=str(exc),
                )
        return True

    def _agent_requires_penalty(self):
        self.ensure_one()
        result = self.result or ''
        conformity = self.specs_conformity or ''
        qty_rejected = self.quantity_rejected or 0.0

        bad_results = {'rejected', 'partial', 'fail', 'failed', 'refused', 'مرفوض', 'مطابق جزئيا', 'مطابق جزئياً'}
        bad_conformity = {'nonconforming', 'partial', 'not_conforming', 'non_conforming', 'fail', 'failed', 'غير مطابق', 'مطابق جزئيا', 'مطابق جزئياً'}

        return (
            result in bad_results
            or conformity in bad_conformity
            or qty_rejected > 0
        )

    def _agent_find_duplicate_penalty(self, vendor):
        self.ensure_one()
        Penalty = self.env['port_said.penalty'].sudo()
        source_text = self.committee_number or str(self.id)

        domain = [('vendor_id', '=', vendor.id)]
        candidates = Penalty.search(domain, limit=50, order='id desc')
        for p in candidates:
            haystack = []
            for fname in ['penalty_description', 'reason', 'description', 'notes', 'source_ref', 'reference', 'origin', 'name']:
                if fname in p._fields and p[fname]:
                    haystack.append(str(p[fname]))
            if source_text and source_text in ' '.join(haystack):
                return p
        return False

    def _agent_create_vendor_penalty(self, vendor):
        self.ensure_one()
        offense_count = self._agent_count_vendor_upheld_or_valid_penalties(vendor)
        rate = self._agent_get_penalty_rate(offense_count)
        rejected_value = self._agent_get_rejected_value()
        penalty_amount = rejected_value * rate
        notification = self._agent_generate_vendor_notification(vendor, offense_count, rate, rejected_value, penalty_amount)
        description = self._agent_generate_penalty_description(vendor, offense_count, rate, rejected_value, penalty_amount)

        vals = self._agent_prepare_penalty_vals(vendor, penalty_amount, description, rejected_value)
        penalty = self.env['port_said.penalty'].sudo().create(vals)

        calc = {
            'offense_count': offense_count,
            'rate': rate,
            'rejected_value': rejected_value,
            'penalty_amount': penalty_amount,
            'notification': notification,
            'description': description,
            'vals': vals,
        }
        return penalty, calc

    def _agent_prepare_penalty_vals(self, vendor, amount, description, rejected_value):
        self.ensure_one()
        Penalty = self.env['port_said.penalty']
        vals = {}

        def put(field_name, value):
            if field_name in Penalty._fields:
                vals[field_name] = value

        put('subject_type', 'vendor')
        put('vendor_id', vendor.id)
        put('amount', amount)
        put('penalty_description', description)
        put('reason', description)
        put('description', description)
        put('notes', description)
        put('incident_date', self.date_inspection or fields.Date.context_today(self))
        put('date', self.date_inspection or fields.Date.context_today(self))
        put('contract_value', self.purchase_order_id.amount_total if self.purchase_order_id and 'amount_total' in self.purchase_order_id._fields else rejected_value)
        put('source_ref', self.committee_number or self.display_name)
        put('reference', self.committee_number or self.display_name)
        put('origin', self.committee_number or self.display_name)
        put('purchase_order_id', self.purchase_order_id.id if self.purchase_order_id else False)
        put('inspection_id', self.id)
        put('company_id', self.env.company.id)

        if 'currency_id' in Penalty._fields:
            currency = self.purchase_order_id.currency_id if self.purchase_order_id and 'currency_id' in self.purchase_order_id._fields else self.env.company.currency_id
            vals['currency_id'] = currency.id

        if 'violation_type_id' in Penalty._fields:
            vt = self._agent_get_or_create_violation_type()
            if vt:
                vals['violation_type_id'] = vt.id

        if 'penalty_type_option_id' in Penalty._fields:
            opt = self._agent_get_or_create_penalty_type_option()
            if opt:
                vals['penalty_type_option_id'] = opt.id

        return vals

    def _agent_get_or_create_violation_type(self):
        Model = self.env['port_said.penalty.violation_type'].sudo()
        vt = Model.search([('name', 'ilike', 'مخالفة توريد')], limit=1)
        if vt:
            return vt

        vals = {}
        for fname in ['name', 'description']:
            if fname in Model._fields:
                vals[fname] = 'مخالفة توريد - رفض أو مطابقة جزئية'
        if 'subject_type' in Model._fields:
            vals['subject_type'] = 'vendor'
        if 'max_fine_percent' in Model._fields:
            vals['max_fine_percent'] = 15.0
        if 'max_fine_fixed' in Model._fields:
            vals['max_fine_fixed'] = 0.0
        try:
            return Model.create(vals)
        except Exception:
            return Model.search([], limit=1)

    def _agent_get_or_create_penalty_type_option(self):
        Model = self.env['port_said.penalty.type_option'].sudo()
        opt = Model.search([('name', 'ilike', 'غرامة')], limit=1)
        if opt:
            return opt
        vals = {}
        if 'name' in Model._fields:
            vals['name'] = 'غرامة مالية'
        if 'code' in Model._fields:
            vals['code'] = 'financial_fine'
        try:
            return Model.create(vals)
        except Exception:
            return Model.search([], limit=1)

    def _agent_count_vendor_upheld_or_valid_penalties(self, vendor):
        Penalty = self.env['port_said.penalty'].sudo()
        domain = [('vendor_id', '=', vendor.id)]
        if 'state' in Penalty._fields:
            domain.append(('state', 'in', ['approved', 'executed', 'upheld', 'closed', 'recorded']))
        return Penalty.search_count(domain)

    def _agent_get_penalty_rate(self, offense_count):
        ICP = self.env['ir.config_parameter'].sudo()
        first = float(ICP.get_param('port_said_vendor_penalty_ai_agent.first_rate', '0.05') or 0.05)
        second = float(ICP.get_param('port_said_vendor_penalty_ai_agent.second_rate', '0.10') or 0.10)
        third = float(ICP.get_param('port_said_vendor_penalty_ai_agent.third_rate', '0.15') or 0.15)

        if offense_count <= 0:
            return first
        if offense_count == 1:
            return second
        return third

    def _agent_get_rejected_value(self):
        self.ensure_one()
        qty_rejected = self.quantity_rejected or 0.0
        qty_received = getattr(self, 'quantity_received', 0.0) or 0.0
        po = self.purchase_order_id

        if not po:
            return 0.0

        amount_total = po.amount_total if 'amount_total' in po._fields else 0.0

        if qty_rejected > 0 and qty_received > 0 and amount_total:
            return amount_total * (qty_rejected / qty_received)

        unit_price = self._agent_get_unit_price()
        if qty_rejected > 0 and unit_price > 0:
            return qty_rejected * unit_price

        if amount_total:
            if (self.result or '') in ['rejected', 'مرفوض']:
                return amount_total
            return amount_total * 0.5

        return 0.0

    def _agent_get_unit_price(self):
        self.ensure_one()
        po = self.purchase_order_id
        if not po or 'order_line' not in po._fields:
            return 0.0
        lines = po.order_line.filtered(lambda l: not getattr(l, 'display_type', False))
        if not lines:
            return 0.0
        total_qty = sum(lines.mapped('product_qty')) or 0.0
        total_amount = sum(lines.mapped('price_subtotal')) or 0.0
        if total_qty:
            return total_amount / total_qty
        return 0.0

    def _agent_generate_penalty_description(self, vendor, offense_count, rate, rejected_value, penalty_amount):
        self.ensure_one()
        return (
            'تم إنشاء هذا الجزاء تلقائياً بواسطة وكيل كشف الجزاءات للموردين.\\n'
            'المورد: %s\\n'
            'محضر لجنة الفحص: %s\\n'
            'تاريخ الفحص: %s\\n'
            'نتيجة الفحص: %s\\n'
            'مطابقة المواصفات: %s\\n'
            'الكمية المرفوضة: %s\\n'
            'عدد الجزاءات السابقة المحتسبة: %s\\n'
            'نسبة الجزاء المطبقة: %.2f%%\\n'
            'قيمة الجزء المرفوض: %.2f\\n'
            'قيمة الجزاء: %.2f\\n'
            'أساس الإجراء: رفض أو مطابقة جزئية في نموذج 12 مخازن، مع حق المورد في التظلم وفقاً للإجراءات المعتمدة.'
        ) % (
            vendor.display_name,
            self.committee_number or self.display_name,
            self.date_inspection or '',
            self.result or '',
            self.specs_conformity or '',
            self.quantity_rejected or 0.0,
            offense_count,
            rate * 100,
            rejected_value,
            penalty_amount,
        )

    def _agent_generate_vendor_notification(self, vendor, offense_count, rate, rejected_value, penalty_amount):
        self.ensure_one()
        return (
            'السادة / %s\\n\\n'
            'تحية طيبة وبعد،\\n'
            'بالإشارة إلى أمر التوريد رقم %s ومحضر لجنة الفحص رقم %s بتاريخ %s، '
            'فقد تبين للجنة وجود رفض أو مطابقة جزئية للأصناف محل الفحص.\\n\\n'
            'وبناءً عليه، تم احتساب جزاء بنسبة %.2f%% من قيمة الجزء المرفوض البالغة %.2f، '
            'لتكون قيمة الجزاء %.2f.\\n\\n'
            'ويحق لكم التقدم بتظلم وفقاً للإجراءات والمواعيد المعتمدة، على أن يتم فحص التظلم من الجهة المختصة.\\n\\n'
            'وتفضلوا بقبول فائق الاحترام.'
        ) % (
            vendor.display_name,
            self.purchase_order_id.name if self.purchase_order_id else '',
            self.committee_number or '',
            self.date_inspection or '',
            rate * 100,
            rejected_value,
            penalty_amount,
        )

    def _agent_create_log(self, decision, reason, trigger='', penalty=False, calc=None, technical_details=''):
        self.ensure_one()
        calc = calc or {}
        vendor = self.purchase_order_id.partner_id if self.purchase_order_id else False
        self.env['port_said.vendor.penalty.agent.log'].sudo().create({
            'inspection_id': self.id,
            'purchase_order_id': self.purchase_order_id.id if self.purchase_order_id else False,
            'vendor_id': vendor.id if vendor else False,
            'penalty_id': penalty.id if penalty else False,
            'decision': decision,
            'result': str(self.result or ''),
            'specs_conformity': str(self.specs_conformity or ''),
            'quantity_rejected': self.quantity_rejected or 0.0,
            'offense_count': calc.get('offense_count', 0),
            'penalty_rate': calc.get('rate', 0.0),
            'rejected_value': calc.get('rejected_value', 0.0),
            'penalty_amount': calc.get('penalty_amount', 0.0),
            'notification_text': calc.get('notification', ''),
            'decision_reason': reason,
            'technical_details': technical_details or ('Trigger: %s' % trigger),
        })

    def _agent_auto_approve_penalty_if_enabled(self, penalty):
        auto = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_vendor_penalty_ai_agent.auto_approve', 'False'
        ) == 'True'
        if not auto:
            return

        for method in ['action_record', 'action_approve', 'button_approve']:
            if hasattr(penalty, method):
                try:
                    getattr(penalty, method)()
                except Exception:
                    pass
