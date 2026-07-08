"""Cover-page / document-control metadata for the Setup & Configuration
Handbook — a distinct deliverable from the System Manual (manual/meta.py):
this one is a reverse-engineering-grade technical handbook that cites actual
files, ACL rows, and code facts rather than end-user functional narrative.
"""

NOT_FOUND = "لم يتم العثور على هذه المعلومة داخل النظام ويجب استكمالها أثناء مرحلة التوثيق."

META = dict(
    system_name="دليل الإعداد والتهيئة الرسمي — نظام الديوان العام لمحافظة بورسعيد",
    system_subtitle="Setup & Configuration Handbook — Odoo 17 — إعادة هندسة عكسية كاملة للتخصيصات",
    version="1.0.0",
    doc_number="PAI-PSG-CFG-HANDBOOK-001",
    revision_no="A",
    issue_date="2026-07-08",
    prepared_by="Paradise AI Solutions — فريق الهندسة العكسية والتوثيق الفني",
    reviewed_by="__________________ (بيانات تُستكمل من العميل)",
    approved_by="__________________ (بيانات تُستكمل من العميل)",
    vendor="Paradise AI Solutions",
    client="محافظة بورسعيد — الديوان العام",
    classification="سري — للاستخدام الداخلي الرسمي فقط",
    confidentiality_statement=(
        "هذا المستند وما يحتويه من معلومات فنية تفصيلية (بما يشمل أسماء الجداول "
        "والحقول وقواعد الأمان) هو ملكية فكرية مشتركة بين شركة Paradise AI "
        "Solutions ومحافظة بورسعيد. يُحظر نسخه أو توزيعه خارج نطاق الاستخدام "
        "الرسمي المصرح به دون إذن كتابي مسبق من الجهتين."
    ),
    vendor_logo_placeholder="شعار Paradise AI Solutions هنا",
    customer_logo_placeholder="شعار محافظة بورسعيد هنا",
)

REVISIONS = [
    ["A", "2026-07-08", "الإصدار الأول — إعادة هندسة عكسية كاملة لكل الوحدات المخصصة، الأمان، قاعدة البيانات، وسير العمل", "Paradise AI Solutions", "مسودة للمراجعة"],
]

APPROVALS = [
    ["إعداد المستند (Prepared By)", "فريق الهندسة العكسية — Paradise AI Solutions", "", ""],
    ["المراجعة الفنية (Technical Review)", "__________________", "", ""],
    ["مراجعة أمن المعلومات (Security Review)", "__________________", "", ""],
    ["الاعتماد النهائي (Final Approval)", "مدير عام الديوان العام لمحافظة بورسعيد", "", ""],
]

DISTRIBUTION = [
    "الإدارة العامة لتكنولوجيا المعلومات",
    "فريق قواعد البيانات (DBA)",
    "فريق أمن المعلومات",
    "فريق Paradise AI Solutions — إدارة المشروع والتطوير",
    "المدقق الداخلي (نسخة اطلاع عند الطلب)",
]
