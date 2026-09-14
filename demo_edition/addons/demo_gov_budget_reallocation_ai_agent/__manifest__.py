# -*- coding: utf-8 -*-
{
    'name': 'وكيل توصية إعادة توزيع الاعتمادات',
    'version': '17.0.1.0.0',
    'summary': 'Budget Reallocation Recommendation Agent',
    'description': 'وكيل توصية إعادة توزيع الاعتمادات بناءً على العجز والفائض المتوقع دون تنفيذ فعلي.',
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': ['base', 'mail', 'demo_gov_budget_planning', 'demo_gov_commitment', 'demo_gov_daftar55', 'demo_gov_ai_agents_menu',],
    'data': [
        'security/ir.model.access.csv',
        'views/budget_reallocation_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
