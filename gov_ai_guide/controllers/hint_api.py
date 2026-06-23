# -*- coding: utf-8 -*-
"""
REST API للمرشد الحكومي — /gov_ai/hint
نقطة نهاية REST بديلة للـ WebSocket للأجهزة التي لا تدعمه
"""
import json
import time
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# تلميح عام للحالات التي لا يوجد فيها سياق محدد
GENERIC_FALLBACK_HINT = """**الإجراء المطلوب:**
يُرجى التأكد من صحة البيانات المُدخلة وتوافقها مع اللوائح الحكومية المعمول بها.

**الأساس القانوني:**
قانون المحاسبة الحكومية رقم 127 لسنة 1981 — المبادئ العامة.
اللائحة المالية للجهات الحكومية.

**تنبيهات هامة:**
⚠ تأكد من الحصول على الموافقات اللازمة قبل إتمام أي إجراء مالي.
⚠ احتفظ بجميع المستندات الداعمة لمدة لا تقل عن 5 سنوات.

**الخطوة التالية:**
راجع الإجراءات المعتمدة في دليل العمل الخاص بجهتك قبل المتابعة."""


class GovAIHintAPI(http.Controller):

    @http.route('/gov_ai/hint', type='json', auth='user', methods=['POST'], csrf=True)
    def get_hint(self, session_token=None, model=None, field=None,
                 value=None, view_type='form', record_id=None, **kwargs):
        """
        POST /gov_ai/hint
        الجسم: { session_token, model, field, value, view_type, record_id }
        الرد: { type, text, log_id, tokens, response_ms }

        هذه النقطة تُعيد التلميح كاملاً دفعة واحدة (بدون بث).
        للبث الحقيقي استخدم /gov_ai/stream
        """
        if not session_token or not model or not field:
            return {
                'type': 'hint_error',
                'message': 'session_token و model و field مطلوبة',
            }

        env = request.env.sudo()
        uid = request.env.uid

        # التحقق من الجلسة
        session = env['gov.agent.session'].search([
            ('session_token', '=', session_token),
            ('user_id', '=', uid),
        ], limit=1)

        if not session:
            # إنشاء جلسة جديدة تلقائياً
            session = env['gov.agent.session'].get_or_create_session(
                session_token=session_token,
                user_id=uid,
            )

        payload = {
            'model': model,
            'field': field,
            'value': str(value or '')[:200],
            'view_type': view_type,
            'record_id': record_id,
        }

        start_time = time.time()

        try:
            api_key = env['ir.config_parameter'].get_param('gov_ai_guide.api_key')
            if not api_key:
                _logger.warning('gov_ai_guide: API Key غير محدد')
                fallback = self._build_fallback(payload)
                return {
                    'type': 'hint_done',
                    'text': fallback,
                    'fallback': True,
                    'response_ms': int((time.time() - start_time) * 1000),
                }

            # بناء السياق
            system_prompt, user_message, history = session.process(payload)

            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            messages = []
            for msg in (history or []):
                if msg.get('role') in ('user', 'assistant'):
                    messages.append({'role': msg['role'], 'content': msg['content']})

            if not messages or messages[-1]['role'] != 'user':
                messages.append({'role': 'user', 'content': user_message})

            response = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=1024,
                system=system_prompt,
                messages=messages[-10:],
            )

            hint_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            response_ms = int((time.time() - start_time) * 1000)

            log = env['gov.agent.log'].create_hint_log(
                session=session,
                payload=payload,
                hint_text=hint_text,
                kb_chunks=[],
                tokens=tokens_used,
                response_ms=response_ms,
            )
            session.add_to_history('assistant', hint_text)
            session.total_hints += 1

            return {
                'type': 'hint_done',
                'text': hint_text,
                'log_id': log.id,
                'tokens': tokens_used,
                'response_ms': response_ms,
            }

        except Exception as e:
            _logger.error('gov_ai_guide REST: %s', str(e))
            fallback = self._build_fallback(payload)
            return {
                'type': 'hint_done',
                'text': fallback,
                'fallback': True,
                'response_ms': int((time.time() - start_time) * 1000),
            }

    @http.route('/gov_ai/session/ping', type='json', auth='user', methods=['POST'])
    def session_ping(self, session_token=None, **kwargs):
        """نبضة الجلسة — تُحدّث last_active وتبقي الجلسة حية"""
        if not session_token:
            return {'status': 'error'}

        session = request.env['gov.agent.session'].sudo().search([
            ('session_token', '=', session_token),
            ('user_id', '=', request.env.uid),
        ], limit=1)

        if session:
            session.write({'last_active': fields_now(), 'state': 'active'})
            return {'status': 'ok', 'session_id': session.id}
        return {'status': 'not_found'}

    @http.route('/gov_ai/followup', type='json', auth='user', methods=['POST'])
    def followup_question(self, session_token=None, question=None, **kwargs):
        """
        سؤال متابعة — يُرسله المستخدم من الشريط الجانبي
        يستخدم سياق المحادثة الموجود
        """
        if not session_token or not question:
            return {'type': 'hint_error', 'message': 'بيانات ناقصة'}

        env = request.env.sudo()
        session = env['gov.agent.session'].search([
            ('session_token', '=', session_token),
            ('user_id', '=', request.env.uid),
        ], limit=1)

        if not session:
            return {'type': 'hint_error', 'message': 'جلسة غير صالحة'}

        start_time = time.time()
        try:
            api_key = env['ir.config_parameter'].get_param('gov_ai_guide.api_key')
            if not api_key:
                return {'type': 'hint_error', 'message': 'API Key غير محدد'}

            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            # إضافة سؤال المتابعة للتاريخ
            session.add_to_history('user', question)
            history = session.message_history or []

            messages = [{'role': m['role'], 'content': m['content']}
                        for m in history if m.get('role') in ('user', 'assistant')]

            from odoo.addons.gov_ai_guide.models.agent_session import GOV_SYSTEM_PROMPT
            # نستخدم prompt مبسّط للمتابعة
            system = GOV_SYSTEM_PROMPT.format(
                kb_context='استمر في السياق الحالي للمحادثة',
                model_name=session.current_model or '',
                field_name=session.current_field or '',
                field_value='',
                view_type='form',
                module_name='',
            )

            response = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=1024,
                system=system,
                messages=messages[-10:],
            )
            answer = response.content[0].text
            session.add_to_history('assistant', answer)

            return {
                'type': 'hint_done',
                'text': answer,
                'response_ms': int((time.time() - start_time) * 1000),
            }
        except Exception as e:
            _logger.error('gov_ai_guide followup: %s', str(e))
            return {'type': 'hint_error', 'message': 'حدث خطأ في معالجة السؤال'}

    def _build_fallback(self, payload):
        """بناء تلميح احتياطي من FIELD_HINT_CONTEXT"""
        from odoo.addons.gov_ai_guide.models.kb_indexer import FIELD_HINT_CONTEXT
        field_key = f"{payload.get('model', '')}.{payload.get('field', '')}"
        hint_data = FIELD_HINT_CONTEXT.get(field_key, {})
        if hint_data:
            parts = []
            if hint_data.get('context'):
                parts.append(f"**الإجراء المطلوب:**\n{hint_data['context']}")
            if hint_data.get('law_ref'):
                parts.append(f"**الأساس القانوني:**\n{hint_data['law_ref']}")
            if hint_data.get('warning'):
                parts.append(f"**تنبيهات هامة:**\n⚠ {hint_data['warning']}")
            return '\n\n'.join(parts)
        return GENERIC_FALLBACK_HINT


def fields_now():
    """مساعد لإعادة الوقت الحالي"""
    from odoo import fields
    return fields.Datetime.now()
