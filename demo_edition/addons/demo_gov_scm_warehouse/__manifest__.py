{
    "name": "لجنة الفحص والمخازن",
    "category": "الخدمات الحكومية التجريبية/المخازن والمستودعات",
    "summary": "C-SCM-03: Inspection Committee + Warehouse Forms (نموذج 12 + نموذج 1)",
    "version": "17.0.1.0.0",
    "author": "Enterprise Solutions Demo",
    "license": "LGPL-3",
    "depends": ["stock","purchase","uom","demo_gov_scm_purchase_bridge","demo_gov_dossier", "demo_branding"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "views/warehouse_forms_views.xml",
        "reports/inspection_report.xml",
        "reports/inspection_template.xml",
    ],
    "installable": True,
}
