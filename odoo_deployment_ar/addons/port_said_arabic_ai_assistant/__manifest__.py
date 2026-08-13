# -*- coding: utf-8 -*-
{
    'name': 'مساعد لغوي عربي داخل Odoo — اسألني بالعربي',
    'version': '17.0.1.2.1',
    'summary': 'Arabic dynamic read-only assistant with robust Ollama JSON fallback',
    'description': 'Fixed version: forces Ollama JSON format, safer local fallback, and better vendor routing.',
    'category': 'Dashboard/Egypt Government',
    'author': 'Paradise AI Solutions',
    'depends': ['base', 'web', 'mail', 'portsaid_dashboard'],
    'data': [
        'security/ir.model.access.csv',
        'views/ai_assistant_views.xml',
        'views/ai_assistant_menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
