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
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': [
        'base',
        'mail',
        'purchase',
        'stock',
        'demo_gov_scm_warehouse',
        'demo_gov_vendor_penalty_ai_agent', 'demo_gov_ai_agents_menu',],
    'data': [
        'security/ir.model.access.csv',
        'views/vendor_performance_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
