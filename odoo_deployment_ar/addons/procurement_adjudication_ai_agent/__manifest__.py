# -*- coding: utf-8 -*-
{
    'name': 'وكيل تحليل العروض في البت الفني والمالي',
    'version': '17.0.1.0.0',
    'summary': 'تحليل فني ومالي للعروض وإعداد مسودات محاضر البت وفق آلية المظروفين',
    'description': '''
وكيل تحليل العروض في البت الفني والمالي
=======================================
يقوم بتحليل العروض عند فتح المظاريف الفنية والمالية، وتجهيز مسودات عربية رسمية للجنة.
''',
    'author': 'Paradise AI Solutions',
    'category': 'Purchases/Government',
    'depends': [
        'base',
        'mail',
        'procurement_adjudication',
        'procurement_committee',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/adjudication_agent_log_views.xml',
        'views/adjudication_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
