# -*- coding: utf-8 -*-
{
    'name': 'مجموعة وكلاء الذكاء الاصطناعي',
    'version': '17.0.1.0.0',
    'summary': 'AI Agents Menu Group',
    'description': '''
تجميع قوائم وكلاء الذكاء الاصطناعي في قائمة رئيسية واحدة باسم مجموعة وكلاء AI.
يقوم بتجميع الوكلاء المثبتين فعليًا دون الحاجة لوضع كل الوكلاء كاعتمادات مباشرة.
''',
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/ai_agents_menu_views.xml',
        'data/server_actions.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
