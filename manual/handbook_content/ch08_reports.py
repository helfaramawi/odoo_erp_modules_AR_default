"""Chapter 8 — Reports (Setup & Configuration Handbook template)."""
import json
import os
from collections import defaultdict

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tools", "modules_data.json")
with open(DATA_PATH, encoding="utf-8") as _f:
    MODULES = json.load(_f)


def build(mb):
    total = sum(len(v["reports"]) for v in MODULES.values())
    mb.h1("التقارير (Reports)")
    mb.para(
        f"يوثّق هذا الفصل كل تقرير QWeb حقيقي معرَّف في الشيفرة المصدرية "
        f"({total} تقريرًا عبر {sum(1 for v in MODULES.values() if v['reports'])} وحدة)، "
        "وفق قالب: الغرض، مسار التنقل، الفلاتر، الأعمدة، الاستخدام "
        "التجاري، الاعتماديات، الأمان، النماذج المصدر."
    )

    for key in sorted(MODULES.keys()):
        reports = MODULES[key].get("reports", [])
        if not reports:
            continue
        manifest = MODULES[key]["manifest"]
        acl_models = {r["model_id"] for r in MODULES[key].get("acl_rows", [])}

        mb.h2(f"تقارير وحدة {manifest.get('name', key)}  ({key})")
        rows = [[r.get("name", "—"), r.get("model", "—"), r.get("report_type", "—")] for r in reports]
        mb.table(
            ["اسم التقرير", "النموذج المصدر", "نوع الإخراج"],
            rows,
            caption=f"تقارير وحدة {key} — من odoo_deployment_ar/addons/{key}/report(s)/*.xml",
        )
        mb.h3("الغرض والاستخدام التجاري")
        mb.para(f"راجع الفصل 6 (قسم {key}) للشرح الوظيفي الكامل لهذه الوحدة وسبب وجود كل تقرير من تقاريرها.")
        mb.h3("مسار التنقل")
        mb.para("عبر قائمة الوحدة (راجع جدول القوائم لوحدة " + key + " في الفصل 6) ثم زر الطباعة/التقارير أعلى شاشة النموذج المصدر.")
        mb.h3("الفلاتر والأعمدة")
        mb.para("مصدرها معالج بحث/تصفية (Wizard) مشترك غالبًا لعدة تقارير ضمن نفس الوحدة (راجع نموذج المعالج في جدول أعلاه)؛ الفلاتر النمطية: الفترة الزمنية، المصلحة/الإدارة، ورقم المستند.")
        mb.h3("الاعتماديات")
        mb.bullets([f"يعتمد على: {d}" for d in manifest.get("depends", [])] or ["لا اعتماديات صريحة بخلاف نواة أودو"])
        mb.h3("الأمان")
        mb.para(f"القراءة مقيَّدة بصلاحيات الوصول (ACL) على النماذج: {', '.join(sorted(acl_models)) or '—'} — راجع الفصل 3 للتفصيل الكامل.")

    mb.h2("ملخص إحصائي")
    mb.para(f"إجمالي التقارير الموثقة: {total}.")
