# -*- coding: utf-8 -*-
{
    'name': 'تجميع البرامج المخصصة في القائمة الجانبية',
    'version': '17.0.1.0.0',
    'summary': 'Group all c* custom addon menus under one sidebar parent menu',
    'description': '''
يقوم هذا الموديول بتجميع كل القوائم التابعة للوحدات التي تبدأ بحرف c
مثل c1_purchase_approval_matrix و c2_batch_posting و c13_tax_xml_export
داخل مجموعة واحدة باسم: مجموعة البرامج المخصصة.
''',
    'category': 'Tools/Menu',
    'author': 'Paradise AI Solutions',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_programs_menu_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
