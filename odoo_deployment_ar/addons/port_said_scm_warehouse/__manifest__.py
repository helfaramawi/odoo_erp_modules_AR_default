{
    'category': 'الديوان العام/المخازن',
    "name": "لجنة الفحص والمخازن",
    "summary": "C-SCM-03: Inspection Committee + Warehouse Forms (نموذج 12 + نموذج 1)",
    "version": "17.0.1.0.0",
    "author": "Paradise Integrated Solutions",
    "license": "LGPL-3",
    "depends": ["stock","purchase","uom","port_said_scm_purchase_bridge","port_said_dossier"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "views/warehouse_forms_views.xml",
        "reports/inspection_report.xml",
        "reports/inspection_template.xml",
    ],
    "installable": True,
}
