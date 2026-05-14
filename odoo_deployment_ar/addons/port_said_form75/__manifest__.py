{
    'category': 'الديوان العام/المحاسبة',
    'name': 'استمارة 75 - الحسابات الشهرية والختامية',
    'summary': 'C-FM-04: Form 75 Monthly/Annual Closing with 3-Stage Sequential Approval',
    'version': '17.0.1.0.0',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': ['port_said_form69', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/form75_views.xml',
        'reports/form75_report.xml',
        'reports/form75_template.xml',
    ],
    'installable': True,
}
