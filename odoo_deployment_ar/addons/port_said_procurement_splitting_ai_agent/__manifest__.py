# -*- coding: utf-8 -*-
{
    'name': 'وكيل مراقبة تجزئة المشتريات',
    'version': '17.0.1.0.0',
    'summary': 'Procurement Splitting Detection Agent',
    'description': '''
وكيل رقابي لاكتشاف تجزئة المشتريات المحتملة لتفادي حدود الاعتماد.
يفحص أوامر الشراء وطلبات الاحتياج والعمليات القريبة من حد الموافقة خلال فترة زمنية قصيرة.
''',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'purchase',
        'port_said_scm_requisition',
        'port_said_commitment',
        'procurement_adjudication',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/procurement_splitting_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
