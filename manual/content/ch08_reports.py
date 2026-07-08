"""Chapter 8 — Reports.

Full catalogue of every QWeb report actually defined in the addon source
(100 reports across 30 modules — extracted by manual/tools/extract_modules.py
into modules_data.json), grouped by module and by the wizard/model that
produces them so the documentation reflects how users actually run them in
Odoo (most Port Said reports share one selection wizard per module that then
prints one of several report layouts).
"""
import json
import os
from collections import OrderedDict, defaultdict

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tools", "modules_data.json")
with open(DATA_PATH, encoding="utf-8") as _f:
    MODULES = json.load(_f)

MODULE_LABELS = {
    "c10_inventory_revaluation": "إعادة تقييم المخزون",
    "c3_aging_report": "أعمار المدينين والدائنين",
    "l10n_eg_auction": "المزايدات",
    "l10n_eg_custody": "العُهد الحكومية",
    "l10n_eg_eta_invoice": "الفاتورة الإلكترونية ETA",
    "port_said_acct_reports": "التقارير المحاسبية",
    "port_said_advances": "السلف والضمانات البنكية",
    "port_said_budget_planning": "الموازنة التقديرية",
    "port_said_cash_books": "دفاتر النقدية والبنوك",
    "port_said_cash_transfers": "حركة النقود المرسلة والواردة",
    "port_said_cheques": "الشيكات وأوامر الدفع",
    "port_said_commitment": "الارتباطات والتسميح",
    "port_said_daftar224": "دفتر 224 ع.ح",
    "port_said_daftar55": "دفتر 55 ع.ح",
    "port_said_dossier": "الاضابير",
    "port_said_fixed_assets": "الأصول الثابتة",
    "port_said_form69": "استمارة 69",
    "port_said_form75": "استمارة 75",
    "port_said_gl_reports": "التقارير المحاسبية الحكومية",
    "port_said_insurance_subsidiary": "دفاتر التأمينات",
    "port_said_penalties": "دفتر الجزاءات",
    "port_said_reports": "التقارير الحكومية الشاملة",
    "port_said_revenue_books": "دفاتر الإيرادات والمصروفات",
    "port_said_scm_requisition": "طلب الاحتياج",
    "port_said_scm_warehouse": "لجنة الفحص والمخازن",
    "port_said_subsidiary_books": "الدفاتر المساعدة",
    "procurement_adjudication": "البت الفني والمالي",
    "procurement_committee": "تشكيل اللجان",
    "stock_addition_permit": "إذن الإضافة",
    "stock_stocktaking_eg": "الجرد الحكومي",
}


def build(mb):
    mb.h1("التقارير (Reports)")
    mb.para(
        "يوثّق هذا الفصل كل تقرير QWeb حقيقي معرَّف فعليًا داخل الشيفرة "
        "المصدرية للنظام (100 تقرير عبر 30 وحدة)، مستخرَجًا آليًا من ملفات "
        "التقارير (ir.actions.report) لضمان عدم إغفال أي تقرير. تُعرض "
        "التقارير مجمّعة حسب الوحدة وحسب المعالج (Wizard) الذي يُنتجها، لأن "
        "الغالبية العظمى من التقارير الحكومية في هذا النظام تُشغَّل من شاشة "
        "معايير بحث واحدة (Wizard) تتيح اختيار نوع التقرير المطلوب من قائمة "
        "منسدلة، وليس كل تقرير له شاشة معايير منفصلة."
    )
    mb.bullets([
        "جميع التقارير في هذا النظام من نوع qweb-pdf (توليد PDF مباشر قابل للطباعة)، إضافة إلى تصدير Excel المتاح قياسيًا من شاشة أي قائمة عرض في أودو (راجع الفصل 1 — التصدير والاستيراد).",
        "الفلترة القياسية عبر كل معالجات التقارير الحكومية تشمل: الفترة الزمنية (من/إلى)، المصلحة/الإدارة، ورقم المستند عند الحاجة.",
        "الفرز الافتراضي زمني تصاعدي حسب تاريخ المستند ما لم يُذكر خلاف ذلك صراحة.",
    ])

    total = 0
    for key, arabic_label in MODULE_LABELS.items():
        if key not in MODULES or not MODULES[key]["reports"]:
            continue
        reports = MODULES[key]["reports"]
        total += len(reports)
        mb.h2(f"تقارير وحدة: {arabic_label} ({key})")
        mb.para(
            f"راجع الفصل 6 للتفاصيل الوظيفية الكاملة لوحدة {arabic_label}. "
            "يقتصر هذا القسم على توثيق مخرجات الطباعة والتقارير فقط."
        )

        by_model = defaultdict(list)
        for r in reports:
            by_model[r.get("model", "—")].append(r)

        for model, rlist in by_model.items():
            rows = [[r.get("name", "—"), r.get("report_type", "—")] for r in rlist]
            mb.table(
                ["اسم التقرير", "نوع الإخراج"],
                rows,
                caption=f"تقارير مُنتَجة من النموذج {model} — وحدة {key}",
                col_widths=[10, 4],
            )
        mb.h3("مصدر البيانات وعوامل التصفية")
        mb.para(
            f"مصدر البيانات: النموذج/النماذج {', '.join(sorted(by_model.keys()))} "
            f"الموثقة بالكامل (الحقول والحالات) في الفصل 6. تُصفَّى معظم هذه "
            "التقارير بالفترة الزمنية والمصلحة كحد أدنى، مع معايير إضافية "
            "خاصة بكل تقرير (مثال: المورد/العميل لكشوف الحسابات، رقم "
            "الأصل للأصول الثابتة)."
        )
        mb.h3("التصدير")
        mb.bullets(["PDF (qweb-pdf) — الصيغة الأساسية لكل تقارير هذه الوحدة", "Excel — عبر تصدير شاشة القائمة المصدر قبل الطباعة"])
        mb.screenshot(f"معاينة أحد تقارير وحدة {arabic_label}")

    mb.h2("ملخص إحصائي لكل التقارير الموثقة")
    mb.para(f"إجمالي عدد التقارير الموثقة في هذا الفصل: {total} تقريرًا عبر {len(MODULE_LABELS)} وحدة.")
    mb.note(
        "لا توجد حاليًا تقارير مبنية على لوحات بيانات تفاعلية (BI/Charts) "
        "منفصلة عن تقارير الطباعة الرسمية؛ العنصر الأقرب لذلك هو لوحة "
        "القيادة التنفيذية الموثقة بالكامل في الفصل 9."
    )
