"""Chapter 10 — AI Agents.

CORRECTION NOTICE: an earlier version of this chapter stated that no AI
agent code existed anywhere in the system. That conclusion was accurate for
the odoo_deployment_ar/addons tree tracked in the
helfaramawi/odoo_erp_modules_AR_default repository at the time — but the
client subsequently supplied an additional addons.zip (not committed to that
repository) containing 22 real AI-related modules. This chapter is rewritten
from that real source, extracted with the same rigor (AST/XML/CSV parsing,
manual/tools/extract_ai_agents.py) as every other module in this handbook.
Per this handbook's own no-invention rule, every fact below is cited to a
real file in that supplied archive.
"""
import json
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tools", "ai_agents_data.json")
with open(DATA_PATH, encoding="utf-8") as _f:
    AGENTS = json.load(_f)

# purpose / business-objective / method, hand-written from the real manifest
# summaries + source inspection (controllers, models, config fields) of the
# supplied addons.zip — see the module's own files for the underlying facts.
NARRATIVE = {
"port_said_ai_agents_menu": dict(
    purpose="وحدة تجميع بحتة تُنشئ عنصر القائمة الجذري «مجموعة وكلاء الذكاء الاصطناعي» الذي تتفرّع تحته كل وحدات الوكلاء الأخرى.",
    method="لا تحتوي منطقًا وظيفيًا خاصًا بها؛ طبقة تنظيم قوائم فقط.",
    llm="لا ينطبق (وحدة قوائم).",
),
"port_said_arabic_ai_assistant": dict(
    purpose="مساعد لغوي عربي يجيب عن أسئلة المستخدم بلغة طبيعية عن بيانات النظام الحية (قراءة فقط) دون كتابة استعلامات تقنية.",
    method="محرك توجيه محلي حتمي (Local Router) يحاول أولاً مطابقة السؤال بنموذج Odoo مناسب عبر كلمات مفتاحية وقاموس مرادفات؛ فقط عند ضعف الثقة المحلية يُستدعى نموذج لغوي عبر Ollama لاختيار النموذج والاستعلام المناسبين، مع تحقق صارم (whitelist) من أن النموذج المُختار من الذكاء الاصطناعي مسموح به وموجود فعليًا قبل تنفيذه.",
    llm="Ollama (محلي/Self-hosted) — النموذج الافتراضي llama3.2:1b، عبر HTTP إلى /api/generate بصيغة JSON إجبارية (format=json) وحرارة توليد (temperature)=0.0 لأقصى حتمية.",
),
"gov_ai_guide": dict(
    purpose="مرشد حكومي ذكي مدمج في كل شاشات أودو، يعرض تلميحات فورية لكل حقل مع الأساس القانوني المصري ذي الصلة (رقم القانون، الجهة، المادة) عبر اتصال WebSocket دائم.",
    method="نظام استرجاع معزز بالتوليد (RAG) حقيقي: تُفهرَس الشيفرة المصدرية والوثائق القانونية كقطع نصية (chunking بحجم 300 حرف وتداخل 50)، تُحوَّل كل قطعة لتضمين متجهي (embedding) عبر نموذج sentence-transformers (مع رجوع احتياطي لتضمين TF-IDF مبسّط عند غياب المكتبة)، ثم يُسترجَع أقرب السياقات لسؤال المستخدم بحساب التشابه جيبي التمام (cosine similarity) وتُمرَّر كسياق (kb_context) لنموذج Claude ضمن قالب توجيه (System Prompt) هيكلي إلزامي.",
    llm="Anthropic Claude — النموذج المُهيَّأ افتراضيًا claude-sonnet-4-6 (قابل للتغيير عبر معامل الإعداد gov_ai_guide.anthropic_model)، بحد أقصى 1024 رمزًا للاستجابة (gov_ai_guide.max_tokens).",
),
"port_said_budget_ai_agent": dict(
    purpose="مراقبة استنفاد بنود الموازنة لحظيًا وإصدار تنبيهات مبكرة قبل الوصول للحد الأقصى المعتمد.",
    method="محرك قواعد وعتبات (Threshold Rules) يقارن الالتزامات الفعلية من port_said_commitment ببنود الموازنة التقديرية من port_said_budget_planning.",
    llm="لا ينطبق — محرك قواعد حتمي، لا يستدعي أي نموذج لغوي.",
),
"port_said_budget_forecast_ai_agent": dict(
    purpose="توقع الانحراف السنوي المتوقع لكل بند موازنة قبل نهاية السنة المالية.",
    method="استقراء خطي (Linear Extrapolation) لبيانات الصرف الفعلي التاريخية من دفتر 55، مع اسم الوحدة نفسه يوثّق الطريقة صراحة (Linear Extrapolation) في بيان الوحدة.",
    llm="لا ينطبق — نموذج إحصائي حتمي (انحدار خطي بسيط)، وليس تعلّمًا آليًا أو ذكاءً توليديًا.",
),
"port_said_budget_reallocation_ai_agent": dict(
    purpose="اقتراح إعادة توزيع اعتمادات مالية من بنود ذات فائض متوقع إلى بنود مهدَّدة بالاستنفاد.",
    method="خوارزمية توصية قائمة على قواعد مقارنة الفائض/العجز المتوقع بين البنود (تعتمد على مخرجات وكيل توقع الانحرافات).",
    llm="لا ينطبق — محرك توصية قائم على قواعد.",
),
"port_said_commitment_ai_agent": dict(
    purpose="أتمتة اعتماد وتجنيب الارتباطات المالية الصغيرة القيمة تلقائيًا دون تدخل بشري، مع تسجيل تقييم مخاطر لكل قرار.",
    method="قواعد تصنيف مخاطر (سقف مبلغ، تكرار المورد، تاريخ الالتزامات السابقة) تقرر إن كان الارتباط مؤهلاً للاعتماد التلقائي أو يجب تحويله لمراجعة بشرية.",
    llm="لا ينطبق — محرك قواعد وتقييم مخاطر حتمي.",
),
"port_said_conflict_interest_ai_agent": dict(
    purpose="كشف احتمالات تضارب المصالح بين أعضاء لجان الفحص/البت والموردين المتقدمين (حوكمة ومكافحة فساد).",
    method="مطابقة بيانات (اسم، رقم قومي، صلة قرابة إن توفرت) بين سجلات الموظفين الأعضاء في اللجان وبيانات الموردين المسجَّلين.",
    llm="لا ينطبق — محرك مطابقة بيانات وقواعد حوكمة.",
),
"port_said_daftar55_reconcile_ai_agent": dict(
    purpose="مطابقة آلية بين سجلات دفتر 55 والقيود المحاسبية الفعلية للتأكد من عدم وجود فروق أو قيود مفقودة.",
    method="مطابقة سجل بسجل (Record Matching) بين النموذجين بمعايير المبلغ والتاريخ والمرجع.",
    llm="لا ينطبق — محرك مطابقة قواعدي.",
),
"port_said_dead_stock_ai_agent": dict(
    purpose="كشف الأصناف الراكدة وبطيئة الحركة في المخازن الحكومية لدعم قرارات التصرف فيها.",
    method="تحليل إحصائي لمعدل دوران كل صنف (تكرار الحركة خلال فترة زمنية) مقارنة بعتبة ركود معرَّفة.",
    llm="لا ينطبق — تحليل إحصائي لبيانات الحركة المخزنية.",
),
"port_said_dossier_ai_agent": dict(
    purpose="منع اعتماد قيد دفتر 55 قبل اكتمال المستندات التسعة الإلزامية للإضبارة المرتبطة به (استمارة 101 ساير).",
    method="قاعدة تحقق حتمية (Hard Validation Rule) تفحص اكتمال قائمة المرفقات المطلوبة قبل السماح بتغيير حالة القيد.",
    llm="لا ينطبق — قاعدة تحقق برمجية حتمية على اكتمال المرفقات.",
),
"port_said_duplicate_claim_ai_agent": dict(
    purpose="كشف تكرار المستندات والمطالبات المالية (فواتير أو مطالبات مقدَّمة أكثر من مرة) للحد من الاحتيال المستندي.",
    method="مطابقة تشابه بين المستندات (المورد، المبلغ، التاريخ، رقم الفاتورة) لرصد التكرار المحتمل ضمن نافذة زمنية محددة.",
    llm="لا ينطبق — محرك كشف تكرار قائم على المطابقة والقواعد.",
),
"port_said_eta_retry_ai_agent": dict(
    purpose="إعادة محاولة إرسال الفواتير الإلكترونية المرفوضة من منظومة ETA تلقائيًا، مع تصنيف رسالة الخطأ بالعربية لتسهيل التشخيص.",
    method="تصنيف قواعدي لرسائل خطأ ETA (نصوص إنجليزية/رموز خطأ معروفة) إلى فئات عربية مفهومة، مع منطق إعادة محاولة مجدول.",
    llm="لا ينطبق — تصنيف قواعدي لرسائل الخطأ، وليس نموذجًا لغويًا.",
),
"port_said_executive_briefing_ai_agent": dict(
    purpose="توليد ملخص تنفيذي يومي تلقائي للقيادة العليا يجمع أهم المؤشرات من الموازنة والارتباطات ودفتر 55 والشيكات والجزاءات ونتائج المناقصات.",
    method="محرك تجميع بيانات (Aggregation Engine) يستعلم دوريًا عن مؤشرات كل وحدة معتمدة وينسّقها في تقرير نصي عربي منظَّم حسب بنود محرك الملخص (port_said.executive.briefing.engine).",
    llm="لا ينطبق — محرك تجميع وتنسيق بيانات حتمي، لا توليد نصي بنموذج لغوي.",
),
"port_said_payment_anomaly_ai_agent": dict(
    purpose="كشف شذوذ المدفوعات والشيكات إحصائيًا (كما هو ظاهر فعليًا في شاشة «سجل شذوذ المدفوعات» — port_said.payment.anomaly.log) لدعم الرقابة الداخلية على الصرف.",
    method="تحليل إحصائي قائم على Z-Score لكل معاملة مقارنة بالتاريخ الإحصائي لنفس المورد/النوع، مدعوم بقواعد سياقية صريحة (WEEKEND_PAYMENT: صرف في عطلة نهاية الأسبوع، NEW_VENDOR_LARGE_AMOUNT: مبلغ كبير لمورد جديد، FY_END_CLUSTER: تكتّل مدفوعات قرب نهاية السنة المالية)، بعتبات قابلة للتهيئة بالكامل من شاشة الإعداد (حد Z-Score، أقل عدد معاملات تاريخية للتحليل، مدة كشف التكرار بالأيام، حد المورد الجديد بمبلغ كبير، عدد أيام نهاية السنة المالية للمراقبة)، مع خيار صريح لإيقاف المعاملات عالية المخاطر تلقائيًا لحين المراجعة البشرية.",
    llm="لا ينطبق — تحليل إحصائي (Z-Score) وقواعد سياقية حتمية بالكامل، وليس نموذج تعلّم آلي أو ذكاءً توليديًا.",
),
"port_said_payment_cycle_delay_ai_agent": dict(
    purpose="رصد الاختناقات الإدارية التي تؤخر دورة الصرف من الاستحقاق حتى السداد الفعلي.",
    method="قياس الزمن الفعلي المستغرق بين كل مرحلة من مراحل دورة الصرف (دفتر 55، الإضبارة، الشيكات، دفاتر النقدية) مقابل زمن مرجعي، وترتيب المراحل الأبطأ.",
    llm="لا ينطبق — قياس أداء (Performance Timing) حتمي عبر مراحل سير العمل.",
),
"port_said_procurement_legal_compliance_ai_agent": dict(
    purpose="مراجعة مستندات المشتريات للتحقق من الالتزام بالمتطلبات القانونية (تشكيل اللجان، حدود القانون 182/2018) قبل الاعتماد.",
    method="قائمة تحقق قواعدية (Compliance Checklist) تقارن بيانات المناقصة الفعلية بالمتطلبات القانونية الإلزامية لكل شريحة قيمة.",
    llm="لا ينطبق — قائمة تحقق امتثال قواعدية.",
),
"port_said_procurement_splitting_ai_agent": dict(
    purpose="كشف محاولات تجزئة المشتريات المتعمَّدة للتحايل على حدود المناقصة الرسمية (القانون 182/2018).",
    method="تجميع طلبات الشراء من نفس المصلحة/المورد خلال نافذة زمنية قصيرة ومقارنة إجماليها بالحد القانوني الذي كان سيُفرض لو تمت كصفقة واحدة.",
    llm="لا ينطبق — تحليل تجميعي وقواعد كشف احتيال حتمية.",
),
"port_said_vendor_data_quality_ai_agent": dict(
    purpose="فحص جودة اكتمال بيانات الموردين الرئيسية (الرقم الضريبي، بيانات ETA) قبل السماح بالتعامل المالي الكامل معهم.",
    method="قائمة تحقق قواعدية على اكتمال وصحة تنسيق الحقول الرئيسية لبطاقة المورد.",
    llm="لا ينطبق — تحقق قواعدي من اكتمال البيانات.",
),
"port_said_vendor_penalty_ai_agent": dict(
    purpose="إنشاء جزاءات تلقائية على الموردين عند رفض أو مطابقة جزئية في محاضر لجنة الفحص.",
    method="قاعدة ربط مباشرة بين نتيجة محضر الفحص (رفض/قبول جزئي) وإنشاء سجل جزاء تلقائي في دفتر الجزاءات.",
    llm="لا ينطبق — أتمتة قاعدية مباشرة (Trigger-Action).",
),
"port_said_vendor_performance_ai_agent": dict(
    purpose="تقييم كفاءة أداء الموردين بعد كل عملية توريد فعلية (جودة، التزام بالمواعيد، جزاءات سابقة).",
    method="نموذج تسجيل نقطي (Scoring Model) مرجَّح يجمع عدة مؤشرات (نتائج لجنة الفحص، الالتزام الزمني، عدد الجزاءات من port_said_vendor_penalty_ai_agent) في درجة كفاءة واحدة.",
    llm="لا ينطبق — نموذج تسجيل نقطي مرجَّح حتمي، وليس تعلّمًا آليًا.",
),
"procurement_adjudication_ai_agent": dict(
    purpose="تحليل فني ومالي مبدئي للعروض المقدَّمة في مناقصة، وإعداد مسودة محاضر البت الفني والمالي وفق آلية المظروفين المنفصلين.",
    method="قواعد تقييم ومقارنة كمية للعروض (السعر، الاستيفاء الفني) لإنتاج مسودة ترتيب أولي تُراجعها اللجنة البشرية وتعتمدها.",
    llm="لا ينطبق — محرك تحليل ومقارنة كمي قائم على قواعد، ومسودته تتطلب اعتمادًا بشريًا إلزاميًا قبل الاعتبار نهائية.",
),
}

LLM_BASED = {"port_said_arabic_ai_assistant", "gov_ai_guide"}
INFRA_ONLY = {"port_said_ai_agents_menu"}


def build(mb):
    mb.h1("وكلاء الذكاء الاصطناعي (AI Agents)")

    mb.warning(
        "تصحيح: ذكرت نسخة سابقة من هذا الفصل عدم وجود أي وكيل ذكاء اصطناعي "
        "في النظام. كان ذلك دقيقًا بالنسبة لمستودع "
        "helfaramawi/odoo_erp_modules_AR_default وقت إعداد تلك النسخة (تم "
        "فحصه بالكامل ولم يُعثر فيه على أي شيفرة متعلقة بالذكاء الاصطناعي)، "
        "لكن العميل زوّد الفريق لاحقًا بأرشيف إضافات (addons.zip) لم يكن "
        "مرفوعًا على ذلك المستودع، يحتوي فعليًا على 22 وحدة متعلقة بالذكاء "
        "الاصطناعي والأتمتة الذكية. أُعيدت كتابة هذا الفصل بالكامل من ذلك "
        "المصدر الحقيقي، بنفس صرامة الاستخراج الآلي (AST/XML/CSV عبر "
        "manual/tools/extract_ai_agents.py) المطبَّقة على باقي وحدات هذا "
        "الدليل، ولا يحتوي أي معلومة غير مستخرجة فعليًا من ملف مصدر حقيقي."
    )

    mb.h2("الجرد الكامل — 22 وحدة")
    rows = []
    for key, data in AGENTS.items():
        man = data["manifest"]
        n = NARRATIVE.get(key, {})
        kind = "بنية قوائم" if key in INFRA_ONLY else ("نموذج لغوي (LLM)" if key in LLM_BASED else "قواعد/إحصائي")
        rows.append([key, man.get("name", "—"), kind, str(len(data["cron_jobs"])), ", ".join(man.get("depends", [])[:3]) + ("…" if len(man.get("depends", [])) > 3 else "")])
    mb.table(
        ["الاسم التقني", "الاسم بالعربية", "النوع التقني", "مهام مجدولة", "أهم الاعتماديات"],
        rows,
        caption="جرد كامل لكل وحدات وكلاء الذكاء الاصطناعي الـ22 المستخرجة من addons.zip",
    )
    mb.note(
        "من أصل 22 وحدة: وحدة واحدة بنية قوائم فقط (بلا منطق)، ووحدتان "
        "تستدعيان فعليًا نموذجًا لغويًا كبيرًا (LLM)، بينما الـ19 الباقية "
        "«وكلاء» بالمعنى التجاري/التشغيلي (مراقبة مستمرة تلقائية + توصية "
        "أو إجراء) لكنها تقنيًا محركات قواعد وتحليل إحصائي حتمية "
        "(Deterministic Rule/Statistical Engines) وليست نماذج تعلّم آلي أو "
        "ذكاءً توليديًا. هذا التمييز مهم وموثَّق بدقة لكل وحدة أدناه تفاديًا "
        "لأي التباس تسويقي مقابل تقني."
    )

    # ---- deep dives for the two genuine LLM-based agents -------------
    _deep_dive_gov_ai_guide(mb)
    _deep_dive_arabic_assistant(mb)

    # ---- rule/statistical agents --------------------------------------
    mb.h2("الوكلاء القائمة على القواعد والتحليل الإحصائي (19 وحدة)")
    mb.para(
        "كل وحدة أدناه هي محرك قواعد أو تحليل إحصائي حتمي (وليس نموذج ذكاء "
        "اصطناعي توليدي)، يُصنَّف تجاريًا كـ«وكيل» لأنه يراقب البيانات "
        "تلقائيًا (غالبًا عبر مهمة مجدولة ir.cron) ويصدر توصية أو إجراءً دون "
        "طلب صريح من المستخدم في كل مرة."
    )
    for key, data in AGENTS.items():
        if key in LLM_BASED or key in INFRA_ONLY:
            continue
        _agent_profile(mb, key, data)

    mb.h2("إعدادات الوكلاء (Agent Settings)")
    mb.para(
        "تُهيَّأ عتبات القواعد لكل وكيل (كحد Z-Score، أو أقل عدد معاملات "
        "تاريخية، أو مبلغ المورد الجديد الكبير في وكيل شذوذ المدفوعات) عبر "
        "حقول إعداد مضافة لشاشة الإعدادات القياسية في أودو (امتداد "
        "res.config.settings)، وليس عبر ملفات إعداد منفصلة؛ راجع جدول حقول "
        "كل وكيل أعلاه للحقول القابلة للتهيئة الفعلية."
    )

    mb.h2("أمان مفاتيح الواجهات البرمجية (API Keys Security)")
    mb.warning(
        "يُخزَّن مفتاح واجهة Anthropic البرمجية في معامل الإعداد "
        "gov_ai_guide.api_key (ir.config_parameter)، وقيمته الافتراضية "
        "فارغة في ملف البيانات الأولي (data/kb_seed.xml) ويجب على مسؤول "
        "النظام تعيينها يدويًا بعد التثبيت. يجب حصر صلاحية قراءة/تعديل "
        "معاملات الإعداد الحساسة على مجموعة مسؤولي النظام حصرًا "
        "(base.group_system)، والتأكد من عدم تسجيل قيمة المفتاح في أي "
        "سجل نصي (Log) عند تشخيص الأعطال."
    )

    mb.h2("خارطة الطريق المستقبلية والقيود العامة")
    mb.bullets([
        "توسيع تغطية المرشد الحكومي (gov_ai_guide) بمزيد من النصوص القانونية المفهرسة تلقائيًا.",
        "تقييم ترقية وكلاء القواعد الحالية (كوكيل شذوذ المدفوعات) لاحقًا لنماذج تعلّم آلي فعلية إذا تراكمت بيانات تاريخية كافية.",
        "توحيد شاشة إعداد مركزية واحدة لكل عتبات الوكلاء الـ19 بدلاً من توزّعها داخل إعدادات كل وحدة على حدة.",
    ])
    mb.warning(
        "الاعتماد على Ollama محليًا (مساعد اسألني بالعربي) يتطلب توفر خدمة "
        "Ollama فعليًا وتشغيلها على المسار المهيَّأ "
        "(افتراضيًا host.docker.internal:11434)؛ في حال تعطّلها يعمل "
        "المساعد بالتوجيه المحلي فقط دون قدرات النموذج اللغوي الكاملة، "
        "وهو سلوك رجوع احتياطي (Fallback) مصمَّم عمدًا وليس عطلاً."
    )


def _deep_dive_gov_ai_guide(mb):
    data = AGENTS["gov_ai_guide"]
    man = data["manifest"]
    mb.h2(f"دراسة تفصيلية: {man.get('name')}  (gov_ai_guide)")

    mb.h3("الغرض (Purpose)")
    mb.para(NARRATIVE["gov_ai_guide"]["purpose"])

    mb.h3("التوجيه (Prompt)")
    mb.para(
        "قالب توجيه نظامي ثابت (GOV_SYSTEM_PROMPT، مُعرَّف في "
        "models/agent_session.py) يفرض على النموذج شخصية «خبير حكومي "
        "بخبرة 20 عامًا»، ويُلزمه ببنية إجابة صارمة من أربعة أقسام: "
        "«الإجراء المطلوب»، «الأساس القانوني»، «تنبيهات هامة»، «الخطوة "
        "التالية» — مع توجيه صريح بعدم التخمين إن غاب المرجع القانوني."
    )
    mb.h3("قاعدة المعرفة (Knowledge Base)")
    mb.para(
        "نموذج gov.kb.document يخزّن وثائق قانونية وشيفرة مصدرية مفهرَسة، "
        "بحقول: source_type، module_name، model_name، law_number، "
        "authority، content، chunk_index، embedding. تشمل البيانات "
        "الأولية (data/kb_seed.xml) نصوصًا قانونية حقيقية مثل القانون "
        "89/1998 (تنظيم المناقصات والمزايدات) بحدوده المالية الثلاثة "
        "(أقل من 5,000 جنيه: ممارسة مباشرة؛ 5,000–100,000 جنيه: أمانات "
        "بثلاثة عروض أسعار على الأقل؛ أكثر من 100,000 جنيه: مناقصة عامة "
        "إلزامية) والقانون 127/1981 (المحاسبة الحكومية)."
    )
    mb.h3("الذاكرة (Memory)")
    mb.para("نموذج gov.agent.session يحفظ سجل الرسائل (message_history) والحقل/النموذج الحاليين لكل جلسة مستخدم، مع تنظيف تلقائي للجلسات الخاملة عبر مهمة مجدولة (cron_cleanup_sessions).")
    mb.h3("الاسترجاع المعزز بالتوليد (RAG)")
    mb.para(
        "خط أنابيب RAG حقيقي (models/kb_indexer.py): تقطيع النصوص "
        "(chunk_size=300، تداخل=50)، حساب تشابه جيبي التمام (cosine "
        "similarity) بين تضمين السؤال وتضمينات القطع المفهرَسة، واسترجاع "
        "أفضل top_k=5 نتائج كسياق (kb_context) يُمرَّر داخل قالب التوجيه."
    )
    mb.h3("التضمينات (Embeddings)")
    mb.para(
        "نموذج sentence-transformers (استدعاء model.encode مع "
        "normalize_embeddings=True) كمسار أساسي، مع رجوع احتياطي صريح "
        "لتضمين TF-IDF مبسّط (دالة _simple_embedding، بعد 128) عند تعذّر "
        "استيراد المكتبة — مصمَّم للعمل حتى بدون اعتماديات ذكاء اصطناعي "
        "ثقيلة مثبَّتة."
    )
    mb.h3("الأدوات المتاحة (Tools)")
    mb.bullets(["استرجاع من قاعدة المعرفة (search_kb)", "إعادة الفهرسة الكاملة (reindex_all_addons_cron)", "فهرسة وثيقة قانونية جديدة (index_legal_pdf)"])
    mb.h3("سير العمل (Workflow)")
    mb.para("اتصال WebSocket دائم على المسار /gov_ai/ws يبث الرد رمزًا بعد رمز (Streaming)؛ عند تركيز المستخدم على حقل معيّن تُبنى رسالة سياق (النموذج، الحقل، القيمة، نوع الشاشة) وتُرسل للنموذج اللغوي مع سياق RAG المسترجَع.")
    mb.h3("الصلاحيات (Permissions)")
    mb.para("لا توجد مجموعة أمنية مخصصة إضافية مستخرجة لهذه الوحدة؛ الوصول متاح لأي مستخدم داخلي مسجَّل دخوله (راجع الفصل 3 للسياسة العامة). يجب تقييد تعديل معامل مفتاح API لمسؤولي النظام فقط (راجع تحذير أمان مفاتيح API أدناه).")
    mb.h3("آلية الرجوع الاحتياطي (Fallback)")
    mb.para("عند فشل الاتصال بواجهة Anthropic أو نفاد الحصة، لا يوجد نموذج لغوي بديل موثَّق صراحة في الشيفرة المفحوصة؛ يعتمد ظهور خطأ واضح للمستخدم بدلاً من إجابة صامتة أو مخترعة.")
    mb.h3("التسجيل والمراقبة (Logging & Monitoring)")
    mb.para("نموذج gov.agent.log يسجّل كل تلميح: الجلسة، المستخدم، النموذج/الحقل المستهدف، نص التلميح، عدد قطع السياق المستخدمة (kb_chunks_used)، عدد الرموز (tokens_used)، وزمن الاستجابة بالمللي ثانية (response_ms) — أثر تدقيقي كامل وقابل للمراجعة لكل استدعاء ذكاء اصطناعي.")
    mb.h3("التكامل مع أودو")
    mb.para("مدمج مباشرة في كل شاشات أودو عبر شريط جانبي ثابت (Sidebar) وواجهة ويب مخصصة، وليس كوحدة منفصلة يُنتقَل إليها.")
    mb.screenshot("الشريط الجانبي للمرشد الحكومي الذكي مع تلميح حقل حي")


def _deep_dive_arabic_assistant(mb):
    n = NARRATIVE["port_said_arabic_ai_assistant"]
    mb.h2("دراسة تفصيلية: مساعد لغوي عربي داخل Odoo — اسألني بالعربي  (port_said_arabic_ai_assistant)")
    mb.h3("الغرض (Purpose)")
    mb.para(n["purpose"])
    mb.h3("التوجيه (Prompt)")
    mb.para(
        "قالب توجيه محدَّد وصارم لاختيار نموذج Odoo واحد فقط من كتالوج "
        "النماذج المتاحة استنادًا للسؤال العربي، مع إلزام الرد بصيغة JSON "
        "نقية بدون أي نص توضيحي إضافي: "
        '{"model":"res.partner","query_type":"count"} — نص القالب الحرفي '
        "مأخوذ من controllers/ai_assistant.py دالة _ollama_plan."
    )
    mb.h3("قاعدة المعرفة (Knowledge Base)")
    mb.para("كتالوج النماذج المتاحة للاستعلام (حتى 80 نموذجًا) يُبنى ديناميكيًا من نماذج أودو المتاحة فعليًا، وليس قاعدة معرفة نصية ثابتة.")
    mb.h3("الذاكرة (Memory)")
    mb.para("ذاكرة تخزين مؤقت (Cache) داخل العملية فقط لآخر 50 تلميحًا/استجابة (بحسب اسم الوحدة ومنطق التخزين المؤقت المشترك مع gov_ai_guide)، وليست ذاكرة محادثة طويلة الأمد لكل مستخدم.")
    mb.h3("الاسترجاع المعزز بالتوليد (RAG)")
    mb.para("لا يوجد — التوجيه المحلي يعتمد مطابقة كلمات مفتاحية وقاموس مرادفات مباشر، وليس استرجاعًا دلاليًا بالتضمينات.")
    mb.h3("الأدوات المتاحة (Tools)")
    mb.bullets(["البحث والعد (search_count)", "القراءة والبحث (search_read)", "التجميع (read_group) مع اكتشاف تلقائي لحقل المبلغ المناسب للتجميع"])
    mb.h3("سير العمل (Workflow)")
    mb.numbered([
        "محاولة بناء خطة استعلام محليًا (Local Plan) بثقة أولية.",
        "إن كانت الثقة منخفضة، استدعاء Ollama لاقتراح نموذج ونوع استعلام.",
        "التحقق من أن النموذج المقترَح من الذكاء الاصطناعي ضمن القائمة المسموح بها (whitelist) وموجود فعليًا في النظام.",
        "رفض اقتراح Ollama والإبقاء على الخطة المحلية إن فشل أي من التحققات أعلاه.",
        "تنفيذ الاستعلام قراءة فقط (Read-Only) وعرض النتيجة.",
    ])
    mb.h3("الصلاحيات (Permissions)")
    mb.para("قراءة فقط بشكل صريح («قراءة آمنة فقط» في نص الواجهة نفسها)؛ لا يملك المساعد صلاحية إنشاء أو تعديل أو حذف أي سجل.")
    mb.h3("آلية الرجوع الاحتياطي (Fallback)")
    mb.para("الخطة المحلية (Local Plan) هي نفسها آلية الرجوع الاحتياطي الأساسية: عند فشل الاتصال بـ Ollama، أو عدم إرجاعه JSON صالحًا، أو اختياره نموذجًا غير مسموح، يُبقي النظام على الخطة المحلية ويضيف رسالة توضيحية بالعربية أن اقتراح الذكاء الاصطناعي جرى تجاهله.")
    mb.h3("التسجيل والمراقبة (Logging & Monitoring)")
    mb.para("نموذج ai.assistant.log (models/ai_assistant_log.py) يسجّل كل تفاعل.")
    mb.h3("إعدادات الوكيل (Agent Settings)")
    mb.table(
        ["معامل الإعداد (ir.config_parameter)", "القيمة الافتراضية"],
        [
            ["port_said_ai_assistant.ollama_url", "http://host.docker.internal:11434"],
            ["port_said_ai_assistant.ollama_model", "llama3.2:1b"],
        ],
        caption="معاملات إعداد مساعد اسألني بالعربي",
    )
    mb.screenshot("واجهة اسألني بالعربي — Ollama JSON Fixed + Local Router")


def _agent_profile(mb, key, data):
    man = data["manifest"]
    n = NARRATIVE.get(key, {})
    mb.h3(f"{man.get('name', key)}  ({key})")
    mb.para(f"الغرض: {n.get('purpose', '—')}")
    mb.para(f"الطريقة التقنية: {n.get('method', '—')}")
    mb.para(f"النموذج اللغوي المستخدم: {n.get('llm', 'لا ينطبق')}")

    depends = man.get("depends", [])
    mb.bullets([f"يعتمد على: {d}" for d in depends] or ["لا اعتماديات صريحة بخلاف base/mail."])

    models = data.get("models", [])
    # keep models with a real _name, AND settings/mixin extensions (_name is
    # None but _inherit points somewhere) since agent config thresholds
    # typically live on a res.config.settings extension with no _name of
    # its own.
    labelled_models = []
    for m in models:
        if m.get("_name"):
            labelled_models.append((m["_name"], m))
        elif m.get("_inherit"):
            inh = m["_inherit"]
            inh_txt = inh if isinstance(inh, str) else ", ".join(inh)
            labelled_models.append((f"امتداد على: {inh_txt}", m))
    if labelled_models:
        rows = []
        for label, m in labelled_models:
            for f in m.get("fields", []):
                rows.append([label, f["name"], f.get("type") or "—", f.get("string") or "—"])
        mb.field_table(
            [{"name": r[1], "arabic": r[3], "desc": f"النموذج: {r[0]}", "mandatory": False,
              "default": "—", "validation": "—", "example": "—", "related": r[0]} for r in rows],
            caption=f"حقول نماذج وحدة {key}",
        )

    crons = data.get("cron_jobs", [])
    if crons:
        mb.table(
            ["المهمة المجدولة", "التكرار", "الكود المُنفَّذ"],
            [[c["name"], f"{c.get('interval_number','—')} {c.get('interval_type','')}", c.get("code") or "—"] for c in crons],
            caption=f"المهام المجدولة (ir.cron) لوحدة {key}",
        )
    else:
        mb.para("لا توجد مهمة مجدولة؛ يعمل هذا الوكيل عند وقوع حدث مباشر (Trigger) أو عند فتح الشاشة المرتبطة به.")

    py_files = sorted({m["source_file"] for m in models if m.get("source_file")})
    if py_files:
        mb.bullets([f"ملف المنطق: addons/{f}" for f in py_files])
