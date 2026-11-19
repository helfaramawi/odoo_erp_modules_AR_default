# -*- coding: utf-8 -*-
{
    'name': 'وكيل كشف تضارب المصالح في الموردين واللجان',
    'version': '17.0.1.0.0',
    'summary': 'Governance & Anti-Corruption Agent for supplier/committee conflict risk detection',
    'description': '''
وكيل حوكمة وشفافية يقوم بفحص العلاقات المحتملة بين الموردين وأعضاء لجان الشراء/الفحص/البت.
الهدف هو إصدار تنبيه تضارب مصالح محتمل وليس إثبات مخالفة.
''',
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': ['base','mail','hr','purchase','procurement_committee','procurement_adjudication', 'demo_gov_ai_agents_menu',],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_cron.xml',
        'views/conflict_interest_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
