# -*- coding: utf-8 -*-
{
    'name': 'وكيل مطابقة دفتر 55 مع القيود المحاسبية',
    'version': '17.0.1.0.0',
    'summary': 'Daftar55 to Accounting Reconciliation Agent',
    'description': 'وكيل رقابي لمطابقة سجلات دفتر 55 مع القيود المحاسبية الناتجة عنها.',
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': ['base', 'mail', 'account', 'demo_gov_daftar55', 'demo_gov_cash_books', 'demo_gov_ai_agents_menu',],
    'data': [
        'security/ir.model.access.csv',
        'views/daftar55_reconcile_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
