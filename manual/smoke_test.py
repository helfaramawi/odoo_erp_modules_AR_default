import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (new_document, add_header_footer, add_cover_page,
                     add_document_control, add_toc_section, ManualBuilder, Numbering)

doc = new_document()
meta = dict(
    system_name="نظام الديوان العام المالي واللوجستي المخصص",
    system_subtitle="مبني على Odoo 17 — الديوان العام لمحافظة بورسعيد",
    version="1.0.0",
    doc_number="PAI-PSG-SYS-001",
    revision_no="A",
    issue_date="2026-07-08",
    prepared_by="Paradise AI Solutions — فريق التوثيق الفني",
    reviewed_by="__________________",
    approved_by="__________________",
    vendor="Paradise AI Solutions",
    client="محافظة بورسعيد — الديوان العام",
    classification="سري — للاستخدام الداخلي الرسمي فقط",
    confidentiality_statement="هذا المستند ملك لمحافظة بورسعيد و Paradise AI Solutions. يُمنع نسخه أو توزيعه دون إذن كتابي مسبق.",
    vendor_logo_placeholder="شعار Paradise AI Solutions",
    customer_logo_placeholder="شعار محافظة بورسعيد",
)
add_cover_page(doc, meta)
num = Numbering()
mb = ManualBuilder(doc, num)
add_document_control(doc, mb,
    revisions=[["A", "2026-07-08", "الإصدار الأول", "Paradise AI", "معتمد للمراجعة"]],
    approvals=[["إعداد", "فريق باراديس", "", ""], ["اعتماد", "مدير الديوان العام", "", ""]],
    distribution=["مدير عام الديوان", "إدارة تكنولوجيا المعلومات", "فريق باراديس"])
add_toc_section(doc, mb)

mb.h1("المقدمة")
mb.h2("الغرض من الدليل")
mb.para("هذا نص تجريبي للتأكد من عمل البنية التحتية لتوليد المستند.")
mb.screenshot("شاشة الصفحة الرئيسية للنظام")
mb.field_table([
    {"name": "sequence_number", "arabic": "رقم المسلسل", "desc": "رقم تسلسلي فريد", "mandatory": True, "default": "تلقائي", "validation": "فريد", "example": "2026/001", "related": "port_said.daftar55"}
])
mb.h1("الهيكل التنظيمي")
mb.h2("الأقسام")
mb.para("نص آخر لاختبار ترقيم الفصل الثاني.")

add_header_footer(doc)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "smoke_test.docx")
doc.save(out)
print("OK ->", out)
