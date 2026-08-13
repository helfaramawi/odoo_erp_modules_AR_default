# -*- coding: utf-8 -*-
"""
نموذج جلسة المرشد — gov.agent.session
جلسة واحدة لكل مستخدم لكل تبويب في المتصفح — مستمرة طوال الجلسة
"""
import uuid
import json
import logging
from datetime import datetime, timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# النظام الأساسي للمرشد الحكومي — يُحدد شخصيته وأسلوبه
GOV_SYSTEM_PROMPT = """
أنت "المرشد الحكومي" — مساعد ذكي متخصص في الإجراءات الحكومية المصرية
مدمج داخل نظام ERP الحكومي المبني على Odoo.

## شخصيتك وأسلوبك:
- خبير حكومي بخبرة لا تقل عن 20 سنة في الإدارة المالية والمشتريات الحكومية
- تتحدث بلغة عربية رسمية فصحى مناسبة للوثائق الرسمية
- تستشهد دائماً بالقوانين واللوائح والقرارات الوزارية ذات الصلة بالسياق
- تعطي توجيهات عملية خطوة بخطوة مع المرجع القانوني لكل خطوة
- لا تتخمن — إذا لم يكن لديك مرجع قانوني واضح، تقول ذلك صراحةً
- تنبّه على المخاطر القانونية والمخالفات المحتملة بوضوح

## هيكل إجابتك (اتبعه دائماً):

**الإجراء المطلوب:**
[وصف واضح لما يجب فعله في هذه الخطوة]

**الأساس القانوني:**
[اذكر: رقم القانون / اللائحة / القرار الوزاري / المادة المحددة]

**تنبيهات هامة:**
[أي مخاطر، شروط، أو استثناءات يجب مراعاتها]

**الخطوة التالية:**
[ما يجب فعله بعد إتمام هذه الخطوة]

## قواعد صارمة:
1. لا تتجاوز 250 كلمة في الرد الواحد
2. استخدم الأرقام والتواريخ الحقيقية للقوانين المذكورة
3. إذا كان الحقل يتعلق بمبالغ مالية، اذكر حدود الصلاحيات المالية المعمول بها
4. إذا كان الحقل يتعلق بموردين أو عقود، أشر لقانون المناقصات والمزايدات
5. إذا كان الحقل يتعلق بالموارد البشرية، أشر لقانون الخدمة المدنية

## قاعدة المعرفة المتاحة:
{kb_context}

## سياق النظام:
النموذج الحالي: {model_name}
الحقل الحالي: {field_name}
القيمة الحالية: {field_value}
نوع العرض: {view_type}
وحدة النظام: {module_name}
"""


class AgentSession(models.Model):
    _name = 'gov.agent.session'
    _description = 'جلسة المرشد الحكومي الذكي'
    _order = 'last_active desc'

    user_id = fields.Many2one(
        'res.users',
        string='المستخدم',
        required=True,
        ondelete='cascade',
        index=True,
    )
    session_token = fields.Char(
        string='رمز الجلسة',
        required=True,
        index=True,
        default=lambda self: str(uuid.uuid4()),
        help='UUID فريد يطابق مفتاح localStorage في المتصفح',
    )
    last_active = fields.Datetime(
        string='آخر نشاط',
        default=fields.Datetime.now,
    )
    current_model = fields.Char(string='النموذج الحالي')
    current_field = fields.Char(string='الحقل الحالي')
    message_history = fields.Json(
        string='سجل المحادثة',
        default=list,
        help='آخر 20 رسالة (نافذة منزلقة)',
    )
    total_hints = fields.Integer(
        string='إجمالي التلميحات',
        default=0,
    )
    state = fields.Selection(
        selection=[
            ('active', 'نشط'),
            ('idle', 'خامل'),
            ('disconnected', 'منفصل'),
        ],
        string='الحالة',
        default='active',
    )

    @api.model
    def get_or_create_session(self, session_token, user_id=None):
        """
        استرجاع الجلسة الموجودة أو إنشاء جلسة جديدة
        يُستدعى من WebSocket عند أول اتصال
        """
        if not user_id:
            user_id = self.env.uid

        session = self.search([
            ('session_token', '=', session_token),
            ('user_id', '=', user_id),
        ], limit=1)

        if not session:
            session = self.create({
                'user_id': user_id,
                'session_token': session_token,
                'state': 'active',
            })
        else:
            session.write({
                'state': 'active',
                'last_active': fields.Datetime.now(),
            })
        return session

    def update_activity(self, model_name, field_name):
        """تحديث آخر حقل نشط للجلسة"""
        self.ensure_one()
        self.write({
            'current_model': model_name,
            'current_field': field_name,
            'last_active': fields.Datetime.now(),
            'state': 'active',
        })

    def add_to_history(self, role, content):
        """
        إضافة رسالة لسجل المحادثة مع الحفاظ على نافذة منزلقة بحجم 20 رسالة
        role: 'user' أو 'assistant'
        """
        self.ensure_one()
        history = self.message_history or []
        history.append({'role': role, 'content': content})
        # حافظ على آخر 20 رسالة فقط لتجنب تجاوز حجم السياق
        if len(history) > 20:
            history = history[-20:]
        self.message_history = history

    def process(self, payload):
        """
        المعالج الرئيسي: يبني السياق ويستدعي Anthropic API
        يُعيد مولّد (generator) يبث الرموز واحداً تلو الآخر
        """
        self.ensure_one()

        model_name = payload.get('model', '')
        field_name = payload.get('field', '')
        field_value = str(payload.get('value', ''))[:200]
        view_type = payload.get('view_type', 'form')
        module_name = model_name.split('.')[0] if '.' in model_name else model_name

        # 1. بناء السياق من قاعدة المعرفة
        kb_context = self._build_context(model_name, field_name, field_value)

        # 2. بناء prompt النظام مع السياق
        system_prompt = GOV_SYSTEM_PROMPT.format(
            kb_context=kb_context,
            model_name=model_name,
            field_name=field_name,
            field_value=field_value,
            view_type=view_type,
            module_name=module_name,
        )

        # 3. بناء رسالة المستخدم
        user_message = (
            f"أنا أعمل على حقل '{field_name}' في نموذج '{model_name}'. "
            f"القيمة الحالية: '{field_value}'. "
            f"ما الإرشاد الحكومي المناسب لهذه الخطوة؟"
        )

        # إضافة للسجل
        self.add_to_history('user', user_message)
        self.update_activity(model_name, field_name)

        return system_prompt, user_message, self.message_history

    def _build_context(self, model_name, field_name, field_value):
        """
        بناء السياق من:
        1. نتائج البحث في قاعدة المعرفة (vector similarity)
        2. FIELD_HINT_CONTEXT للحقول المعروفة
        3. سجل التلميحات السابقة لهذا الحقل
        """
        context_parts = []

        # البحث في قاعدة المعرفة
        indexer = self.env['gov.kb.indexer']
        query = f"{field_value or field_name}"
        kb_results = indexer.search_kb(
            query=query,
            model_name=model_name,
            field_name=field_name,
            top_k=5,
        )

        if kb_results:
            context_parts.append("=== نتائج من قاعدة المعرفة ===")
            for i, chunk in enumerate(kb_results, 1):
                law_ref = f"[{chunk.get('law_number', '')} — {chunk.get('authority', '')}]" \
                    if chunk.get('law_number') else ""
                context_parts.append(
                    f"{i}. {law_ref}\n{chunk.get('content', '')[:500]}"
                )

        # استخدام FIELD_HINT_CONTEXT كاحتياطي
        field_key = f"{model_name}.{field_name}"
        field_hint = indexer.FIELD_HINT_CONTEXT.get(field_key, {})
        if field_hint:
            context_parts.append("\n=== سياق الحقل المعروف ===")
            context_parts.append(field_hint.get('context', ''))
            if field_hint.get('law_ref'):
                context_parts.append(f"المرجع القانوني: {field_hint['law_ref']}")
            if field_hint.get('warning'):
                context_parts.append(f"⚠ تحذير: {field_hint['warning']}")

        # التلميحات السابقة لهذا الحقل
        prev_logs = self.env['gov.agent.log'].search([
            ('user_id', '=', self.user_id.id),
            ('model_name', '=', model_name),
            ('field_name', '=', field_name),
        ], limit=3, order='timestamp desc')

        if prev_logs:
            context_parts.append("\n=== التلميحات السابقة لهذا الحقل ===")
            for log in prev_logs:
                context_parts.append(
                    f"تلميح سابق ({log.timestamp}): {log.hint_text[:200]}..."
                )

        return "\n".join(context_parts) if context_parts else "لا توجد معلومات محددة في قاعدة المعرفة لهذا الحقل."

    @api.model
    def cleanup_idle_sessions(self):
        """تنظيف الجلسات الخاملة — يُستدعى بواسطة cron"""
        cutoff = datetime.now() - timedelta(hours=8)
        idle_sessions = self.search([
            ('last_active', '<', cutoff),
            ('state', '=', 'active'),
        ])
        idle_sessions.write({'state': 'idle'})

        # حذف الجلسات القديمة جداً (أكثر من 30 يوم)
        old_cutoff = datetime.now() - timedelta(days=30)
        old_sessions = self.search([('last_active', '<', old_cutoff)])
        old_sessions.unlink()
