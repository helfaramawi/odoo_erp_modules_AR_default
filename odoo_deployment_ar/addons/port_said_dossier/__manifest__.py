{
    'name': 'الاضابير - نظام الأرشفة (استمارة 101 ساير)',
    'summary': 'C-FM-08: Dossier Archive System – Form 101 ساير with 9-attachment enforcement',
    'version': '19.0.1.0.0',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': ['port_said_daftar55'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/dossier_views.xml',
        'reports/dossier_report.xml',
        'reports/dossier_template.xml',
    ],
    'installable': True,
}
