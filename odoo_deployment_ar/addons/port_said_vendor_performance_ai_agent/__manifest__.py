# -*- coding: utf-8 -*-
{
    'name': 'وكيل تقييم كفاءة الموردين بعد التوريد',
    'version': '17.0.1.0.1',
    'summary': 'Vendor Performance Scoring Agent',
    'description': '''
وكيل تقييم كفاءة الموردين بعد التوريد.
يقوم بحساب درجة المورد بناءً على جودة التوريد، الالتزام بالوقت، سجل الجزاءات، وحجم التعامل الناجح.
تظهر النتيجة على شاشة المورد وتستخدم كمرجع رقابي عند قرارات الشراء والترسية.
''',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'purchase',
        'stock',
        'port_said_scm_warehouse',
        'port_said_vendor_penalty_ai_agent',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/vendor_performance_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
