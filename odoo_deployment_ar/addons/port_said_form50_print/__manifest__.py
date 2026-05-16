# -*- coding: utf-8 -*-
{
    'name': 'استمارة 50 ع.ح — طبقة الطباعة الرسمية',
    'summary': 'C-FM-03: Form 50 Official Print Layer — Port Said Governorate',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'author': 'Paradise Integrated Solutions',
    'website': 'https://paradise.solutions.com',
    'license': 'LGPL-3',
    'depends': ['port_said_daftar55', 'port_said_dossier'],
    'data': [
        'security/ir.model.access.csv',
        'views/form50_views.xml',
        'views/form50_reprint_wizard_views.xml',
        'reports/form50_report.xml',
        'reports/form50_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'port_said_form50_print/static/src/css/form50_print.css',
        ],
    },
    'installable': True,
    'application': False,
}
