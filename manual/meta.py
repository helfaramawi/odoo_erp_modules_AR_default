"""Shared cover-page / document-control metadata for the manual.

Values marked with a leading '__' placeholder-style string are intentionally
left for the client/vendor to fill in (real names, dates, signatures). All
other values are grounded in the actual repository (see
odoo_deployment_ar/addons/README.md and the module manifests).
"""

META = dict(
    system_name="نظام الديوان العام المالي واللوجستي المخصص على أوديو",
    system_subtitle="Odoo 17 — محافظة بورسعيد، جمهورية مصر العربية",
    version="1.0.0",
    doc_number="PAI-PSG-SYS-MANUAL-001",
    revision_no="A",
    issue_date="2026-07-08",
    prepared_by="Paradise AI Solutions — فريق التوثيق الفني",
    reviewed_by="__________________ (بيانات تُستكمل من العميل)",
    approved_by="__________________ (بيانات تُستكمل من العميل)",
    vendor="Paradise AI Solutions",
    client="محافظة بورسعيد — الديوان العام",
    classification="سري — للاستخدام الداخلي الرسمي فقط",
    confidentiality_statement=(
        "هذا المستند وما يحتويه من معلومات فنية وتنظيمية هو ملكية فكرية مشتركة "
        "بين شركة Paradise AI Solutions ومحافظة بورسعيد. يُحظر نسخ أو تصوير أو "
        "توزيع أو نشر أي جزء من هذا الدليل، كليًا أو جزئيًا، لأي جهة خارج نطاق "
        "الاستخدام الرسمي المصرح به دون إذن كتابي مسبق من الجهتين."
    ),
    vendor_logo_placeholder="شعار Paradise AI Solutions هنا",
    customer_logo_placeholder="شعار محافظة بورسعيد هنا",
)

REVISIONS = [
    ["A", "2026-07-08", "الإصدار الأول للدليل — تغطية كاملة للوحدات المالية ووحدات سلسلة التوريد المخصصة", "Paradise AI Solutions", "مسودة للمراجعة"],
]

APPROVALS = [
    ["إعداد المستند (Prepared By)", "فريق التوثيق الفني — Paradise AI Solutions", "", ""],
    ["المراجعة الفنية (Technical Review)", "__________________", "", ""],
    ["مراجعة الجودة (QA Review)", "__________________", "", ""],
    ["الاعتماد النهائي (Final Approval)", "مدير عام الديوان العام لمحافظة بورسعيد", "", ""],
]

DISTRIBUTION = [
    "السيد/ة المحافظ — مكتب المحافظ",
    "مدير عام الديوان العام",
    "الإدارة المركزية للشؤون المالية",
    "الإدارة العامة لتكنولوجيا المعلومات",
    "لجنة تسيير المشروع (Project Steering Committee)",
    "فريق Paradise AI Solutions — إدارة المشروع والدعم الفني",
    "الجهاز المركزي للمحاسبات (نسخة اطلاع عند الطلب)",
]
