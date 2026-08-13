# -*- coding: utf-8 -*-
{
    'name': 'وكيل مطابقة دفتر 55 مع القيود المحاسبية',
    'version': '17.0.1.0.0',
    'summary': 'Daftar55 to Accounting Reconciliation Agent',
    'description': 'وكيل رقابي لمطابقة سجلات دفتر 55 مع القيود المحاسبية الناتجة عنها.',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': ['base', 'mail', 'account', 'port_said_daftar55', 'port_said_cash_books'],
    'data': [
        'security/ir.model.access.csv',
        'views/daftar55_reconcile_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
