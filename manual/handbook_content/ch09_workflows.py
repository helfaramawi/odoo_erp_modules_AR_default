"""Chapter 9 — Workflows (BPMN-style documentation)."""
from handbook_meta import NOT_FOUND


def build(mb):
    mb.h1("سير العمل — توثيق بأسلوب BPMN (Workflow Documentation)")
    mb.para(
        "توثّق كل عملية أدناه بأسلوب مخطط BPMN الوصفي (أطراف فاعلة، مدخلات، "
        "مخرجات، خطوات، نقاط قرار، موافقات، معالجة استثناءات)، مستنِدة إلى "
        "حقول الحالة (state) الفعلية المستخرجة من الشيفرة المصدرية حيثما "
        "وُجدت، وليس إلى افتراض عام لسير عمل أودو القياسي."
    )

    mb.workflow_doc("المحاسبة (Accounting Workflow)", dict(
        actors=["المحاسب", "المدير المالي"],
        inputs=["مستند مصدر (فاتورة، دفعة، حركة مخزون)"],
        outputs=["قيد يومية مرحّل في الأستاذ العام"],
        steps=["إنشاء القيد (مسودة)", "التحقق من توازن مدين/دائن والأبعاد المالية الإلزامية", "الترحيل (يدويًا أو عبر الترحيل الدفعي الليلي — c2_batch_posting)"],
        decision_points=["هل القيد متوازن؟", "هل الأبعاد المالية الإلزامية مكتملة (x_requires_department/project/region)؟"],
        approvals="لا يوجد مسار موافقة متعدد المراحل على القيد اليدوي القياسي نفسه؛ الرقابة الفعلية تتم مسبقًا عبر محرك الارتباطات.",
        exception_handling="القيود التي تفشل التحقق تبقى في حالة مسودة وتُسجَّل في سجل استثناءات الترحيل الدفعي الليلي.",
        related_configuration="راجع الفصل 4 — دليل الحسابات ودفاتر اليومية.",
        related_models=["account.move", "account.move.line"],
        related_reports=["ميزان المراجعة", "دفتر الأستاذ العام"],
    ))

    mb.workflow_doc("المشتريات (Purchase Workflow)", dict(
        actors=["المصلحة الطالبة", "لجنة الفحص/البت", "المورد"],
        inputs=["طلب احتياج معتمد"],
        outputs=["أمر توريد معتمد + استمارة 50"],
        steps=["طلب احتياج (port_said_scm_requisition)", "ارتباط بالموازنة تلقائي", "طلب عروض أسعار", "تشكيل لجنة (procurement_committee)", "الترسية", "أمر توريد", "جسر تلقائي لاستمارة 50 (port_said_scm_purchase_bridge)"],
        decision_points=["هل الارتباط بالموازنة معتمد؟", "هل تتطلب القيمة مناقصة رسمية بمظروفين (procurement_adjudication)؟"],
        approvals="مصفوفة موافقات متدرجة حسب القيمة (c1_purchase_approval_matrix) — راجع سير عمل «اعتماد المشتريات» أدناه.",
        exception_handling="رفض الارتباط عند تجاوز رصيد بند الموازنة المتاح.",
        related_models=["port_said.requisition", "port_said.commitment"],
        related_configuration="راجع الفصل 5 — التدبير والمشتريات.",
    ))

    mb.workflow_doc("المخزون (Inventory Workflow)", dict(
        actors=["أمين المخزن", "لجنة الفحص"],
        inputs=["أصناف واردة من مورد أو مصلحة"],
        outputs=["رصيد مخزون محدَّث في الموقع الهدف"],
        steps=["فحص لجنة الفحص (نموذج 12)", "إذن الإضافة (نموذج 1)", "تحديث الرصيد", "قيد محاسبي تلقائي (port_said_stock_finance_bridge)"],
        related_models=["stock.addition.permit", "port_said.inspection.committee"],
        related_configuration="راجع الفصل 5 — المخزون والمستودعات.",
    ))

    mb.workflow_doc("المخازن (Warehouse Workflow)", dict(
        actors=["أمين المخزن", "مدير المخازن", "لجنة الجرد"],
        inputs=["طلب صرف من مصلحة، أو موعد جرد دوري"],
        outputs=["إذن صرف/ارتجاع/تحويل منفَّذ، أو محضر جرد معتمد"],
        steps=["إصدار الإذن (port_said_scm_issue)", "تحديث الرصيد في الموقعين المصدر والهدف", "تحديث سجل العُهدة إن كان الصنف مستديمًا"],
        related_models=["custody.assignment"],
        related_security="راجع الفصل 3 — مجموعات أمين المخزن ومدير المخازن.",
    ))

    mb.workflow_doc("تسجيل الموردين (Vendor Registration Workflow)", dict(
        actors=["إدارة المشتريات", "المورد"],
        inputs=["بيانات المورد (الرقم الضريبي، شروط الدفع)"],
        outputs=["بطاقة مورد معتمدة"],
        steps=["إدخال بيانات المورد", "التحقق من الرقم الضريبي (مطلوب لتكامل ETA — راجع l10n_eg_eta_invoice)", "اعتماد البطاقة"],
        decision_points=["هل البيانات الضريبية مكتملة لإصدار فواتير إلكترونية لاحقًا؟"],
        exception_handling="رفض الفاتورة الإلكترونية لاحقًا إذا كانت بيانات المورد الضريبية ناقصة عند التسجيل.",
        related_configuration="راجع الفصل 5 — إعداد الموردين.",
    ))

    mb.workflow_doc("اعتماد المشتريات (Purchase Approval Workflow)", dict(
        actors=["مُعِدّ الطلب", "مستويات الاعتماد المتدرجة حسب القيمة"],
        inputs=["أمر شراء بقيمة محددة"],
        outputs=["أمر شراء معتمد قابل للإرسال للمورد"],
        steps=["تأكيد أمر الشراء", "حساب القيمة الإجمالية", "توجيه تلقائي لمسار الاعتماد المناسب حسب السقف المالي (c1_purchase_approval_matrix)", "اعتماد كل مستوى مطلوب"],
        decision_points=["هل القيمة تتجاوز سقف المستوى الأول؟ الثاني؟ وهكذا."],
        approvals="مستويات متعددة حسب جدول السقوف المالية المعتمد (القيم الفعلية: " + NOT_FOUND + ")",
        related_models=["[نموذج مصفوفة الاعتماد — c1_purchase_approval_matrix]"],
        related_configuration="odoo_deployment_ar/addons/c1_purchase_approval_matrix/models/*.py",
    ))

    mb.workflow_doc("استلام البضائع (Goods Receipt Workflow)", dict(
        actors=["لجنة الفحص", "أمين المخزن"],
        inputs=["شحنة واردة من مورد مرتبطة بأمر توريد"],
        outputs=["إذن إضافة معتمد (نموذج 1) ورصيد مخزون محدَّث"],
        steps=["فحص لجنة الفحص للشحنة ومطابقتها بالمواصفات (نموذج 12 — port_said_scm_warehouse)", "قرار القبول الكلي/الجزئي/الرفض", "إذن الإضافة للأصناف المقبولة فقط (نموذج 1 — stock_addition_permit)"],
        decision_points=["هل الشحنة مطابقة للمواصفات التعاقدية بالكامل، جزئيًا، أم مرفوضة؟"],
        exception_handling="الأصناف المرفوضة فنيًا لا تدخل رصيد المخزون الرسمي ولا يُصدر لها إذن إضافة.",
        related_models=["stock.addition.permit", "stock.inspection.report"],
        related_reports=["محضر الفحص", "إذن إضافة — نموذج 1 مخازن حكومية"],
    ), screenshot_desc="مخطط تدفق استلام البضائع (Goods Receipt)")

    mb.workflow_doc("التحويل المخزني (Inventory Transfer Workflow)", dict(
        actors=["أمين المخزن المُرسل", "أمين المخزن المستلم"],
        inputs=["طلب تحويل بين مخزنين حكوميين"],
        outputs=["رصيد محدَّث في كلا الموقعين"],
        steps=["إصدار إذن تحويل (port_said_scm_issue)", "خصم الرصيد من المخزن المصدر", "إضافة الرصيد للمخزن الهدف"],
        related_models=["[نموذج إذن التحويل — port_said_scm_issue]"],
    ))

    mb.workflow_doc("تسوية المخزون (Inventory Adjustment Workflow)", dict(
        actors=["أمين المخزن", "مفتش المخزن", "لجنة الجرد"],
        inputs=["نتائج الجرد الفعلي مقارنة بالرصيد الدفتري"],
        outputs=["تسوية معتمدة (فائض/عجز) أو إجراء إعدام معتمد (نموذج 4)"],
        steps=["الجرد الفعلي (نموذج 6 — stock_stocktaking_eg)", "حساب الفروق", "تسوية الفروق البسيطة", "أو إجراء إعدام رسمي منفصل للأصناف التالفة (نموذج 4)"],
        decision_points=["هل الفرق تسوية عادية أم يستوجب إعدامًا رسميًا؟"],
        approvals="إجراء الإعدام (نموذج 4) يتطلب اعتمادًا من مستوى إداري أعلى من أمين المخزن.",
        related_models=["stock.stocktaking.session"],
        related_security="راجع الفصل 3 — مجموعات أمين المخزن/مفتش المخزن/مدير المخازن/لجنة الجرد.",
    ))

    mb.workflow_doc("فواتير الموردين (Vendor Bills Workflow)", dict(
        actors=["المحاسب", "المدير المالي"],
        inputs=["فاتورة مورد مرتبطة باستمارة 50/دفتر 55"],
        outputs=["قيد محاسبي (دائن حساب المورد)"],
        steps=["استلام الفاتورة", "مطابقتها باستمارة 50", "تسجيلها في دفتر 55", "ترحيلها محاسبيًا"],
        related_configuration="راجع الفصل 6 — port_said_daftar55 وport_said_scm_purchase_bridge.",
    ))

    mb.workflow_doc("الدفع (Payment Workflow)", dict(
        actors=["المحاسب", "أمين الصندوق/الخزينة"],
        inputs=["فاتورة مستحقة السداد"],
        outputs=["دفعة مسجَّلة ومطابَقة"],
        steps=["فتح سجل الدفعات من الفاتورة", "تحديد المبلغ ووسيلة الدفع (نقدًا/شيك/تحويل)", "التأكيد", "المطابقة التلقائية أو اليدوية (c4_payment_matching)"],
        decision_points=["هل يستحق المورد خصم سداد مبكر؟ (c4_payment_matching)"],
        related_configuration="راجع الفصل 6 — port_said_cheques وport_said_cash_books وc4_payment_matching.",
    ))

    mb.workflow_doc("ترحيل القيود (Journal Posting Workflow)", dict(
        actors=["المحاسب", "مهمة مجدولة ليلية (c2_batch_posting)"],
        inputs=["قيود يومية في حالة مسودة"],
        outputs=["قيود مرحّلة نهائيًا"],
        steps=["إنشاء القيد", "التحقق اليدوي أو الانتظار للترحيل الدفعي الليلي", "الترحيل"],
        exception_handling="القيود التي تحتوي أخطاء تحقق تبقى في حالة مسودة وتُسجَّل في سجل استثناءات يراجعه المحاسب صباحًا.",
        related_configuration="odoo_deployment_ar/addons/c2_batch_posting/models/*.py — ir.cron: ir_cron_batch_posting (يومي)",
    ))

    mb.workflow_doc("إقفال الفترة (Period Closing Workflow)", dict(
        actors=["مُعِدّ الحساب الشهري", "المراجع", "المعتمِد النهائي"],
        inputs=["حسبة يومية مجمّعة (استمارة 69) لكل أيام الشهر"],
        outputs=["حساب شهري/ختامي معتمد نهائيًا (استمارة 75) وتاريخ قفل جديد"],
        steps=["إعداد الحساب الشهري (حالة «إعداد»)", "المراجعة (حالة «مراجعة»)", "الاعتماد النهائي (حالة «اعتماد نهائي»)", "تحديد تاريخ القفل"],
        decision_points=["هل تم استيفاء كل مرحلة قبل الانتقال للتالية؟ (تسلسل صارم لا يقبل التخطي)"],
        approvals="ثلاث مراحل اعتماد متسلسلة إلزامية (port_said_form75).",
        exception_handling="لا يمكن تعديل قيد في فترة مقفلة إلا بفتح تاريخ القفل استثنائيًا بصلاحية خاصة.",
        related_models=["port_said.form75", "port_said.form69"],
    ), screenshot_desc="مخطط تسلسل اعتماد الإقفال الشهري (3 مراحل)")

    mb.workflow_doc("إدارة الأصول (Asset Management Workflow)", dict(
        actors=["المحاسب", "مدير العهد", "لجنة المزايدات"],
        inputs=["أصل ثابت جديد أو أصل مستهلك بالكامل"],
        outputs=["سجل أصل محدَّث، أو قرار تصرف (بيع/إعدام)"],
        steps=["تسجيل الأصل", "ربطه بعُهدة موظف إن وُجدت", "الإهلاك الشهري التلقائي", "عند الاستهلاك الكامل: قرار التصرف (تحويل لمزايدة أو إعدام)"],
        decision_points=["هل الأصل قابل لإعادة البيع (مزايدة) أم للإعدام فقط؟"],
        related_configuration="راجع الفصل 6 — port_said_fixed_assets، وقاعدة السجل rule_no_delete_active_asset (الفصل 3).",
        related_models=["port_said.fixed.asset", "port_said.asset.disposal", "auction.lease.contract"],
    ))

    mb.workflow_doc("رقابة الموازنة (Budget Control Workflow)", dict(
        actors=["المصلحة الطالبة", "مدير الإدارة المالية"],
        inputs=["طلب احتياج أو أمر صرف"],
        outputs=["ارتباط مسمَّح جاهز للصرف الفعلي"],
        steps=["مسودة", "تقديم", "اعتماد", "تجنيب (حجز المبلغ)", "تسميح (اعتماد نهائي بعد استيفاء المستندات)", "صرف"],
        decision_points=["هل الرصيد المتاح من بند الموازنة كافٍ للارتباط الجديد؟"],
        approvals="اعتماد الارتباط ثم اعتماد التسميح، كلاهما بصلاحية مدير الإدارة المالية.",
        exception_handling="رفض الارتباط تلقائيًا عند تجاوز الرصيد المتاح؛ إمكانية إلغاء الارتباط في أي مرحلة قبل الصرف الفعلي.",
        related_models=["port_said.commitment"],
        related_configuration="odoo_deployment_ar/addons/port_said_commitment/models/*.py",
    ), screenshot_desc="مخطط تدفق رقابة الموازنة (ارتباط ← تجنيب ← تسميح)")

    mb.workflow_doc("عمليات الذكاء الاصطناعي (AI Processes)", dict(
        actors=NOT_FOUND,
        inputs=NOT_FOUND,
        outputs=NOT_FOUND,
        steps=[NOT_FOUND],
        exception_handling="لا ينطبق — لا يوجد وكيل ذكاء اصطناعي فعلي في النظام حتى تاريخ إعداد هذا الدليل. راجع الفصل 10.",
    ))

    mb.workflow_doc("سير العمل الحكومي للموافقات (Government Approval Process)", dict(
        actors=["اللجنة الفنية", "اللجنة المالية", "لجنة تشكيل اللجان", "الجهة المعتمِدة"],
        inputs=["مناقصة أو مزايدة حكومية بقيمة تستوجب لجانًا رسمية"],
        outputs=["قرار ترسية معتمد وفق القانون 182/2018"],
        steps=["تشكيل اللجان (procurement_committee)", "فتح المظروف الفني وتقييمه", "استبعاد غير المستوفين فنيًا", "فتح المظروف المالي للمتأهلين فقط", "الترسية على أفضل عرض مالي مؤهل فنيًا (procurement_adjudication)"],
        decision_points=["هل يجتاز العرض الحد الأدنى الفني؟"],
        approvals="فصل صارم بين التقييم الفني والمالي، وتوقيع اللجنة كاملة قبل الترسية.",
        related_models=["procurement.committee", "procurement.adjudication"],
        related_reports=["محضر البت الفني", "محضر البت المالي ومقارنة العروض", "إخطار الترسية"],
    ), screenshot_desc="مخطط سير عمل المظروفين المنفصلين (Dual-Envelope Adjudication)")
