{
    'name': 'طلب الاحتياج — التدبير والمشتريات',
    'category': 'الخدمات الحكومية التجريبية/المشتريات',
    'summary': 'C-SCM-01: Purchase Requisition with Budget Commitment Auto-Integration',
    'version': '17.0.1.0.0',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['purchase', 'demo_gov_commitment', 'mail',
        'uom', 'demo_branding'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/requisition_views.xml',
        'reports/requisition_report.xml',
        'reports/requisition_template.xml',
    ],
    'installable': True,
}