# -*- coding: utf-8 -*-
{
    'name': 'وكيل توصية إعادة توزيع الاعتمادات',
    'version': '17.0.1.0.0',
    'summary': 'Budget Reallocation Recommendation Agent',
    'description': 'وكيل توصية إعادة توزيع الاعتمادات بناءً على العجز والفائض المتوقع دون تنفيذ فعلي.',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': ['base', 'mail', 'port_said_budget_planning', 'port_said_commitment', 'port_said_daftar55'],
    'data': [
        'security/ir.model.access.csv',
        'views/budget_reallocation_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
