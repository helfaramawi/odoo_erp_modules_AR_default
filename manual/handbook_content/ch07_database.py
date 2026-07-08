"""Chapter 7 — Database Documentation.

Flat, DBA-oriented catalogue distinct from Chapter 6's per-module narrative:
a model index, a full relation index (every Many2one/One2many/Many2many),
a consolidated SQL constraint list, and an explicit-index list — all
generated directly from modules_data.json.
"""
import json
import os

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tools", "modules_data.json")
with open(DATA_PATH, encoding="utf-8") as _f:
    MODULES = json.load(_f)


def _all_models():
    out = []
    for module_key, data in sorted(MODULES.items()):
        for m in data.get("models", []) + data.get("wizards", []):
            out.append((module_key, m))
    return out


def build(mb):
    all_models = _all_models()
    total_fields = sum(len(m.get("fields", [])) for _, m in all_models)
    total_rel = sum(1 for _, m in all_models for f in m.get("fields", []) if f.get("comodel"))

    mb.h1("توثيق قاعدة البيانات (Database Documentation)")
    mb.para(
        f"يوثّق هذا الفصل {len(all_models)} نموذج بيانات (بما فيها "
        f"المعالجات/Wizards) تحتوي إجمالاً {total_fields} حقلاً، منها "
        f"{total_rel} حقل علاقة (Many2one/One2many/Many2many)، مستخرجة "
        "آليًا من كل ملفات models/*.py وwizard/*.py عبر الوحدات الـ47. هذا "
        "الفصل مرجع مسطّح (Flat Reference) لفريق قواعد البيانات، بخلاف "
        "الفصل 6 الذي ينظّم نفس الحقائق سرديًا لكل وحدة على حدة."
    )

    mb.h2("فهرس النماذج (Model Index)")
    rows = []
    for module_key, m in all_models:
        inh = m.get("_inherit")
        inh_txt = ", ".join(inh) if isinstance(inh, list) else (inh or "—")
        rows.append([
            m.get("_name") or "—", module_key, m.get("source_file", "—"),
            inh_txt, str(len(m.get("fields", []))),
        ])
    mb.table(
        ["اسم النموذج (_name)", "الوحدة", "ملف المصدر", "يرث من", "عدد الحقول"],
        rows,
        caption="فهرس شامل لكل نماذج البيانات المخصصة عبر النظام",
        col_widths=[4, 3, 5, 3, 1.5],
    )

    mb.h2("فهرس العلاقات (Relations Index — Many2one / One2many / Many2many)")
    mb.para("كل حقل علاقة حقيقي مستخرج من الشيفرة المصدرية، مع النموذج المصدر ونوع العلاقة والنموذج الهدف (comodel).")
    rel_rows = []
    for module_key, m in all_models:
        model_name = m.get("_name") or m["class_name"]
        for f in m.get("fields", []):
            if f.get("comodel"):
                rel_rows.append([model_name, f["name"], f["type"], f["comodel"], module_key])
    mb.table(
        ["النموذج المصدر", "اسم الحقل", "نوع العلاقة", "النموذج الهدف (comodel)", "الوحدة"],
        rel_rows,
        caption="فهرس كل علاقات قاعدة البيانات المخصصة (Many2one/One2many/Many2many)",
        col_widths=[3.5, 3, 2, 3.5, 2.5],
    )

    mb.h2("قيود SQL الموحّدة (Consolidated SQL Constraints)")
    sql_rows = []
    for module_key, m in all_models:
        for c in m.get("sql_constraints", []):
            sql_rows.append([m.get("_name") or "—", c["name"], c["constraint"], c["message"], module_key])
    if sql_rows:
        mb.table(
            ["النموذج", "اسم القيد", "تعريف SQL", "رسالة الخطأ", "الوحدة"],
            sql_rows,
            caption="كل قيود SQL (_sql_constraints) المعرَّفة صراحة عبر النظام",
            col_widths=[3, 3, 4, 4, 2],
        )
    else:
        mb.para("لم يُعثر على أي قيد SQL صريح.")

    mb.h2("دوال التحقق البرمجي الموحّدة (@api.constrains)")
    cons_rows = []
    for module_key, m in all_models:
        for c in m.get("constrains_methods", []):
            cons_rows.append([m.get("_name") or "—", c["method"], ", ".join(c["fields"]) or "—", module_key])
    if cons_rows:
        mb.table(
            ["النموذج", "الدالة", "الحقول المراقَبة", "الوحدة"],
            cons_rows,
            caption="كل دوال @api.constrains المعرَّفة عبر النظام",
            col_widths=[3.5, 3.5, 5, 2.5],
        )
    else:
        mb.para("لم يُعثر على أي دالة @api.constrains.")

    mb.h2("الحقول المفهرَسة صراحة (Explicit index=True Fields)")
    idx_rows = []
    for module_key, m in all_models:
        for f in m.get("fields", []):
            if f.get("index"):
                idx_rows.append([m.get("_name") or "—", f["name"], f["type"], module_key])
    if idx_rows:
        mb.table(
            ["النموذج", "الحقل", "النوع", "الوحدة"],
            idx_rows,
            caption="الحقول التي تحمل index=True صراحة في تعريفها",
            col_widths=[4, 3.5, 3, 3.5],
        )
    mb.note(
        "بخلاف الفهرسة الصريحة أعلاه، يفهرس أودو تلقائيًا (ORM-level) كل "
        "حقل Many2one، وحقل company_id، وحقل الحالة (state) في أغلب "
        "النماذج القياسية — وهو سلوك افتراضي من إطار عمل أودو لا يظهر "
        "كسطر صريح في الشيفرة المصدرية."
    )

    mb.h2("طبقة الربط الكائني-العلائقي (ORM Layer)")
    mb.para(
        "تعتمد كل النماذج الموثقة أعلاه على ORM الخاص بأودو (Object-"
        "Relational Mapping)، حيث يُترجم كل تعريف حقل بايثون تلقائيًا لعمود "
        "فعلي في جدول PostgreSQL يحمل نفس اسم الحقل، وتُترجم حقول Many2one "
        "لعمود معرّف صحيح (Integer) مع قيد مفتاح خارجي (Foreign Key) على "
        "جدول النموذج الهدف، بينما تُترجم حقول Many2many لجدول ربط وسيط "
        "(Relation Table) منفصل يُنشئه أودو تلقائيًا ما لم يُحدَّد اسمه "
        "صراحة."
    )
