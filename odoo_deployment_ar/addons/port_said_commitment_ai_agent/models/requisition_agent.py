# -*- coding: utf-8 -*-
import re

from odoo import models, _


class PortSaidRequisitionCommitmentAgent(models.Model):
    _inherit = 'port_said.requisition'

    def action_approve(self):
        result = super().action_approve()
        for req in self:
            req._agent_process_commitment_after_requisition_approval()
        return result

    def _agent_process_commitment_after_requisition_approval(self):
        self.ensure_one()

        params = self.env['ir.config_parameter'].sudo()
        enabled = params.get_param('port_said_commitment_ai_agent.enabled', 'True') == 'True'
        auto_limit = float(params.get_param('port_said_commitment_ai_agent.auto_limit', '50000') or 50000)

        if not enabled:
            self._agent_create_log(False, 'skipped_config', 'أتمتة الارتباطات غير مفعلة من الإعدادات.', auto_limit=auto_limit)
            return True

        commitment = self._agent_get_commitment()
        if not commitment:
            self._agent_create_log(False, 'skipped_no_commitment', 'تم اعتماد الطلب ولكن لم يتم العثور على ارتباط مرتبط به.', auto_limit=auto_limit)
            return True

        total_amount = self._agent_get_total_amount()
        available_balance = self._agent_get_available_balance()
        vendor_penalties, penalty_summary = self._agent_check_vendor_penalties()
        risk = self._agent_assess_requisition_risk(total_amount, available_balance, vendor_penalties, penalty_summary, auto_limit)

        require_balance = params.get_param('port_said_commitment_ai_agent.require_available_balance', 'True') == 'True'
        strict_penalties = params.get_param('port_said_commitment_ai_agent.strict_vendor_penalties', 'True') == 'True'

        can_auto = (
            total_amount <= auto_limit
            and risk['level'] == 'low'
            and (not strict_penalties or not vendor_penalties)
            and (not require_balance or available_balance >= total_amount)
        )

        if can_auto:
            decision, reason, technical = self._agent_auto_approve_and_reserve_commitment(commitment, risk)
        else:
            decision = 'manual_review'
            reason = self._agent_prepare_manual_review_reason(total_amount, available_balance, auto_limit, vendor_penalties, penalty_summary, risk)
            technical = 'Auto reservation conditions were not met.'
            self._agent_notify_approver(commitment, reason)

        log = self._agent_create_log(
            commitment=commitment,
            decision=decision,
            decision_reason=reason,
            technical_details=technical,
            risk_level=risk['level'],
            risk_score=risk['score'],
            vendor_has_penalties=vendor_penalties,
            penalty_summary=penalty_summary,
            auto_limit=auto_limit,
        )
        self._agent_post_decision_to_chatter(commitment, log, reason)
        return True

    def _agent_get_commitment(self):
        self.ensure_one()

        if 'commitment_id' in self._fields and self.commitment_id:
            return self.commitment_id

        commitment_model = self.env['port_said.commitment']
        for field_name in ['requisition_id', 'request_id', 'scm_requisition_id', 'source_requisition_id']:
            if field_name in commitment_model._fields:
                found = commitment_model.search([(field_name, '=', self.id)], limit=1, order='id desc')
                if found:
                    return found

        if 'origin' in commitment_model._fields and 'name' in self._fields and self.name:
            found = commitment_model.search([('origin', '=', self.name)], limit=1, order='id desc')
            if found:
                return found

        return False

    def _agent_get_total_amount(self):
        self.ensure_one()
        for field_name in ['total_amount', 'amount_total', 'estimated_amount', 'amount']:
            if field_name in self._fields and self[field_name]:
                try:
                    return float(self[field_name])
                except Exception:
                    return 0.0
        return 0.0

    def _agent_get_available_balance(self):
        self.ensure_one()
        for field_name in ['available_balance', 'budget_available_balance', 'remaining_balance']:
            if field_name in self._fields and self[field_name]:
                try:
                    return float(self[field_name])
                except Exception:
                    return 0.0

        if 'budget_position_id' in self._fields and self.budget_position_id:
            bp = self.budget_position_id
            for field_name in ['available_balance', 'amount_available', 'remaining_balance', 'balance']:
                if field_name in bp._fields and bp[field_name]:
                    try:
                        return float(bp[field_name])
                    except Exception:
                        return 0.0

        return 0.0

    def _agent_get_vendor(self):
        self.ensure_one()
        for field_name in ['vendor_id', 'partner_id', 'supplier_id']:
            if field_name in self._fields and self[field_name]:
                return self[field_name]
        return False

    def _agent_check_vendor_penalties(self):
        vendor = self._agent_get_vendor()
        if not vendor:
            return False, 'لا يوجد مورد محدد على الطلب.'

        summaries = []
        total_count = 0
        for model_name in ['port_said.penalty', 'port_said.penalties', 'vendor.penalty', 'res.partner.penalty']:
            if model_name not in self.env:
                continue

            model = self.env[model_name].sudo()
            partner_field = False
            for f in ['vendor_id', 'partner_id', 'supplier_id']:
                if f in model._fields:
                    partner_field = f
                    break
            if not partner_field:
                continue

            domain = [(partner_field, '=', vendor.id)]
            if 'state' in model._fields:
                domain.append(('state', 'not in', ['cancel', 'cancelled', 'closed', 'done']))

            records = model.search(domain, limit=5, order='id desc')
            if records:
                total_count += len(records)
                summaries.append('%s: %s سجل' % (model_name, len(records)))

        if total_count:
            return True, '؛ '.join(summaries)
        return False, 'لا توجد جزاءات نشطة مسجلة على المورد.'

    def _agent_assess_requisition_risk(self, total_amount, available_balance, vendor_has_penalties, penalty_summary, auto_limit):
        score = 0.0
        reasons = []

        if total_amount <= 0:
            score += 40
            reasons.append('إجمالي الطلب غير واضح أو يساوي صفر.')
        if total_amount > auto_limit:
            score += 35
            reasons.append('قيمة الطلب أكبر من حد الأتمتة.')
        if available_balance and total_amount > available_balance:
            score += 40
            reasons.append('قيمة الطلب تتجاوز الرصيد المتاح.')
        if vendor_has_penalties:
            score += 35
            reasons.append('يوجد سجل جزاءات أو ملاحظات نشطة على المورد.')

        justification = self._agent_get_text_value(['justification', 'description', 'notes', 'reason'])
        if not justification or len(justification.strip()) < 20:
            score += 20
            reasons.append('مبرر الطلب غير كافٍ أو قصير.')

        normalized = self._agent_normalize_text(justification)
        for word in ['عاجل جدا', 'بدون عرض', 'استثناء', 'مباشر', 'طارئ']:
            if self._agent_normalize_text(word) in normalized:
                score += 10
                reasons.append('المبرر يحتوي على كلمات تستدعي مراجعة إضافية.')
                break

        if score <= 25:
            level = 'low'
        elif score <= 60:
            level = 'medium'
        else:
            level = 'high'

        if not reasons:
            reasons.append('الطلب ضمن حد الأتمتة ولا توجد مؤشرات مخاطر واضحة وفق القواعد الحالية.')

        return {'score': score, 'level': level, 'reason': ' '.join(reasons), 'penalty_summary': penalty_summary}

    def _agent_get_text_value(self, field_names):
        values = []
        for field_name in field_names:
            if field_name in self._fields and self[field_name]:
                values.append(str(self[field_name]))
        return '\\n'.join(values)

    def _agent_normalize_text(self, text):
        text = str(text or '').lower()
        text = re.sub(r'[\\s\\u0640]+', ' ', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        return text.strip()

    def _agent_auto_approve_and_reserve_commitment(self, commitment, risk):
        technical_steps = []
        try:
            if hasattr(commitment, 'action_approve'):
                commitment.action_approve()
                technical_steps.append('action_approve executed.')
            elif hasattr(commitment, 'button_approve'):
                commitment.button_approve()
                technical_steps.append('button_approve executed.')
            else:
                technical_steps.append('No approve method found.')

            if hasattr(commitment, 'action_reserve'):
                commitment.action_reserve()
                technical_steps.append('action_reserve executed.')
            elif hasattr(commitment, 'button_reserve'):
                commitment.button_reserve()
                technical_steps.append('button_reserve executed.')
            else:
                technical_steps.append('No reserve method found.')

            reason = (
                'تم اعتماد وتجنيب الارتباط تلقائياً لأن قيمة الطلب ضمن الحد المسموح، '
                'ولا توجد جزاءات نشطة على المورد، ومستوى المخاطر منخفض. '
                'درجة المخاطر: %.2f. %s'
            ) % (risk['score'], risk['reason'])

            self._agent_write_commitment_note(commitment, reason)
            return 'auto_reserved', reason, '\\n'.join(technical_steps)

        except Exception as exc:
            reason = 'فشل الاعتماد/التجنيب التلقائي للارتباط ويلزم مراجعة بشرية. سبب الخطأ: %s' % str(exc)
            self._agent_write_commitment_note(commitment, reason)
            return 'failed', reason, '\\n'.join(technical_steps)

    def _agent_prepare_manual_review_reason(self, total_amount, available_balance, auto_limit, vendor_penalties, penalty_summary, risk):
        reasons = []
        if total_amount > auto_limit:
            reasons.append('قيمة الطلب %.2f أكبر من حد الأتمتة %.2f.' % (total_amount, auto_limit))
        if available_balance and total_amount > available_balance:
            reasons.append('قيمة الطلب %.2f أكبر من الرصيد المتاح %.2f.' % (total_amount, available_balance))
        if vendor_penalties:
            reasons.append('يوجد جزاءات/ملاحظات على المورد: %s.' % penalty_summary)
        if risk['level'] != 'low':
            reasons.append('مستوى المخاطر ليس منخفضاً: %s، درجة المخاطر %.2f. %s' % (risk['level'], risk['score'], risk['reason']))
        if not reasons:
            reasons.append('يتطلب الطلب مراجعة بشرية وفق قواعد الوكيل الحالية.')
        return '\\n'.join(reasons)

    def _agent_notify_approver(self, commitment, reason):
        param_user_id = self.env['ir.config_parameter'].sudo().get_param('port_said_commitment_ai_agent.notify_user_id')
        user = False
        if param_user_id:
            try:
                user = self.env['res.users'].browse(int(param_user_id))
            except Exception:
                user = False

        if not user or not user.exists():
            user = self.create_uid or self.env.user

        if hasattr(commitment, 'activity_schedule'):
            commitment.activity_schedule('mail.mail_activity_data_warning', user_id=user.id, summary='مراجعة ارتباط مطلوبة', note=reason)

    def _agent_write_commitment_note(self, commitment, note):
        if not commitment:
            return
        if 'notes' in commitment._fields:
            current = commitment.notes or ''
            commitment.sudo().write({'notes': (current + '\\n\\n' + note).strip()})
        elif 'note' in commitment._fields:
            current = commitment.note or ''
            commitment.sudo().write({'note': (current + '\\n\\n' + note).strip()})

    def _agent_create_log(self, commitment, decision, decision_reason, technical_details='', risk_level='medium', risk_score=0.0, vendor_has_penalties=False, penalty_summary='', auto_limit=50000.0):
        vendor = self._agent_get_vendor()
        vals = {
            'requisition_id': self.id,
            'commitment_id': commitment.id if commitment else False,
            'vendor_id': vendor.id if vendor else False,
            'total_amount': self._agent_get_total_amount(),
            'available_balance': self._agent_get_available_balance(),
            'auto_commit_limit': auto_limit,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'vendor_has_penalties': vendor_has_penalties,
            'penalty_summary': penalty_summary or '',
            'decision': decision,
            'decision_reason': decision_reason or '',
            'technical_details': technical_details or '',
        }
        return self.env['port_said.commitment.agent.log'].sudo().create(vals)

    def _agent_post_decision_to_chatter(self, commitment, log, reason):
        msg = _(
            'قرار وكيل أتمتة الارتباطات:<br/>'
            '<b>القرار:</b> %s<br/>'
            '<b>السبب:</b><br/>%s<br/>'
            '<b>رقم سجل القرار:</b> %s'
        ) % (
            dict(log._fields['decision'].selection).get(log.decision, log.decision),
            reason.replace('\\n', '<br/>'),
            log.name,
        )

        if hasattr(self, 'message_post'):
            self.message_post(body=msg)
        if commitment and hasattr(commitment, 'message_post'):
            commitment.message_post(body=msg)
