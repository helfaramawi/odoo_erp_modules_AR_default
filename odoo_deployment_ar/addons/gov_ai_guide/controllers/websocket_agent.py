# -*- coding: utf-8 -*-
"""
متحكم WebSocket للمرشد الحكومي — /gov_ai/ws
يحافظ على اتصال مستمر لكل تبويب متصفح ويبث الردود رمزاً بعد رمز
"""
import json
import time
import logging
import hashlib
import threading

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# ذاكرة مؤقتة للتلميحات — مفتاحها: hash(model+field+value)
# تخزن آخر 50 تلميح لتجنب استدعاء API متكرر لنفس البيانات
_hint_cache = {}
_hint_cache_lock = threading.Lock()
_CACHE_SIZE = 50


def _get_cache_key(model: str, field: str, value: str) -> str:
    return hashlib.md5(f"{model}|{field}|{value[:100]}".encode()).hexdigest()


def _cache_get(key: str):
    with _hint_cache_lock:
        return _hint_cache.get(key)


def _cache_set(key: str, value: str):
    with _hint_cache_lock:
        if len(_hint_cache) >= _CACHE_SIZE:
            # إزالة أقدم عنصر (FIFO)
            oldest_key = next(iter(_hint_cache))
            del _hint_cache[oldest_key]
        _hint_cache[key] = value


class GovAIWebSocketController(http.Controller):
    """
    متحكم WebSocket — يستخدم Odoo 17's bus.Bus للاتصالات الثنائية الاتجاه
    البروتوكول:
      CLIENT → SERVER: JSON message بنوع 'hint_request'
      SERVER → CLIENT: بث رموز عبر البروتوكول

    ملاحظة تقنية: Odoo 17 Community يستخدم gevent للـ WebSocket الحقيقي.
    نستخدم هنا آلية longpolling + streaming عبر HTTP للتوافقية الأوسع،
    مع إمكانية الترقية لـ WebSocket حقيقي في Odoo Enterprise.
    """

    @http.route('/gov_ai/ws/connect', type='json', auth='user', methods=['POST'])
    def ws_connect(self, session_token=None, **kwargs):
        """
        نقطة بداية الاتصال — تُنشئ/تسترجع جلسة المرشد
        تُستدعى من agent_connector.js عند تحميل التطبيق
        """
        if not session_token:
            return {'error': 'session_token مطلوب'}

        env = request.env
        session = env['gov.agent.session'].sudo().get_or_create_session(
            session_token=session_token,
            user_id=request.env.uid,
        )
        return {
            'status': 'connected',
            'session_id': session.id,
            'user_name': request.env.user.name,
        }

    @http.route('/gov_ai/ws/hint', type='json', auth='user', methods=['POST'])
    def ws_hint(self, session_token=None, model=None, field=None,
                value=None, view_type='form', record_id=None,
                form_state='edit', **kwargs):
        """
        نقطة طلب التلميح — تُعيد JSON مع التلميح الكامل
        للبث الحقيقي token-by-token نستخدم /gov_ai/stream
        """
        if not session_token:
            return {'error': 'session_token مطلوب', 'type': 'hint_error'}

        env = request.env.sudo()

        # التحقق من صحة الجلسة
        session = env['gov.agent.session'].search([
            ('session_token', '=', session_token),
            ('user_id', '=', request.env.uid),
        ], limit=1)

        if not session:
            return {'error': 'جلسة غير صالحة', 'type': 'hint_error'}

        payload = {
            'model': model or '',
            'field': field or '',
            'value': value or '',
            'view_type': view_type,
            'record_id': record_id,
        }

        # التحقق من الذاكرة المؤقتة أولاً
        cache_key = _get_cache_key(
            payload['model'], payload['field'], payload['value']
        )
        cached_hint = _cache_get(cache_key)
        if cached_hint:
            env['gov.agent.log'].create_hint_log(
                session=session,
                payload=payload,
                hint_text=cached_hint,
                kb_chunks=[],
                tokens=0,
                response_ms=0,
                cached=True,
            )
            session.total_hints += 1
            return {
                'type': 'hint_done',
                'text': cached_hint,
                'cached': True,
            }

        # بناء السياق واستدعاء API
        start_time = time.time()
        try:
            system_prompt, user_message, history = session.process(payload)
            hint_text, tokens_used, kb_chunks = self._call_anthropic(
                system_prompt=system_prompt,
                user_message=user_message,
                history=history,
                env=env,
            )
            response_ms = int((time.time() - start_time) * 1000)

            # حفظ في الذاكرة المؤقتة
            _cache_set(cache_key, hint_text)

            # تسجيل التلميح
            log = env['gov.agent.log'].create_hint_log(
                session=session,
                payload=payload,
                hint_text=hint_text,
                kb_chunks=kb_chunks,
                tokens=tokens_used,
                response_ms=response_ms,
            )

            # تحديث سجل المحادثة
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
            _logger.error('gov_ai_guide: خطأ في معالجة التلميح: %s', str(e))
            # إعادة التلميح الاحتياطي من FIELD_HINT_CONTEXT
            fallback = self._get_fallback_hint(payload, env)
            response_ms = int((time.time() - start_time) * 1000)
            env['gov.agent.log'].create_hint_log(
                session=session,
                payload=payload,
                hint_text=fallback,
                kb_chunks=[],
                tokens=0,
                response_ms=response_ms,
                fallback=True,
            )
            return {
                'type': 'hint_done',
                'text': fallback,
                'fallback': True,
            }

    @http.route('/gov_ai/stream', type='http', auth='user', methods=['GET'])
    def stream_hint(self, session_token=None, model=None, field=None,
                    value=None, view_type='form', **kwargs):
        """
        بث التلميح بتقنية Server-Sent Events (SSE) — token بعد token
        المتصفح يستقبل الرموز فور توليدها من Anthropic
        """
        if not session_token:
            return request.make_response(
                'data: {"error": "session_token مطلوب"}\n\n',
                headers=[('Content-Type', 'text/event-stream')]
            )

        env = request.env
        session = env['gov.agent.session'].sudo().search([
            ('session_token', '=', session_token),
            ('user_id', '=', request.env.uid),
        ], limit=1)

        if not session:
            return request.make_response(
                'data: {"error": "جلسة غير صالحة"}\n\n',
                headers=[('Content-Type', 'text/event-stream')]
            )

        payload = {
            'model': model or '',
            'field': field or '',
            'value': value or '',
            'view_type': view_type,
        }

        def generate():
            """مولّد SSE — يبث كل رمز فور وصوله من Anthropic"""
            start_time = time.time()
            full_text = []
            tokens_used = 0

            try:
                system_prompt, user_message, history = session.process(payload)
                api_key = env['ir.config_parameter'].sudo().get_param('gov_ai_guide.api_key')

                if not api_key:
                    yield 'data: {"type":"hint_error","message":"لم يتم تعيين Anthropic API Key"}\n\n'
                    return

                import anthropic
                client = anthropic.Anthropic(api_key=api_key)

                messages = [{'role': m['role'], 'content': m['content']}
                            for m in (history or [])
                            if m.get('role') in ('user', 'assistant')]
                # تأكد من أن آخر رسالة هي user
                if not messages or messages[-1]['role'] != 'user':
                    messages.append({'role': 'user', 'content': user_message})

                with client.messages.stream(
                    model='claude-sonnet-4-6',
                    max_tokens=1024,
                    system=system_prompt,
                    messages=messages[-10:],  # آخر 10 رسائل فقط لتجنب تجاوز الحد
                ) as stream:
                    for text_chunk in stream.text_stream:
                        full_text.append(text_chunk)
                        chunk_data = json.dumps({
                            'type': 'hint_chunk',
                            'text': text_chunk,
                        }, ensure_ascii=False)
                        yield f'data: {chunk_data}\n\n'

                    # الحصول على الإحصائيات النهائية
                    final_message = stream.get_final_message()
                    tokens_used = final_message.usage.input_tokens + final_message.usage.output_tokens

            except Exception as e:
                _logger.error('gov_ai_guide: خطأ في البث: %s', str(e))
                # احتياطي
                fallback = self._get_fallback_hint(payload, env)
                full_text = [fallback]
                chunk_data = json.dumps({
                    'type': 'hint_chunk',
                    'text': fallback,
                }, ensure_ascii=False)
                yield f'data: {chunk_data}\n\n'

            # إنهاء البث
            complete_text = ''.join(full_text)
            response_ms = int((time.time() - start_time) * 1000)

            # حفظ في الذاكرة المؤقتة
            cache_key = _get_cache_key(
                payload['model'], payload['field'], payload['value']
            )
            _cache_set(cache_key, complete_text)

            # تسجيل في قاعدة البيانات
            try:
                log = env['gov.agent.log'].sudo().create_hint_log(
                    session=session,
                    payload=payload,
                    hint_text=complete_text,
                    kb_chunks=[],
                    tokens=tokens_used,
                    response_ms=response_ms,
                )
                session.add_to_history('assistant', complete_text)
                session.total_hints += 1

                done_data = json.dumps({
                    'type': 'hint_done',
                    'log_id': log.id,
                    'tokens': tokens_used,
                    'response_ms': response_ms,
                }, ensure_ascii=False)
                yield f'data: {done_data}\n\n'
            except Exception as e:
                _logger.error('gov_ai_guide: فشل تسجيل التلميح: %s', e)

        return request.make_response(
            generate(),
            headers=[
                ('Content-Type', 'text/event-stream'),
                ('Cache-Control', 'no-cache'),
                ('X-Accel-Buffering', 'no'),  # تعطيل buffering في nginx
                ('Access-Control-Allow-Origin', '*'),
            ],
        )

    def _call_anthropic(self, system_prompt, user_message, history, env):
        """
        استدعاء Anthropic API بدون بث (للـ REST endpoint)
        يُعيد: (hint_text, tokens_used, kb_chunks_used)
        """
        api_key = env['ir.config_parameter'].get_param('gov_ai_guide.api_key')
        if not api_key:
            raise ValueError('Anthropic API Key غير محدد في المعلمات التقنية')

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
        return hint_text, tokens_used, []

    def _get_fallback_hint(self, payload, env):
        """
        التلميح الاحتياطي عند تعطل API
        يبحث في FIELD_HINT_CONTEXT ثم يعطي رسالة عامة
        """
        from .hint_api import GENERIC_FALLBACK_HINT
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
