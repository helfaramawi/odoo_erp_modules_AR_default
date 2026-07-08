"""Chapter 6 — Custom Modules, Reverse-Engineered.

Every module gets the handbook's required technical template (Purpose,
Business Problem, Architecture, Dependencies, Menus, Views, Security, Models,
Fields, Python Logic, XML, Reports, Cron Jobs, Integrations, API,
Configuration, Deployment, Testing, Future Enhancements), with explicit file
path citations for every fact. Reuses the purpose/business-need narrative
already authored for the System Manual (content.ch06_customizations) since it
remains accurate, but restructures and extends it with the lower-level
technical facts unique to this handbook (SQL constraints, cron jobs,
sequences, source file paths).
"""
from content import ch06_customizations as sm
from handbook_meta import NOT_FOUND

MODULES = sm.MODULES
NARRATIVE = sm.NARRATIVE
DEFAULT_NARRATIVE = sm.DEFAULT_NARRATIVE
GROUPS = sm.GROUPS


def _model_files(models):
    files = sorted({m["source_file"] for m in models if m.get("source_file")})
    return files


def _sql_constraints_rows(models):
    rows = []
    for m in models:
        for c in m.get("sql_constraints", []):
            rows.append([m.get("_name") or m["class_name"], c["name"], c["constraint"], c["message"]])
    return rows


def _constrains_rows(models):
    rows = []
    for m in models:
        for c in m.get("constrains_methods", []):
            rows.append([m.get("_name") or m["class_name"], c["method"], ", ".join(c["fields"]) or "—"])
    return rows


def build(mb):
    mb.h1("الوحدات المخصصة — إعادة الهندسة العكسية الكاملة (Custom Modules Reverse-Engineered)")
    mb.para(
        "لكل وحدة من الوحدات الـ47، يتّبع هذا الفصل القالب التقني الكامل "
        "المطلوب مع الاستشهاد الصريح بمسار كل ملف. الشرح الوظيفي (الغرض، "
        "المشكلة، سير العمل) مبني على نفس السرد المعتمد في «دليل النظام "
        "الشامل» (يظل دقيقًا وصالحًا لأنه غير مرتبط بتغييرات الشيفرة)، بينما "
        "الحقائق التقنية الدقيقة (مسارات الملفات، قيود SQL، دوال التحقق) "
        "مستخرجة حصريًا لهذا الدليل."
    )

    for group_title, module_keys in GROUPS:
        mb.h2(group_title)
        for key in module_keys:
            if key not in MODULES:
                continue
            _build_module(mb, key, MODULES[key])


def _build_module(mb, key, data):
    manifest = data.get("manifest", {})
    name_ar = manifest.get("name", key)
    narrative = NARRATIVE.get(key, DEFAULT_NARRATIVE)
    models = data.get("models", [])
    wizards = data.get("wizards", [])
    all_models = models + wizards

    mb.h3(f"{name_ar}  ({key})")
    mb.index_entry(name_ar, key)
    for m in all_models:
        if m.get("_name"):
            mb.index_entry(m["_name"])

    mb.h4("الغرض (Purpose)")
    mb.para(narrative["purpose"])

    mb.h4("المشكلة التجارية (Business Problem)")
    mb.para(narrative["problem"])

    mb.h4("البنية (Architecture)")
    mb.para(
        f"الوحدة {key} تحتوي {len(models)} نموذج بيانات و{len(wizards)} "
        f"معالج (Wizard)، موزَّعة على {len(_model_files(all_models))} ملف "
        "بايثون. بيان الوحدة (__manifest__.py) يحمّل الملفات التالية عند "
        "التثبيت:"
    )
    data_files = manifest.get("data", [])
    if data_files:
        mb.bullets([f"odoo_deployment_ar/addons/{key}/{f}" for f in data_files])
    else:
        mb.para(NOT_FOUND)

    mb.h4("الاعتماديات (Dependencies)")
    depends = manifest.get("depends", [])
    mb.bullets([f"يعتمد على وحدة: {d}" for d in depends] if depends else ["لا اعتماديات صريحة بخلاف نواة أودو الأساسية."])

    mb.h4("القوائم (Menus)")
    menus = data.get("menus", [])
    if menus:
        mb.table(
            ["معرّف القائمة (XML ID)", "الاسم", "القائمة الأب", "الإجراء المرتبط"],
            [[m.get("id", "—"), m.get("name", "—"), m.get("parent", "—"), m.get("action", "—")] for m in menus],
            caption=f"قوائم وحدة {key}",
        )
    else:
        mb.para("لا توجد عناصر قوائم مباشرة في هذه الوحدة (تُستدعى شاشاتها من قوائم وحدة أخرى).")

    mb.h4("الواجهات (Views)")
    views = data.get("views", [])
    if views:
        mb.table(
            ["معرّف العرض (XML ID)", "اسم العرض التقني", "النموذج"],
            [[v.get("id", "—"), v.get("name", "—"), v.get("model", "—")] for v in views],
            caption=f"واجهات (Views) وحدة {key}",
        )
    else:
        mb.para(NOT_FOUND)

    mb.h4("الأمان (Security)")
    sec_files = data.get("security_files", [])
    acl_rows = data.get("acl_rows", [])
    rules = data.get("record_rules", [])
    mb.para(
        f"ملفات الأمان: {', '.join(f'security/{s}' for s in sec_files) if sec_files else 'لا توجد'}. "
        f"عدد أسطر ACL: {len(acl_rows)}. عدد قواعد السجل: {len(rules)}. "
        "راجع الفصل 3 للتفصيل الكامل لكل سطر."
    )

    mb.h4("النماذج (Models)")
    if all_models:
        rows = []
        for m in all_models:
            inh = m.get("_inherit")
            inh_txt = ", ".join(inh) if isinstance(inh, list) else (inh or "—")
            rows.append([m.get("_name") or "—", inh_txt, m.get("source_file", "—"), str(len(m.get("fields", [])))])
        mb.table(
            ["اسم النموذج (_name)", "يرث من (_inherit)", "ملف المصدر", "عدد الحقول"],
            rows,
            caption=f"نماذج وحدة {key}",
        )
    else:
        mb.para("لا توجد نماذج بيانات جديدة في هذه الوحدة.")

    mb.h4("الحقول (Fields)")
    for m in all_models:
        name = m.get("_name") or m["class_name"]
        fields = m.get("fields", [])
        if not fields:
            continue
        rows = []
        for f in fields:
            sel = f.get("selection")
            sel_txt = " / ".join(f"{v}={lbl}" for v, lbl in sel) if sel else (f.get("comodel") or "—")
            rows.append([f["name"], f.get("type") or "—", f.get("string") or "—",
                        "نعم" if f.get("required") else "لا", sel_txt])
        mb.field_table(
            [{"name": r[0], "arabic": r[2], "desc": r[4], "mandatory": r[3] == "نعم",
              "default": "—", "validation": "إلزامي" if r[3] == "نعم" else "اختياري",
              "example": "—", "related": r[4] if f.get("comodel") else "—"} for r, f in zip(rows, fields)],
            caption=f"حقول النموذج {name}  —  {m.get('source_file', '—')}",
        )

    mb.h4("قيود SQL ودوال التحقق (SQL Constraints & @api.constrains)")
    sql_rows = _sql_constraints_rows(all_models)
    if sql_rows:
        mb.table(["النموذج", "اسم القيد", "تعريف القيد SQL", "رسالة الخطأ"], sql_rows,
                  caption=f"قيود SQL المعرَّفة صراحة في وحدة {key}")
    constrains_rows = _constrains_rows(all_models)
    if constrains_rows:
        mb.table(["النموذج", "الدالة (@api.constrains)", "الحقول المراقَبة"], constrains_rows,
                  caption=f"دوال التحقق البرمجي (@api.constrains) في وحدة {key}")
    if not sql_rows and not constrains_rows:
        mb.para("لم يُعثر على قيود SQL صريحة (_sql_constraints) أو دوال @api.constrains في هذه الوحدة.")

    mb.h4("منطق بايثون (Python Logic)")
    py_files = _model_files(all_models)
    if py_files:
        mb.bullets([f"odoo_deployment_ar/addons/{f}" for f in py_files])
    else:
        mb.para(NOT_FOUND)

    mb.h4("ملفات XML (XML Files)")
    xml_related = sorted({d for d in data_files if d.endswith(".xml")})
    if xml_related:
        mb.bullets([f"odoo_deployment_ar/addons/{key}/{f}" for f in xml_related])
    else:
        mb.para(NOT_FOUND)

    mb.h4("التقارير (Reports)")
    reports = data.get("reports", [])
    mb.para(f"عدد التقارير المعرَّفة: {len(reports)} — راجع الفصل 8 للكتالوج الكامل بالأسماء ونماذج المصدر." if reports
            else "لا توجد تقارير QWeb في هذه الوحدة.")

    mb.h4("المهام المجدولة (Cron Jobs)")
    crons = data.get("cron_jobs", [])
    if crons:
        mb.table(
            ["معرّف المهمة", "الاسم", "النموذج", "التكرار", "نشط"],
            [[c["id"], c["name"], c.get("model_id") or "—",
              f"{c.get('interval_number','—')} {c.get('interval_type','')}", c.get("active") or "—"] for c in crons],
            caption=f"المهام المجدولة (ir.cron) في وحدة {key}",
        )
    else:
        mb.para("لا توجد مهام مجدولة في هذه الوحدة.")

    sequences = data.get("sequences", [])
    if sequences:
        mb.h4("التسلسلات الرقمية (Sequences)")
        mb.table(
            ["معرّف التسلسل", "الاسم", "الرمز (code)", "البادئة", "عدد الخانات"],
            [[s["id"], s["name"], s.get("code") or "—", s.get("prefix") or "—", s.get("padding") or "—"] for s in sequences],
            caption=f"التسلسلات الرقمية (ir.sequence) في وحدة {key}",
        )

    mb.h4("التكاملات وواجهات البرمجة (Integrations & API)")
    external_api_modules = {"c7_credit_bureau", "l10n_eg_eta_invoice", "c13_tax_xml_export"}
    if key in external_api_modules:
        mb.para("تتكامل هذه الوحدة مع واجهة برمجية خارجية. بيانات الاعتماد والنقاط الطرفية (Endpoints) الفعلية: " + NOT_FOUND)
    else:
        mb.para("لا تكامل خارجي مباشر مرصود لهذه الوحدة؛ التكامل يقتصر على نماذج أودو الداخلية عبر ORM.")

    mb.h4("الإعداد (Configuration)")
    mb.para(f"إصدار الوحدة: {manifest.get('version', '—')} — راجع الفصل 4/5 لصفحة الإعداد الوظيفية المرتبطة إن وُجدت.")

    mb.h4("النشر (Deployment)")
    mb.para("ترتيب التثبيت الإلزامي محكوم بقائمة depends أعلاه؛ راجع الفصل 2 لخطوات النشر العامة.")

    mb.h4("الاختبار (Testing)")
    mb.para("خطة اختبار رسمية موثّقة لهذه الوحدة تحديدًا: " + NOT_FOUND)

    mb.h4("التحسينات المستقبلية (Future Enhancements)")
    mb.para(narrative["future"])
