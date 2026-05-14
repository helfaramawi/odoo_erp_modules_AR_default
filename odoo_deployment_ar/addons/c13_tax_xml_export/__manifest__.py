{
    'name': 'Tax Filing XML Export / تصدير ملف الضريبة XML',
    'version': '17.0.1.0.0',
    'category': 'الديوان العام/المحاسبة',
    'summary': 'Generate signed tax filing XML for government portal submission (schema v3.2)',
    'author': 'ERP Migration Team',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/tax_xml_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}