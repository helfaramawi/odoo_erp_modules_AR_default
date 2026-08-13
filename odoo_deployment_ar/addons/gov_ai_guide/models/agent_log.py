# -*- coding: utf-8 -*-
"""
نموذج سجل المحادثة — gov.agent.log
سجل تدقيق كامل لكل تلميح تم عرضه على المستخدم
"""
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AgentLog(models.Model):
    _name = 'gov.agent.log'
    _description = 'سجل تلميحات المرشد الحكومي'
    _order = 'timestamp desc'

    session_id = fields.Many2one(
        'gov.agent.session',
        string='الجلسة',
        ondelete='set null',
        index=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='المستخدم',
        required=True,
        ondelete='cascade',
        index=True,
    )
    model_name = fields.Char(
        string='النموذج',
        required=True,
        index=True,
    )
    field_name = fields.Char(
        string='الحقل',
        required=True,
        index=True,
    )
    field_value = fields.Char(
        string='قيمة الحقل',
        help='القيمة عند طلب التلميح (محدودة بـ 200 حرف)',
    )
    hint_text = fields.Text(
        string='نص التلميح',
        help='النص العربي الكامل الذي عُرض على المستخدم',
    )
    kb_chunks_used = fields.Json(
        string='قطع قاعدة المعرفة المستخدمة',
        help='معرّفات ومحتوى القطع التي استُخدمت لبناء هذا التلميح (للتدقيق)',
    )
    tokens_used = fields.Integer(
        string='الرموز المستخدمة',
        help='عدد الرموز المستهلكة من Anthropic API',
    )
    response_ms = fields.Integer(
        string='زمن الاستجابة (مللي ثانية)',
        help='الوقت المستغرق من إرسال الطلب حتى اكتمال الرد',
    )
    timestamp = fields.Datetime(
        string='الوقت',
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    was_cached = fields.Boolean(
        string='من الذاكرة المؤقتة',
        default=False,
        help='هل جاء هذا التلميح من الـ cache أم من API مباشرة؟',
    )
    fallback_used = fields.Boolean(
        string='استُخدم الاحتياطي',
        default=False,
        help='هل استُخدم FIELD_HINT_CONTEXT كاحتياطي بدلاً من API؟',
    )

    @api.model
    def create_hint_log(self, session, payload, hint_text, kb_chunks, tokens, response_ms, cached=False, fallback=False):
        """
        تسجيل تلميح جديد — يُستدعى بعد اكتمال الاستجابة من API
        """
        return self.create({
            'session_id': session.id if session else False,
            'user_id': session.user_id.id if session else self.env.uid,
            'model_name': payload.get('model', ''),
            'field_name': payload.get('field', ''),
            'field_value': str(payload.get('value', ''))[:200],
            'hint_text': hint_text,
            'kb_chunks_used': kb_chunks,
            'tokens_used': tokens,
            'response_ms': response_ms,
            'timestamp': fields.Datetime.now(),
            'was_cached': cached,
            'fallback_used': fallback,
        })

    @api.model
    def get_stats_for_user(self, user_id):
        """إحصائيات استخدام المرشد لمستخدم معين"""
        logs = self.search([('user_id', '=', user_id)])
        return {
            'total_hints': len(logs),
            'total_tokens': sum(logs.mapped('tokens_used')),
            'avg_response_ms': sum(logs.mapped('response_ms')) / len(logs) if logs else 0,
            'cached_ratio': sum(1 for l in logs if l.was_cached) / len(logs) if logs else 0,
        }
