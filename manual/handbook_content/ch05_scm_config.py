"""Chapter 5 — Supply Chain Configuration Pages."""
from handbook_meta import NOT_FOUND


def build(mb):
    mb.h1("إعداد سلسلة التوريد (Supply Chain Configuration)")

    mb.config_doc("المخزون والمستودعات (Inventory & Warehouses)", dict(
        purpose="تعريف المستودعات الحكومية ومواقعها الفرعية (استلام، فحص، تخزين، تسليم).",
        navigation="المخزون ← الإعداد ← المستودعات",
        configuration_steps=["إنشاء مستودع لكل موقع حكومي فعلي", "تفعيل خطوات الاستلام المتعددة بما يتوافق مع لجنة الفحص (نموذج 12)", "ربط كل مستودع بمواقعه الفرعية"],
        dependencies=["stock (Odoo قياسي)", "port_said_scm_warehouse", "stock_addition_permit"],
        related_models=["stock.warehouse", "stock.location", "port_said.inspection.committee", "stock.addition.permit"],
        related_python=["odoo_deployment_ar/addons/port_said_scm_warehouse/models/*.py", "odoo_deployment_ar/addons/stock_addition_permit/models/*.py"],
        allowed_values="أسماء وأكواد المستودعات الفعلية المُهيَّأة: " + NOT_FOUND,
    ))

    mb.config_doc("المواقع (Locations)", dict(
        purpose="نقاط تخزين فرعية داخل مستودع أو خارجه (عميل/مورد/خسارة مخزون).",
        navigation="المخزون ← الإعداد ← المواقع",
        dependencies=["stock (Odoo قياسي)"],
        related_models=["stock.location"],
        best_practices=["افصل موقع الفحص عن موقع التخزين النهائي لضمان عدم صرف أصناف لم تُفحص بعد"],
    ))

    mb.config_doc("المسارات وأنواع العمليات (Routes & Operation/Picking Types)", dict(
        purpose="تحديد كيفية تدفق الصنف بين المواقع (استلام → فحص → تخزين → تسليم).",
        navigation="المخزون ← الإعداد ← المسارات / أنواع العمليات",
        dependencies=["stock (Odoo قياسي)"],
        related_configuration="stock_addition_permit (الفصل 6) — عملية استلام من خطوتين: تقرير الفحص ثم إذن الإضافة (نموذج 1).",
        related_workflow="راجع الفصل 9 — سير عمل استلام المخازن (Goods Receipt Workflow).",
    ))

    mb.config_doc("قواعد إعادة الطلب (Reordering Rules)", dict(
        purpose="إنشاء اقتراح شراء تلقائي عند وصول رصيد صنف للحد الأدنى المحدد.",
        navigation="المخزون ← التخطيط ← قواعد إعادة الطلب",
        dependencies=["stock (Odoo قياسي)"],
        validation_rules=["الاقتراح الناتج يتطلب اعتمادًا بشريًا قبل تحويله لأمر توريد فعلي، حفاظًا على الرقابة المسبقة على الموازنة"],
        allowed_values="الحدود الدنيا/القصوى الفعلية المُهيَّأة لكل صنف: " + NOT_FOUND,
    ))

    mb.config_doc("التدبير والمشتريات (Procurement & Purchase)", dict(
        purpose="طلب الاحتياج، طلب عروض الأسعار، أمر التوريد، وفق مصفوفة موافقات متدرجة وتشكيل لجان إلزامي.",
        navigation="الديوان العام ← طلب الاحتياج  |  المشتريات ← الطلبات",
        related_models=["port_said.requisition", "procurement.committee", "procurement.adjudication"],
        related_python=[
            "odoo_deployment_ar/addons/port_said_scm_requisition/models/*.py",
            "odoo_deployment_ar/addons/procurement_committee/models/*.py",
            "odoo_deployment_ar/addons/procurement_adjudication/models/*.py",
            "odoo_deployment_ar/addons/c1_purchase_approval_matrix/models/*.py",
        ],
        dependencies=["purchase (Odoo قياسي)", "port_said_commitment", "mail", "uom"],
        related_workflow="راجع الفصل 9 — سير عمل اعتماد المشتريات (Purchase Approval Workflow) وسير عمل البت الفني والمالي (Dual-Envelope Adjudication).",
        validation_rules=["لا يمكن تأكيد أمر توريد دون ارتباط موازنة معتمد ومسمَّح"],
    ), screenshot_desc="دورة المشتريات من طلب الاحتياج حتى أمر التوريد")

    mb.config_doc("إعداد الموردين (Vendor Configuration)", dict(
        purpose="بطاقة المورد: البيانات الضريبية، شروط الدفع، قوائم الأسعار التعاقدية.",
        navigation="المشتريات ← الموردون",
        dependencies=["purchase (Odoo قياسي)", "c8_contract_pricing", "c7_credit_bureau"],
        related_python=["odoo_deployment_ar/addons/c8_contract_pricing/models/*.py", "odoo_deployment_ar/addons/c7_credit_bureau/models/*.py"],
        related_configuration="c7_credit_bureau (الفصل 6) — فحص ائتماني عبر واجهة برمجية خارجية (يتطلب بيانات اعتماد لا تُدرج في هذا الدليل لأسباب أمنية).",
    ))

    mb.config_doc("تقييم المخزون (Inventory Valuation)", dict(
        purpose="احتساب القيمة المالية للمخزون وربطها بحسابات دليل الحسابات.",
        navigation="المخزون ← الإعداد ← التقييم",
        dependencies=["stock_account (Odoo قياسي)", "c10_inventory_revaluation", "port_said_stock_finance_bridge"],
        related_python=[
            "odoo_deployment_ar/addons/c10_inventory_revaluation/models/*.py",
            "odoo_deployment_ar/addons/port_said_stock_finance_bridge/models/*.py",
        ],
        related_reports=["تقرير إعادة تقييم المخزون (c10_inventory_revaluation) — راجع الفصل 8"],
        allowed_values="طريقة التقييم الفعلية المعتمدة (متوسط مرجّح متحرك/FIFO): " + NOT_FOUND,
    ))

    mb.config_doc("الدُفعات والأرقام التسلسلية (Lots & Serial Numbers)", dict(
        purpose="تتبع الأصناف عبر أرقام دُفعات أو أرقام تسلسلية فردية، خاصة الأصناف المصنَّفة كعُهد مستديمة.",
        navigation="المخزون ← الإعداد ← أنواع التتبع",
        dependencies=["stock (Odoo قياسي)", "l10n_eg_custody"],
        related_python=["odoo_deployment_ar/addons/l10n_eg_custody/models/*.py"],
        related_models=["custody.assignment"],
        validation_rules=["الأصول المصنَّفة كعُهد (نموذج 193) تتطلب رقمًا تسلسليًا فرديًا إلزاميًا"],
    ))

    mb.config_doc("الجودة والصيانة (Quality & Maintenance)", dict(
        purpose="[غير مُفعَّل] لا توجد وحدة جودة (quality) أو صيانة معدات (maintenance) قياسية مثبَّتة ضمن نطاق الفحص.",
        business_need="أقرب وظيفة مكافئة فعليًا هي لجنة الفحص (port_said_scm_warehouse) عند استلام الأصناف الواردة فقط.",
        related_configuration="port_said_scm_warehouse (الفصل 6) — نموذج 12: محضر لجنة الفحص.",
        allowed_values=NOT_FOUND,
    ))

    mb.config_doc("الباركود (Barcode)", dict(
        purpose="تسريع عمليات الاستلام/الصرف/الجرد عبر مسح الباركود.",
        navigation="المخزون ← الباركود",
        allowed_values="حالة تفعيل واجهة الباركود الفعلية ضمن هذا النظام تحديدًا: " + NOT_FOUND,
    ))

    mb.config_doc("التسليم (Delivery)", dict(
        purpose="إصدار أذونات الصرف والتسليم للمصالح الطالبة.",
        navigation="الديوان العام ← أذونات الصرف والارتجاع والتحويل",
        related_models=["[نموذج إذن الصرف — راجع الفصل 6، وحدة port_said_scm_issue]"],
        related_python=["odoo_deployment_ar/addons/port_said_scm_issue/models/*.py"],
        dependencies=["stock", "account", "hr", "mail", "port_said_scm_warehouse", "l10n_eg_custody", "port_said_fixed_assets", "port_said_commitment", "port_said_daftar55"],
    ))

    mb.config_doc("التصنيع (Manufacturing)", dict(
        purpose="[غير مُنطبق] لا يتضمن نطاق هذا النظام أي نشاط تصنيعي؛ لا توجد وحدة mrp أو bom مثبَّتة ضمن نطاق الفحص.",
        allowed_values=NOT_FOUND,
    ))

    mb.config_doc("الجرد الحكومي (Government Stocktaking)", dict(
        purpose="جرد دوري رسمي وفق نموذج 6 مع تقرير فائض/عجز، وإجراء إعدام منفصل (نموذج 4).",
        navigation="الديوان العام ← الجرد الحكومي",
        related_models=["stock.stocktaking.session"],
        related_python=["odoo_deployment_ar/addons/stock_stocktaking_eg/models/*.py"],
        related_security=["security/stocktaking_security.xml — أمين المخزن/مفتش المخزن/مدير المخازن/عضو لجنة الجرد/رئيس لجنة الجرد"],
        related_workflow="راجع الفصل 9 — سير عمل تسوية المخزون (Inventory Adjustment Workflow).",
        validation_rules=["إجراء الإعدام (نموذج 4) يتطلب اعتمادًا منفصلاً عن تسوية الجرد العادية"],
    ), screenshot_desc="محضر جرد الأصناف — نموذج 6")
