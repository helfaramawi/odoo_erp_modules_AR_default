# -*- coding: utf-8 -*-
{
    'name': 'وكيل أتمتة الارتباطات من الطلب للتجنيب',
    'version': '17.0.1.0.0',
    'summary': 'أتمتة اعتماد وتجنيب الارتباطات الصغيرة مع تقييم مخاطر وسجل قرارات',
    'description': '''
وكيل أتمتة الارتباطات من الطلب للتجنيب
=====================================
يقوم هذا الموديول بالتدخل بعد اعتماد طلب الشراء/الاحتياج وبعد إنشاء الارتباط الحالي،
ثم يقرر هل يتم اعتماد وتجنيب الارتباط تلقائياً أم تحويله لمراجعة بشرية.
''',
    'author': 'Paradise AI Solutions',
    'category': 'Accounting/Government',
    'depends': [
        'base',
        'mail',
        'port_said_scm_requisition',
        'port_said_commitment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/commitment_agent_log_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
