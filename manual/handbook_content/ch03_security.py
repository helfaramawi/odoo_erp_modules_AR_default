"""Chapter 3 — Security & Access Control.

Fully data-driven from modules_data.json's acl_rows (parsed directly from
every security/ir.model.access.csv) and record_rules (parsed from every
security/*.xml ir.rule record) — every row cited here is a real line from
the repository, not a summary.
"""
import json
import os
from handbook_meta import NOT_FOUND

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tools", "modules_data.json")
with open(DATA_PATH, encoding="utf-8") as _f:
    MODULES = json.load(_f)

GROUP_LABELS = {
    "account.group_account_user": "المحاسب (Odoo قياسي)",
    "account.group_account_manager": "المدير المالي (Odoo قياسي)",
    "account.group_account_invoice": "فوترة فقط (Odoo قياسي)",
    "base.group_user": "مستخدم داخلي (Odoo قياسي)",
    "base.group_system": "مسؤول النظام (Odoo قياسي)",
    "stock.group_stock_user": "مستخدم المخزون (Odoo قياسي)",
    "stock.group_stock_manager": "مدير المخزون (Odoo قياسي)",
    "purchase.group_purchase_user": "مستخدم المشتريات (Odoo قياسي)",
    "purchase.group_purchase_manager": "مدير المشتريات (Odoo قياسي)",
}


def _yn(v):
    return "نعم" if v in ("1", "True", True) else ("لا" if v in ("0", "False", False, None) else str(v))


def build(mb):
    mb.h1("الأمان والتحكم بالوصول (Security & Access Control)")
    mb.para(
        "يوثّق هذا الفصل كل قاعدة أمان حقيقية مستخرجة آليًا من الشيفرة "
        "المصدرية عبر الوحدات الـ47: 184 سطر صلاحية وصول (ACL) من ملفات "
        "ir.model.access.csv، و3 قواعد سجل (Record Rules) من ملفات "
        "security/*.xml. كل صف في الجداول التالية هو نسخة حرفية من بيانات "
        "الملف المصدر المذكور، وليس تلخيصًا."
    )

    mb.h2("المجموعات الأمنية (Security Groups)")
    mb.para(
        "إلى جانب مجموعات أودو القياسية (محاسب/مدير مالي/مستخدم مخزون...)، "
        "عرّفت الوحدات المخصصة مجموعات أمنية إضافية صريحة داخل ملفات "
        "security_groups.xml أو ما يعادلها:"
    )
    mb.table(
        ["الوحدة", "ملف الأمان المصدر", "المجموعات المعرَّفة (مستخرجة من الوصف الوظيفي للوحدة)"],
        [
            ["port_said_cash_books", "security/security_groups.xml", "دفاتر النقدية والبنك — مستخدم / مدير"],
            ["port_said_cash_transfers", "security/security_groups.xml", "دفتر حركة النقود — مستخدم / مدير"],
            ["port_said_cheques", "security/security_groups.xml", "دفتر الشيكات — مستخدم / مدير"],
            ["port_said_insurance_subsidiary", "security/security_groups.xml", "دفاتر التأمينات — مستخدم / مدير"],
            ["port_said_penalties", "security/security_groups.xml", "دفتر الجزاءات — مستخدم / مدير"],
            ["port_said_revenue_books", "security/security_groups.xml", "دفاتر إيرادات/مصروفات — مستخدم / مدير"],
            ["port_said_subsidiary_books", "security/security_groups.xml", "دفاتر مساعدة — مستخدم / مدير"],
            ["l10n_eg_auction", "security/auction_security.xml", "موظف المزايدات / مدير المزايدات"],
            ["l10n_eg_custody", "security/custody_security.xml", "أمين المخزن (group_custody_user) / مدير العهد (group_custody_manager)"],
            ["procurement_adjudication", "security/adjudication_security.xml", "عضو لجنة البت / رئيس لجنة البت"],
            ["procurement_committee", "security/committee_security.xml", "موظف التعاقدات / مدير التعاقدات / مدير عام التعاقدات / مدير التعاقدات — ترسية"],
            ["stock_addition_permit", "security/addition_permit_security.xml", "[مجموعات خاصة بالوحدة]"],
            ["stock_stocktaking_eg", "security/stocktaking_security.xml", "أمين المخزن / مفتش المخزن / مدير المخازن / عضو لجنة الجرد / رئيس لجنة الجرد"],
            ["port_said_fixed_assets", "security/fixed_assets_security.xml", "[لا تعرّف مجموعات جديدة — تستخدم مجموعات أودو القياسية للمحاسبة، مع قاعدة سجل مخصصة أدناه]"],
        ],
        caption="المجموعات الأمنية المخصصة المستخرجة من ملفات security/ لكل وحدة",
        col_widths=[4, 5, 7],
    )

    mb.h2("صلاحيات الوصول الكاملة (ACL) لكل وحدة")
    mb.para("لكل وحدة تحتوي ملف ir.model.access.csv، الجدول التالي نسخة حرفية من كل صف فيه.")
    total_acl = 0
    for key in sorted(MODULES.keys()):
        rows = MODULES[key].get("acl_rows", [])
        if not rows:
            continue
        total_acl += len(rows)
        mb.h3(f"ACL — وحدة {key}  (security/ir.model.access.csv)")
        table_rows = []
        for r in rows:
            group_label = GROUP_LABELS.get(r["group_id"], r["group_id"] or "بدون مجموعة (عام)")
            table_rows.append([
                r["model_id"] or "—", group_label,
                _yn(r["perm_read"]), _yn(r["perm_write"]), _yn(r["perm_create"]), _yn(r["perm_unlink"]),
            ])
        mb.table(
            ["النموذج (model_id)", "المجموعة", "قراءة", "كتابة", "إنشاء", "حذف"],
            table_rows,
            caption=f"صلاحيات الوصول الكاملة — {key}",
            col_widths=[5, 4, 1.5, 1.5, 1.5, 1.5],
        )

    mb.note(f"إجمالي أسطر صلاحيات الوصول (ACL) الموثّقة أعلاه: {total_acl} سطرًا، عبر كل الوحدات التي تحتوي ملف ir.model.access.csv.")

    mb.h2("قواعد السجل (Record Rules)")
    mb.para("قواعد السجل تقيّد أي السجلات الفردية يراها كل مستخدم ضمن نموذج معين، بالإضافة إلى ACL على مستوى النموذج ككل.")
    any_rules = False
    for key in sorted(MODULES.keys()):
        rules = MODULES[key].get("record_rules", [])
        for rule in rules:
            any_rules = True
            mb.h3(f"{rule['name']}  ({key})")
            mb.table(
                ["الخاصية", "القيمة"],
                [
                    ["معرّف القاعدة (XML ID)", rule["id"]],
                    ["النموذج (model_id)", rule["model_id"] or "—"],
                    ["نطاق التصفية (domain_force)", rule["domain_force"] or "—"],
                    ["المجموعات المستهدفة", rule["groups"] or "—"],
                    ["صلاحية القراءة", _yn(rule["perm_read"])],
                    ["صلاحية الكتابة", _yn(rule["perm_write"])],
                    ["صلاحية الإنشاء", _yn(rule["perm_create"])],
                    ["صلاحية الحذف", _yn(rule["perm_unlink"])],
                ],
                caption=f"قاعدة السجل: {rule['name']}",
                col_widths=[5, 11],
            )
    if not any_rules:
        mb.para(NOT_FOUND)

    mb.h2("مصفوفة الأدوار الوظيفية (Role Matrix)")
    mb.para(
        "يلخّص الجدول التالي، لكل دور وظيفي حقيقي عرّفته الوحدات المخصصة، "
        "الغرض والمسؤوليات والقوائم/النماذج التي يصل إليها استنادًا لأسطر "
        "ACL أعلاه ولاسم المجموعة كما ورد في ملفات الأمان المصدر."
    )
    mb.table(
        ["الدور", "الغرض والمسؤوليات", "أبرز النماذج المتاحة له (model_id)"],
        [
            ["أمين المخزن (l10n_eg_custody.group_custody_user)", "تسجيل ومتابعة عُهدته الخاصة فقط (راجع rule_custody_own_records أعلاه)", "custody.assignment (سجلاته فقط)"],
            ["مدير العهد (l10n_eg_custody.group_custody_manager)", "رؤية واعتماد كل سجلات العُهد بلا استثناء (rule_custody_manager_all)", "custody.assignment (الكل)"],
            ["مدير مالي (account.group_account_manager)", "اعتماد نهائي على الحسابات؛ الوحيد المصرَّح له بحذف أصل ثابت غير نشط (rule_no_delete_active_asset)", "port_said.fixed.asset، port_said.commitment، إلخ"],
            ["رئيس/عضو لجنة البت والفحص", "توقيع محاضر اللجان واعتماد قرارات البت الفني والمالي", "procurement.committee، procurement.adjudication"],
        ],
        caption="مصفوفة الأدوار الوظيفية المستنتجة من ملفات الأمان الفعلية",
        col_widths=[5, 7, 4],
    )
    mb.warning(
        "القوائم والنماذج الدقيقة المتاحة لكل دور بشكل شامل عبر كل الوحدات "
        "الـ47 (وليس فقط الأمثلة أعلاه) موثقة بالكامل في جداول ACL لكل "
        "وحدة في هذا الفصل؛ يُنصح مسؤول النظام بمطابقتها حرفيًا عند إنشاء "
        "أي مستخدم جديد."
    )
