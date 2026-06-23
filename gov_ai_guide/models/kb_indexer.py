# -*- coding: utf-8 -*-
"""
فهرس قاعدة المعرفة — gov.kb.indexer
يقوم بفهرسة كود المصدر والوثائق القانونية وبناء متجهات دلالية للبحث السريع
"""
import os
import re
import ast
import json
import logging
import hashlib
from typing import List, Dict, Any

from odoo import models, api

_logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# سياق الحقول المعروفة — يُستخدم كاحتياطي عند عدم وجود نتائج من قاعدة المعرفة
# ──────────────────────────────────────────────────────────────────────────────
FIELD_HINT_CONTEXT = {
    # account.move
    "account.move.invoice_date": {
        "context": "تاريخ الفاتورة يجب أن يكون ضمن السنة المالية الحالية (1 يوليو — 30 يونيو).",
        "law_ref": "قانون 127/1981 — المادة 8",
        "warning": "لا يجوز إصدار فاتورة بتاريخ منقضٍ بعد قفل الحسابات في 30 يونيو.",
    },
    "account.move.partner_id": {
        "context": "يجب التحقق من تسجيل المورد/العميل في سجل الجهة وحصوله على الموافقات اللازمة.",
        "law_ref": "قانون 89/1998 — المادة 5",
        "warning": "التعامل مع موردين غير مسجلين مخالفة قانونية.",
    },
    "account.move.amount_total": {
        "context": "تحقق من حدود الصلاحيات المالية قبل اعتماد هذا المبلغ.",
        "law_ref": "اللائحة المالية 250/2019 — المادة 8",
        "warning": "المبالغ فوق 10,000 جنيه تحتاج اعتماد رئيس الجهة.",
    },
    "account.move.invoice_line_ids": {
        "context": "كل بند في الفاتورة يجب أن يكون مدعوماً بمستند صرف معتمد.",
        "law_ref": "قانون المحاسبة الحكومية 127/1981 — المادة 8",
        "warning": "لا يجوز تقسيم الفواتير لتجنب حدود الصلاحيات.",
    },
    "account.move.journal_id": {
        "context": "اختيار الدفتر المحاسبي يحدد نوع القيد وطريقة الترحيل.",
        "law_ref": "معايير المحاسبة الحكومية 270/2022 — المعيار 12",
        "warning": "تأكد من انتماء القيد للدفتر الصحيح وفق دليل الحسابات المعتمد.",
    },
    # purchase.order
    "purchase.order.partner_id": {
        "context": "المورد يجب أن يكون مسجلاً في سجل الموردين المعتمدين ومستوفياً لكل الشروط.",
        "law_ref": "قانون المناقصات 89/1998 — المادة 31",
        "warning": "تفضيل مورد بعينه بدون مسوّغ قانوني مخالفة جسيمة.",
    },
    "purchase.order.amount_total": {
        "context": "حدد نوع إجراء الشراء بناءً على القيمة الإجمالية للطلب.",
        "law_ref": "قانون 89/1998 — المادة 11",
        "warning": (
            "< 5,000 جنيه: ممارسة مباشرة | "
            "5,000 — 100,000 جنيه: عروض أسعار (3 على الأقل) | "
            "> 100,000 جنيه: مناقصة عامة إلزامية"
        ),
    },
    "purchase.order.date_order": {
        "context": "تاريخ أمر الشراء يجب أن يسبق تاريخ الاستلام ويكون ضمن السنة المالية.",
        "law_ref": "اللائحة المالية 250/2019 — المادة 15",
        "warning": "لا يجوز إصدار أمر شراء بأثر رجعي.",
    },
    "purchase.order.order_line": {
        "context": "تأكد من وجود الاعتماد المالي لكل بند في طلب الشراء.",
        "law_ref": "قانون الموازنة 53/1973 — المادة 17",
        "warning": "لا يجوز إبرام أي التزام مالي دون توافر اعتماد في الموازنة.",
    },
    # hr.employee
    "hr.employee.job_id": {
        "context": "الوظيفة يجب أن تكون موجودة في كادر التوظيف المعتمد من الجهاز المركزي للتنظيم والإدارة.",
        "law_ref": "قانون الخدمة المدنية 81/2016 — المادة 14",
        "warning": "التعيين في وظيفة خارج الكادر المعتمد يُعدّ باطلاً.",
    },
    "hr.employee.wage": {
        "context": "يجب أن يكون الراتب ضمن الحدين الأدنى والأقصى لدرجة الوظيفة.",
        "law_ref": "قانون الخدمة المدنية 81/2016 — المادة 92",
        "warning": "تجاوز الحد الأقصى للراتب مخالفة لائحية.",
    },
    "hr.employee.department_id": {
        "context": "القسم يجب أن يكون ضمن الهيكل التنظيمي المعتمد للجهة.",
        "law_ref": "قانون الخدمة المدنية 81/2016",
        "warning": "أي تعديل على الهيكل التنظيمي يستلزم موافقة الجهاز المركزي للتنظيم والإدارة.",
    },
    # stock.picking
    "stock.picking.scheduled_date": {
        "context": "تاريخ الاستلام يُحدد المسؤولية القانونية عن البضاعة وبداية احتساب الضمان.",
        "law_ref": "القانون المدني المصري — أحكام التسليم والقبض",
        "warning": "التوقيع على محضر الاستلام يُلزم الجهة قانونياً بقبول البضاعة.",
    },
    "stock.picking.partner_id": {
        "context": "تأكد من أن المورد/العميل هو نفسه المذكور في أمر الشراء/البيع.",
        "law_ref": "قانون 89/1998 — المادة 31",
        "warning": "استلام بضاعة من مورد غير المتعاقد معه يُبطل المعاملة.",
    },
    # account.payment
    "account.payment.amount": {
        "context": "مبلغ الدفع يجب أن لا يتجاوز قيمة الفاتورة المعتمدة.",
        "law_ref": "قانون المحاسبة الحكومية 127/1981 — المادة 19",
        "warning": "الدفع الزائد يستلزم قيد تسوية معتمد من الجهة المختصة.",
    },
    "account.payment.partner_id": {
        "context": "التحقق من هوية المستفيد قبل صرف أي مبلغ إلزامي.",
        "law_ref": "اللائحة المالية 250/2019 — المادة 3",
        "warning": "الصرف لغير المستحق يُعرّض المسؤول للمساءلة القانونية.",
    },
}

# بيانات القوانين الأساسية — تُحمَّل عند التثبيت
SEED_LEGAL_KB = [
    {
        "name": "قانون الموازنة العامة للدولة",
        "law_number": "53/1973",
        "authority": "وزارة المالية",
        "module": "account",
        "source_type": "legal_pdf",
        "content": """
المادة 1: تُعدّ الموازنة العامة للدولة وفق أسلوب الموازنة البرامجية
والأداء اعتباراً من السنة المالية 2018/2019.
المادة 5: لا يجوز الصرف من الخزانة العامة إلا بموجب إذن صرف
معتمد من الوزير المختص أو من يفوضه.
المادة 12: تُقفل حسابات الموازنة في 30 يونيو من كل عام.
المادة 17: لا يجوز تجاوز الاعتمادات المخصصة في الموازنة إلا
بقرار من مجلس الوزراء.
        """,
    },
    {
        "name": "اللائحة المالية للوحدات ذات الطابع الاقتصادي",
        "law_number": "قرار وزاري 250/2019",
        "authority": "وزارة المالية",
        "module": "account",
        "source_type": "ministerial_decree",
        "content": """
المادة 3: يُشترط الحصول على 3 عروض أسعار على الأقل لأي مشتريات
تتجاوز قيمتها خمسة آلاف جنيه.
المادة 8: تُعتمد الفواتير من المدير المالي إذا كانت قيمتها أقل
من عشرة آلاف جنيه، ومن رئيس الجهة إذا تجاوزت ذلك.
المادة 15: يجب توافر الاعتماد المالي قبل إبرام أي التزام مالي.
        """,
    },
    {
        "name": "قانون تنظيم المناقصات والمزايدات",
        "law_number": "89/1998",
        "authority": "الجهاز المركزي للمحاسبات",
        "module": "purchase",
        "source_type": "legal_pdf",
        "content": """
المادة 1: تسري أحكام هذا القانون على جميع عقود التوريد والأشغال
والخدمات التي تُبرمها الجهات الحكومية.
المادة 5: لا يجوز تجزئة الصفقات بقصد التحايل على أحكام هذا القانون.
المادة 11: تُطرح المناقصات العامة لكل عقد تتجاوز قيمته مائة ألف جنيه.
المادة 23: يجب نشر إعلان المناقصة في الجريدة الرسمية أو جريدتين
يوميتين واسعتي الانتشار قبل 15 يوماً من الموعد المحدد للتقدم.
المادة 31: تُقدَّم العروض في مظاريف مختومة ولا تُفتح إلا في
الموعد المحدد وبحضور أصحابها أو من يمثلهم.
        """,
    },
    {
        "name": "قانون الخدمة المدنية",
        "law_number": "81/2016",
        "authority": "وزارة التخطيط والإصلاح الإداري",
        "module": "hr",
        "source_type": "legal_pdf",
        "content": """
المادة 14: ساعات العمل الرسمية 7 ساعات يومياً، 35 ساعة أسبوعياً.
المادة 47: لا يجوز منح إجازة سنوية بأجر كامل تتجاوز 45 يوماً في السنة.
المادة 52: تُحتسب بدلات الانتقال والمهمات وفق جداول ملحقة باللائحة التنفيذية.
المادة 78: توقيع الجزاءات التأديبية يستلزم سماع أقوال الموظف وتحقيق.
المادة 92: يُشترط لترقية الموظف قضاء المدة الزمنية المحددة في درجته
والحصول على تقدير لا يقل عن "جيد".
        """,
    },
    {
        "name": "قانون ضريبة القيمة المضافة",
        "law_number": "67/2016",
        "authority": "مصلحة الضرائب المصرية",
        "module": "account",
        "source_type": "legal_pdf",
        "content": """
المادة 3: نسبة الضريبة العامة على القيمة المضافة 14%.
المادة 7: يلتزم كل مسجل بإصدار فاتورة ضريبية عن كل عملية بيع
أو تقديم خدمة خاضعة للضريبة.
المادة 28: يُقدَّم الإقرار الضريبي الشهري خلال الشهر التالي لانتهاء
الفترة الضريبية.
المادة 38: يُعاقب على التهرب الضريبي بغرامة لا تقل عن 100% من
قيمة الضريبة المستحقة.
        """,
    },
    {
        "name": "قانون المحاسبة الحكومية",
        "law_number": "127/1981",
        "authority": "وزارة المالية — الجهاز المركزي للمحاسبات",
        "module": "account",
        "source_type": "legal_pdf",
        "content": """
المادة 8: يجب توافر 3 مبادئ أساسية في كل قيد محاسبي:
(1) وجود مستند مؤيد، (2) اعتماد من الجهة المختصة، (3) الانتماء
للفترة المالية الصحيحة.
المادة 19: لا يجوز إجراء أي تعديل على القيود المحاسبية المعتمدة
إلا بموجب قيد تسوية معتمد.
المادة 24: تُحفظ المستندات المحاسبية لمدة لا تقل عن خمس سنوات.
        """,
    },
    {
        "name": "لائحة الإجراءات الجمركية للمشتريات الحكومية",
        "law_number": "قرار 160/2020",
        "authority": "الجمارك المصرية — وزارة المالية",
        "module": "stock",
        "source_type": "ministerial_decree",
        "content": """
المادة 2: تُعفى مشتريات الجهات الحكومية من الرسوم الجمركية
بموجب قرار من وزير المالية لكل حالة.
المادة 6: يجب إرفاق شهادة المنشأ مع كل شحنة مستوردة.
المادة 9: تخضع البضائع المستوردة للفحص في مراكز الفحص المعتمدة
قبل الإفراج الجمركي.
        """,
    },
    {
        "name": "قواعد ومعايير المحاسبة الحكومية المصرية",
        "law_number": "قرار وزاري 270/2022",
        "authority": "وزارة المالية",
        "module": "account",
        "source_type": "accounting_standard",
        "content": """
المعيار 1: الاعتراف بالإيرادات الحكومية يتم على أساس الاستحقاق.
المعيار 3: تُصنَّف الأصول الثابتة بحسب طبيعتها وتُهلَك وفق جداول
الإهلاك الصادرة من وزارة المالية.
المعيار 7: الإفصاح عن الالتزامات الطارئة إلزامي في القوائم المالية.
المعيار 12: يُطبَّق مبدأ القيد المزدوج في جميع العمليات المالية.
        """,
    },
]


class KBIndexer(models.AbstractModel):
    """
    خدمة الفهرسة — AbstractModel لأنها لا تحتاج جدولاً في قاعدة البيانات
    يتم الوصول إليها عبر self.env['gov.kb.indexer']
    """
    _name = 'gov.kb.indexer'
    _description = 'فهرس قاعدة المعرفة الحكومية'

    # نجعل FIELD_HINT_CONTEXT متاحاً كـ class attribute
    FIELD_HINT_CONTEXT = FIELD_HINT_CONTEXT

    def _get_embedding_model(self):
        """
        استرجاع نموذج التضمين المحلي
        نستخدم sentence-transformers المتعدد اللغات لدعم العربية
        يُفضَّل النموذج المحلي لتجنب تكلفة API إضافية
        """
        try:
            from sentence_transformers import SentenceTransformer
            # نموذج متعدد اللغات يدعم العربية بشكل ممتاز
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            return model
        except ImportError:
            _logger.warning(
                'gov_ai_guide: sentence-transformers غير مثبت. '
                'سيتم استخدام تضمين مبسّط. '
                'نفّذ: pip install sentence-transformers'
            )
            return None

    def _compute_embedding(self, text: str) -> List[float]:
        """
        حساب المتجه الدلالي لنص معين
        يستخدم sentence-transformers إن توفر، وإلا يعود لتضمين مبسّط
        """
        model = self._get_embedding_model()
        if model:
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        else:
            # تضمين احتياطي مبسّط بناءً على تكرار الكلمات (TF-IDF بسيط)
            return self._simple_embedding(text)

    def _simple_embedding(self, text: str, dim: int = 128) -> List[float]:
        """
        تضمين مبسّط كاحتياطي — يعطي نتائج أقل دقة من sentence-transformers
        يستخدم hash modulo للحصول على متجه ثابت الأبعاد
        """
        import math
        words = re.findall(r'\w+', text.lower())
        vector = [0.0] * dim
        for word in words:
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx = h % dim
            vector[idx] += 1.0
        # تطبيع L2
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """حساب التشابه الجيبي بين متجهين — نستخدم numpy للسرعة"""
        try:
            import numpy as np
            a = np.array(vec_a, dtype=np.float32)
            b = np.array(vec_b, dtype=np.float32)
            dot = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(dot / (norm_a * norm_b))
        except ImportError:
            # احتياطي بدون numpy — أبطأ لكن يعمل
            dot = sum(a * b for a, b in zip(vec_a, vec_b))
            norm_a = sum(x * x for x in vec_a) ** 0.5
            norm_b = sum(x * x for x in vec_b) ** 0.5
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

    def _chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """
        تقسيم النص لقطع بحجم محدد مع تداخل لضمان استمرارية السياق
        chunk_size وoverlap بالكلمات (تقريبياً)
        """
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = ' '.join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            if end >= len(words):
                break
            start += chunk_size - overlap
        return chunks

    def _extract_article_chunks(self, text: str) -> List[str]:
        """
        تقسيم النصوص القانونية بحسب المواد والبنود
        يبحث عن أنماط: "مادة"، "بند"، "فقرة"، "المادة"
        """
        # أنماط بداية المواد في النصوص القانونية العربية
        article_pattern = re.compile(
            r'(?:^|\n)\s*(?:المادة|مادة|البند|بند|الفقرة|فقرة|المعيار|معيار)\s+\d+',
            re.MULTILINE
        )
        positions = [m.start() for m in article_pattern.finditer(text)]

        if not positions:
            # لا توجد مواد — نقسّم كنص عادي
            return self._chunk_text(text)

        chunks = []
        for i, pos in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            article_text = text[pos:end].strip()
            if article_text:
                # إذا كانت المادة طويلة جداً نقسّمها أيضاً
                if len(article_text.split()) > 400:
                    chunks.extend(self._chunk_text(article_text))
                else:
                    chunks.append(article_text)
        return chunks

    @api.model
    def index_addon_source(self, addon_path: str, module_name: str = ''):
        """
        فهرسة كود مصدر addon كامل
        يستخرج: docstrings، help=، string=، _description، عناوين القوائم
        """
        if not os.path.isdir(addon_path):
            return

        extracted = []

        for root, dirs, files in os.walk(addon_path):
            # تجاهل المجلدات غير الضرورية
            dirs[:] = [d for d in dirs if d not in {
                '__pycache__', '.git', 'node_modules', 'static'
            }]

            for filename in files:
                filepath = os.path.join(root, filename)
                if filename.endswith('.py'):
                    extracted.extend(
                        self._extract_from_python(filepath, module_name)
                    )
                elif filename.endswith('.xml'):
                    extracted.extend(
                        self._extract_from_xml(filepath, module_name)
                    )

        # حفظ في قاعدة البيانات
        KBDoc = self.env['gov.kb.document']
        for item in extracted:
            if not item.get('content', '').strip():
                continue
            # تجنب التكرار بناءً على hash المحتوى
            content_hash = hashlib.md5(item['content'].encode('utf-8')).hexdigest()
            existing = KBDoc.search([
                ('source_file', '=', item.get('source_file', '')),
                ('chunk_index', '=', item.get('chunk_index', 0)),
            ], limit=1)

            embedding = self._compute_embedding(item['content'])
            data = {
                'name': item.get('name', f"{module_name}: {filename}"),
                'source_type': 'addon_source',
                'module_name': module_name,
                'model_name': item.get('model_name', ''),
                'field_names': item.get('field_names', ''),
                'content': item['content'],
                'embedding': json.dumps(embedding),
                'source_file': item.get('source_file', ''),
                'chunk_index': item.get('chunk_index', 0),
            }
            if existing:
                existing.write(data)
            else:
                KBDoc.create(data)

    def _extract_from_python(self, filepath: str, module_name: str) -> List[Dict]:
        """استخراج المعلومات الدلالية من ملفات Python"""
        results = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()

            tree = ast.parse(source)
            rel_path = os.path.relpath(filepath)

            for node in ast.walk(tree):
                # استخراج docstrings النماذج والدوال
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    docstring = ast.get_docstring(node)
                    if docstring and len(docstring) > 20:
                        # البحث عن _name في الـ class
                        model_name = ''
                        if isinstance(node, ast.ClassDef):
                            for item in node.body:
                                if isinstance(item, ast.Assign):
                                    for target in item.targets:
                                        if isinstance(target, ast.Name) and target.id == '_name':
                                            if isinstance(item.value, ast.Constant):
                                                model_name = item.value.value

                        chunks = self._chunk_text(docstring)
                        for i, chunk in enumerate(chunks):
                            results.append({
                                'name': f"{rel_path}:{node.name}",
                                'content': f"{node.name}:\n{chunk}",
                                'model_name': model_name,
                                'source_file': rel_path,
                                'chunk_index': i,
                            })

                # استخراج help= و string= من تعريفات الحقول
                if isinstance(node, ast.Call):
                    help_text = self._extract_kwarg(node, 'help')
                    string_text = self._extract_kwarg(node, 'string')
                    if help_text and len(help_text) > 10:
                        combined = f"{string_text or ''}: {help_text}"
                        results.append({
                            'name': f"{rel_path}: field help",
                            'content': combined,
                            'source_file': rel_path,
                            'chunk_index': len(results),
                        })

        except Exception as e:
            _logger.debug('gov_ai_guide: تعذّر تحليل %s: %s', filepath, e)

        return results

    def _extract_kwarg(self, call_node: ast.Call, kwarg_name: str) -> str:
        """استخراج قيمة argument معين من ast.Call"""
        for keyword in call_node.keywords:
            if keyword.arg == kwarg_name and isinstance(keyword.value, ast.Constant):
                return str(keyword.value.value)
        return ''

    def _extract_from_xml(self, filepath: str, module_name: str) -> List[Dict]:
        """استخراج النصوص الدلالية من ملفات XML (views, data)"""
        results = []
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(filepath)
            root = tree.getroot()
            rel_path = os.path.relpath(filepath)

            texts = []
            for elem in root.iter():
                for attr in ('string', 'help', 'name', 'summary'):
                    val = elem.get(attr, '')
                    # نستخرج النصوص العربية فقط (تحتوي على أحرف عربية)
                    if val and re.search(r'[؀-ۿ]', val):
                        texts.append(val)
                # النص المباشر للعناصر
                if elem.text and re.search(r'[؀-ۿ]', elem.text or ''):
                    texts.append(elem.text.strip())

            if texts:
                combined = ' | '.join(texts)
                chunks = self._chunk_text(combined, chunk_size=200)
                for i, chunk in enumerate(chunks):
                    results.append({
                        'name': f"{rel_path}: XML strings",
                        'content': chunk,
                        'source_file': rel_path,
                        'chunk_index': i,
                    })
        except Exception as e:
            _logger.debug('gov_ai_guide: تعذّر تحليل XML %s: %s', filepath, e)

        return results

    @api.model
    def index_legal_pdf(self, file_path: str, metadata: Dict):
        """
        فهرسة وثيقة قانونية PDF
        يستخدم pymupdf لاستخراج النص ثم يقسّمه حسب المواد
        """
        try:
            import fitz  # pymupdf
        except ImportError:
            _logger.error(
                'gov_ai_guide: pymupdf غير مثبت. نفّذ: pip install pymupdf'
            )
            return

        try:
            doc = fitz.open(file_path)
            full_text = ''
            for page in doc:
                full_text += page.get_text('text')
            doc.close()
        except Exception as e:
            _logger.error('gov_ai_guide: فشل فتح PDF %s: %s', file_path, e)
            return

        if not full_text.strip():
            _logger.warning('gov_ai_guide: الملف %s لا يحتوي على نص قابل للاستخراج', file_path)
            return

        # تقسيم بحسب المواد القانونية
        chunks = self._extract_article_chunks(full_text)

        KBDoc = self.env['gov.kb.document']
        for i, chunk in enumerate(chunks):
            if not chunk.strip() or len(chunk) < 20:
                continue
            embedding = self._compute_embedding(chunk)
            KBDoc.create({
                'name': f"{metadata.get('name', 'وثيقة')} — المادة {i + 1}",
                'source_type': metadata.get('source_type', 'legal_pdf'),
                'module_name': metadata.get('module_name', ''),
                'model_name': metadata.get('model_name', ''),
                'content': chunk,
                'embedding': json.dumps(embedding),
                'law_number': metadata.get('law_number', ''),
                'authority': metadata.get('authority', ''),
                'source_file': os.path.basename(file_path),
                'chunk_index': i,
            })

    @api.model
    def search_kb(self, query: str, model_name: str, field_name: str, top_k: int = 5) -> List[Dict]:
        """
        البحث في قاعدة المعرفة بالتشابه الدلالي
        يُعزَّز الترتيب للنتائج التي تطابق model_name أو field_name مباشرةً
        يجب أن ينتهي في < 200ms
        """
        if not query and not field_name:
            return []

        # بناء استعلام مركّب يشمل السياق الكامل
        search_query = f"{model_name}.{field_name}: {query}"
        query_embedding = self._compute_embedding(search_query)

        # استرجاع الوثائق النشطة التي لها embedding
        docs = self.env['gov.kb.document'].search([
            ('active', '=', True),
            ('embedding', '!=', False),
        ])

        if not docs:
            return []

        # حساب التشابه لكل وثيقة — نستخدم numpy لبحث دفعي سريع
        results = []
        try:
            import numpy as np
            query_vec = np.array(query_embedding, dtype=np.float32)
            for doc in docs:
                try:
                    doc_vec = np.array(json.loads(doc.embedding), dtype=np.float32)
                    # التأكد من تطابق الأبعاد
                    if len(doc_vec) != len(query_vec):
                        continue
                    score = float(np.dot(query_vec, doc_vec) / (
                        np.linalg.norm(query_vec) * np.linalg.norm(doc_vec) + 1e-8
                    ))
                    # مكافأة المطابقة المباشرة للنموذج أو الحقل
                    if model_name and doc.model_name == model_name:
                        score += 0.2
                    if field_name and field_name in (doc.field_names or ''):
                        score += 0.2
                    if model_name and doc.module_name == model_name.split('.')[0]:
                        score += 0.1
                    results.append({
                        'id': doc.id,
                        'content': doc.content or '',
                        'law_number': doc.law_number or '',
                        'authority': doc.authority or '',
                        'name': doc.name,
                        'score': score,
                    })
                except (json.JSONDecodeError, Exception):
                    continue
        except ImportError:
            # احتياطي بدون numpy — أبطأ
            for doc in docs:
                try:
                    doc_vec = json.loads(doc.embedding)
                    score = self._cosine_similarity(query_embedding, doc_vec)
                    if model_name and doc.model_name == model_name:
                        score += 0.2
                    results.append({
                        'id': doc.id,
                        'content': doc.content or '',
                        'law_number': doc.law_number or '',
                        'authority': doc.authority or '',
                        'name': doc.name,
                        'score': score,
                    })
                except Exception:
                    continue

        # ترتيب تنازلي وإعادة أفضل top_k نتيجة
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    @api.model
    def load_seed_legal_kb(self):
        """
        تحميل بيانات القوانين الأساسية عند التثبيت
        يتجنب التكرار بالبحث عن law_number موجود
        """
        KBDoc = self.env['gov.kb.document']
        for item in SEED_LEGAL_KB:
            existing = KBDoc.search([
                ('law_number', '=', item['law_number']),
                ('source_type', '=', item.get('source_type', 'legal_pdf')),
            ], limit=1)
            if existing:
                continue  # لا نعيد إنشاء ما هو موجود

            content = item['content'].strip()
            chunks = self._extract_article_chunks(content)
            for i, chunk in enumerate(chunks):
                embedding = self._compute_embedding(chunk)
                KBDoc.create({
                    'name': f"{item['name']} — {i + 1}",
                    'source_type': item.get('source_type', 'legal_pdf'),
                    'module_name': item.get('module', ''),
                    'content': chunk,
                    'embedding': json.dumps(embedding),
                    'law_number': item['law_number'],
                    'authority': item['authority'],
                    'chunk_index': i,
                })
        _logger.info('gov_ai_guide: تم تحميل %d قانون أساسي', len(SEED_LEGAL_KB))

    @api.model
    def reindex_all_addons_cron(self):
        """نقطة الدخول لـ cron الليلي — تُعيد فهرسة كل الـ addons"""
        from odoo.modules.module import get_module_path
        installed = self.env['ir.module.module'].search([('state', '=', 'installed')])
        for module in installed:
            path = get_module_path(module.name, raise_not_found=False)
            if path:
                try:
                    self.index_addon_source(path, module.name)
                except Exception as e:
                    _logger.warning('cron: فشل فهرسة %s: %s', module.name, e)
        _logger.info('gov_ai_guide: اكتملت الفهرسة الليلية')
