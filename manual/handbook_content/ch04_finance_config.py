"""Chapter 4 — Finance Configuration Pages."""
from handbook_meta import NOT_FOUND


def build(mb):
    mb.h1("إعداد الوحدات المالية (Finance Configuration)")
    mb.para(
        "يوثّق هذا الفصل كل صفحة إعداد مالي وفق القالب الموحّد المطلوب. "
        "القيم التشغيلية الفعلية (كالأرقام الدقيقة لكل حساب أو نسبة ضريبة "
        "معتمدة) هي بيانات قاعدة بيانات وليست شيفرة مصدرية، وتُميَّز صراحة "
        f"بالعبارة: «{NOT_FOUND}»"
    )

    mb.config_doc("دليل الحسابات (Chart of Accounts)", dict(
        purpose="تعريف الهيكل الشجري لكل الحسابات المحاسبية المستخدمة في النظام (أصول، خصوم، حقوق ملكية، إيرادات، مصروفات).",
        business_need="توفير مرجع حسابي موحّد لكل القيود المحاسبية والتقارير المالية الحكومية.",
        navigation="المحاسبة ← الإعداد ← دليل الحسابات",
        configuration_steps=["تحديد نوع الحساب", "تحديد العملة (EGP افتراضيًا — راجع قسم العملات أدناه)", "تفعيل التسوية (Reconcile) عند الحاجة", "ربط الحساب بمتطلبات الأبعاد المالية إن لزم (راجع c5_financial_dimensions)"],
        fields=("table", ["الحقل", "النوع"], [
            ["code", "Char"], ["name", "Char"], ["account_type", "Selection"],
            ["currency_id", "Many2one → res.currency"], ["reconcile", "Boolean"],
            ["x_requires_department", "Boolean (مضاف بواسطة c5_financial_dimensions)"],
            ["x_requires_project", "Boolean (مضاف بواسطة c5_financial_dimensions)"],
            ["x_requires_region", "Boolean (مضاف بواسطة c5_financial_dimensions)"],
        ], "حقول account.account ذات الصلة (القياسية + المضافة)"),
        allowed_values="أنواع الحسابات القياسية في أودو (أصول متداولة، أصول ثابتة، التزامات متداولة، حقوق ملكية، إيرادات، مصروفات...) — القائمة الكاملة معرَّفة في نموذج account.account.type القياسي لأودو وليست جزءًا من التخصيص المفحوص.",
        mandatory_fields=["code", "name", "account_type"],
        dependencies=["account (وحدة أودو القياسية)", "c5_financial_dimensions — لحقول x_requires_*"],
        validation_rules=["لا يمكن ترحيل قيد على حساب يتطلب بُعدًا ماليًا (x_requires_department/project/region) دون تحديد قيمة ذلك البُعد على بند القيد."],
        related_models=["account.account", "account.move.line (الحقول x_dimension_* المضافة)"],
        related_python=["odoo_deployment_ar/addons/c5_financial_dimensions/models/*.py"],
        related_security=["account.group_account_manager (تعديل)، account.group_account_user (قراءة) — قياسي أودو، راجع الفصل 3 للتفاصيل الكاملة"],
        common_mistakes=["تصنيف حساب بنوع خاطئ يؤثر على تبويبه في الميزانية العمومية/قائمة الدخل", "نسيان تفعيل بُعد إلزامي على حساب يحتاجه فعليًا"],
        troubleshooting="عند رفض ترحيل قيد بسبب بُعد مالي ناقص، راجع حقول x_requires_* على الحساب المستخدم في الفصل 6 (c5_financial_dimensions).",
        best_practices=["لا تحذف حسابًا مستخدَمًا تاريخيًا؛ أوقف تفعيله بدلاً من ذلك"],
    ), screenshot_desc="شاشة دليل الحسابات")

    mb.config_doc("دفاتر اليومية (Journals)", dict(
        purpose="تحديد دفاتر اليومية (مبيعات، مشتريات، بنك، صندوق، عمليات متنوعة) التي تُصنَّف تحتها كل القيود.",
        navigation="المحاسبة ← الإعداد ← دفاتر اليومية",
        configuration_steps=["تحديد نوع الدفتر (بيع/شراء/نقدية/بنك/عام)", "ربط الدفتر بحسابه الافتراضي", "تفعيل التسلسل الرقمي الخاص بالدفتر"],
        dependencies=["account (Odoo قياسي)"],
        related_models=["account.journal"],
        common_mistakes=["استخدام دفتر بنكي لتسجيل حركة نقدية فعلية بالخطأ"],
        best_practices=["افصل كل دفتر بنكي حقيقي في دفتر يومية مستقل بدلاً من تجميعها في دفتر واحد"],
        related_configuration="راجع قسم «البنوك» أدناه، وقسم «دفاتر النقدية والبنوك الحكومية» في الفصل 6 (port_said_cash_books).",
    ))

    mb.config_doc("الضرائب (Taxes)", dict(
        purpose="تعريف نسب الضريبة المطبَّقة على بنود الفواتير (ضريبة القيمة المضافة المصرية بشكل أساسي).",
        navigation="المحاسبة ← الإعداد ← الضرائب",
        configuration_steps=["تحديد نسبة الضريبة", "تحديد نوع الاحتساب (شامل/غير شامل)", "ربطها بحساب الضريبة المستحقة/المدينة"],
        allowed_values="النسبة الفعلية المعتمدة حاليًا في بيئة الإنتاج: " + NOT_FOUND,
        dependencies=["account (Odoo قياسي)"],
        related_configuration="راجع l10n_eg_eta_invoice وc13_tax_xml_export في الفصل 6 للتكامل مع مصلحة الضرائب المصرية.",
        common_mistakes=["تطبيق ضريبة خاطئة على صنف معفى"],
        best_practices=["راجع النسب الضريبية عند بداية كل سنة مالية"],
    ))

    mb.config_doc("الأوضاع الضريبية (Fiscal Positions)", dict(
        purpose="أتمتة تبديل الضريبة أو الحساب حسب نوع العميل/المورد أو موقعه الجغرافي.",
        navigation="المحاسبة ← الإعداد ← الأوضاع الضريبية",
        dependencies=["account (Odoo قياسي)"],
        related_models=["account.fiscal.position"],
        allowed_values="الأوضاع الضريبية الفعلية المُهيَّأة (إن وُجدت): " + NOT_FOUND,
    ))

    mb.config_doc("شروط الدفع (Payment Terms)", dict(
        purpose="تحديد تاريخ استحقاق سداد الفاتورة (فوري، 30 يومًا، 60 يومًا...).",
        navigation="المحاسبة ← الإعداد ← شروط الدفع",
        dependencies=["account (Odoo قياسي)"],
        related_models=["account.payment.term"],
        related_configuration="راجع c4_payment_matching (الفصل 6) لمنطق مطابقة الدفعات المتجاوز.",
        allowed_values="شروط الدفع الفعلية المُهيَّأة: " + NOT_FOUND,
    ))

    mb.config_doc("البنوك (Banks)", dict(
        purpose="تسجيل الحسابات البنكية الفعلية للجهة وربطها بدفاتر اليومية البنكية.",
        navigation="المحاسبة ← الإعداد ← البنوك",
        dependencies=["account (Odoo قياسي)"],
        related_configuration="port_said_cash_books (الفصل 6) — دفتر البنك المركزي الحكومي بتنسيق استمارة 78.",
        allowed_values="أرقام الحسابات البنكية الفعلية (IBAN): " + NOT_FOUND,
    ))

    mb.config_doc("العملات (Currencies)", dict(
        purpose="تحديد العملة الأساسية للنظام وأي عملات إضافية مفعَّلة.",
        navigation="الإعدادات ← العملات",
        business_need="جميع الدفاتر الحكومية المفحوصة تستخدم الجنيه المصري (EGP) حصريًا (مستنتج من دالة amount_to_words في port_said_daftar55/models/daftar55.py التي تُخرج المبلغ بصيغة «جنيه» و«قرش» فقط).",
        allowed_values="لا دليل على تفعيل تعدد العملات القياسي في أودو ضمن الوحدات المفحوصة.",
        related_python=["odoo_deployment_ar/addons/port_said_daftar55/models/daftar55.py (دالة amount_to_words)"],
    ))

    mb.config_doc("السنوات المالية وتواريخ الإغلاق (Fiscal Years & Lock Dates)", dict(
        purpose="تحديد بداية ونهاية السنة المالية، وتاريخ قفل الفترات المحاسبية بعد اعتمادها.",
        business_need="السنة المالية الحكومية المصرية تبدأ 1 يوليو وتنتهي 30 يونيو (مستدَل عليه من حقل fiscal_year النصي في port_said.daftar55، وهو حقل Char وليس ربطًا بنموذج سنة مالية).",
        navigation="المحاسبة ← الإعداد ← تواريخ القفل",
        related_configuration="port_said_form75 (الفصل 6) — مسار اعتماد الإقفال الشهري بثلاث مراحل متسلسلة.",
        related_models=["port_said.form75 (حقل state بحالاته المتسلسلة)"],
        common_mistakes=["اعتبار حقل fiscal_year في دفتر 55 مرجعًا موحّدًا رغم كونه نصًا حرًا قابلاً للتفاوت في الصياغة بين المستخدمين"],
        allowed_values="تاريخ القفل الفعلي المعتمد حاليًا: " + NOT_FOUND,
    ))

    mb.config_doc("المحاسبة التحليلية (Analytic Accounting)", dict(
        purpose="تتبع الإيرادات والمصروفات حسب أبعاد إضافية (قسم/مشروع/منطقة) بمعزل عن دليل الحسابات.",
        navigation="المحاسبة ← الإعداد ← الحسابات التحليلية",
        dependencies=["analytic (Odoo قياسي)", "c5_financial_dimensions"],
        fields=("table", ["الحقل", "النموذج", "النوع"], [
            ["x_dimension_department_id", "account.move.line", "Many2one → hr.department"],
            ["x_dimension_project_id", "account.move.line", "Many2one → project.project"],
            ["x_dimension_region_id", "account.move.line", "Many2one → financial.dimension"],
        ], "حقول الأبعاد التحليلية المخصصة (c5_financial_dimensions)"),
        related_python=["odoo_deployment_ar/addons/c5_financial_dimensions/models/*.py"],
        related_models=["financial.dimension"],
        validation_rules=["إلزام تحديد البُعد التحليلي على الحسابات المصنَّفة بأنها تتطلب ذلك (x_requires_department/project/region = True)"],
    ), screenshot_desc="شاشة إعداد الأبعاد المالية")

    mb.config_doc("الأصول الثابتة (Assets)", dict(
        purpose="إدارة وإهلاك الأصول الثابتة الحكومية وفق معيار المحاسبة المصري رقم 10.",
        navigation="المحاسبة ← المحاسبة ← الأصول  |  الديوان العام ← الأصول الثابتة",
        related_models=["port_said.fixed.asset", "port_said.asset.disposal"],
        related_python=["odoo_deployment_ar/addons/port_said_fixed_assets/models/*.py"],
        related_xml=["odoo_deployment_ar/addons/port_said_fixed_assets/reports/*.xml"],
        related_security=["security/fixed_assets_security.xml — قاعدة rule_no_delete_active_asset (راجع الفصل 3)"],
        related_workflow="راجع الفصل 9 — سير عمل إدارة الأصول (Asset Management Workflow).",
        dependencies=["account", "l10n_eg_custody", "port_said_daftar55", "port_said_commitment", "l10n_eg_auction", "general_ledger_ar"],
        common_mistakes=["حذف أصل نشط مباشرة بدلاً من تغيير حالته أولاً — تمنعه قاعدة السجل rule_no_delete_active_asset فعليًا"],
    ), screenshot_desc="سجل الأصول الثابتة")

    mb.config_doc("الموازنات ورقابة الموازنة (Budgets & Budget Control)", dict(
        purpose="إعداد الموازنة التقديرية السنوية ومتابعة تنفيذها عبر محرك الارتباطات (ارتباط ← تجنيب ← تسميح).",
        navigation="الديوان العام ← الموازنة التقديرية وتحليل الانحرافات",
        related_models=["port_said.budget.plan", "port_said.commitment"],
        related_python=["odoo_deployment_ar/addons/port_said_budget_planning/models/*.py", "odoo_deployment_ar/addons/port_said_commitment/models/*.py"],
        related_workflow="راجع الفصل 9 — سير عمل رقابة الموازنة (Budget Control Workflow) بحالاته الكاملة (مسودة، مُقدَّم، معتمد، محجوز، مُسمَّح، مصروف، ملغى).",
        dependencies=["account", "port_said_daftar55", "port_said_commitment", "c5_financial_dimensions", "general_ledger_ar"],
        validation_rules=["يُمنع الارتباط بمبلغ يتجاوز الرصيد المتاح من بند الموازنة"],
        related_reports=["ملخص الموازنة التقديرية", "تقرير الانحرافات", "تقرير تنفيذ الموازنة (port_said_budget_planning وport_said_reports — راجع الفصل 8)"],
    ), screenshot_desc="تقرير الموازنة التقديرية مقابل الفعلي")

    mb.config_doc("النقدية (Cash)", dict(
        purpose="إدارة صناديق النقدية ودفاتر البنك المركزي وأوامر الدفع والكفالات وفق تنسيق استمارة 78 الحكومي.",
        navigation="الديوان العام ← دفاتر النقدية وأوامر الدفع والكفالات",
        related_models=["port_said.cash.folio", "port_said.payment_order", "port_said.surety"],
        related_python=["odoo_deployment_ar/addons/port_said_cash_books/models/*.py"],
        related_security=["security/security_groups.xml — دفاتر النقدية والبنك: مستخدم/مدير"],
        dependencies=["account", "port_said_daftar55", "port_said_daftar224", "port_said_subsidiary_books", "port_said_menu", "general_ledger_ar"],
    ))

    mb.config_doc("التقارير المالية (Financial Reports)", dict(
        purpose="ميزان المراجعة، الميزانية العمومية، قائمة الدخل، قائمة التدفقات النقدية.",
        navigation="المحاسبة ← التقارير ← التقارير المالية  |  الديوان العام ← التقارير المحاسبية الحكومية",
        related_configuration="راجع الفصل 8 (التقارير) للكتالوج الكامل — 100 تقرير حقيقي مستخرَج من الشيفرة المصدرية.",
    ))

    mb.config_doc("التوطين المصري والإعداد الحكومي (Localization & Government Configuration)", dict(
        purpose="متطلبات التوطين الضريبي المصري: الفاتورة الإلكترونية (ETA)، تصدير ملفات الضريبة XML.",
        navigation="الديوان العام ← الفاتورة الإلكترونية",
        related_models=["eta.invoice"],
        related_python=["odoo_deployment_ar/addons/l10n_eg_eta_invoice/models/*.py", "odoo_deployment_ar/addons/c13_tax_xml_export/models/*.py"],
        dependencies=["base", "mail", "account", "port_said_daftar55", "general_ledger_ar"],
        related_security="بيانات اعتماد الواجهة البرمجية الخارجية (Client ID/Secret): " + NOT_FOUND + " — تُدار عبر خزانة أسرار آمنة منفصلة لأسباب أمنية.",
    ))
