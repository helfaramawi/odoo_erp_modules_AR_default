{
    'name': 'النقل والندب والإعارة والترقيات',
    'summary': 'C-HR-06: Secondment/loan/transfer tracking with 30-day expiry alerts, promotion committee workflow, settlement re-appointment approvals',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الموارد البشرية',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_hr_employee', 'demo_gov_hr_training'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/cron_data.xml',
        'views/hr_transfer_views.xml',
        'views/hr_promotion_views.xml',
        'views/hr_transfer_menu.xml',
    ],
    'installable': True,
    'application': False,
}
