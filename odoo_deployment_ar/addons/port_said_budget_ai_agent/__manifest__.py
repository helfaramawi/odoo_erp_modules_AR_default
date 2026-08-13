# -*- coding: utf-8 -*-
{
    'name': 'وكيل مراقبة الموازنة الذكي - بورسعيد',
    'version': '17.0.1.0.0',
    'summary': 'مراقبة الموازنة والتنبؤ بالاستنفاد وإصدار التنبيهات والتقارير الحكومية العربية',
    'description': '''
Port Said Budget AI Monitoring Agent
====================================
Daily budget monitoring agent for Port Said Governorate Odoo deployment.

Main features:
- Daily cron job to monitor active budget plans.
- Risk calculation based on execution, commitment exposure, available amount, and predicted exhaustion.
- Alert history model with audit trail.
- Odoo activities and email notifications.
- Weekly Arabic governmental-style report.
- Optional LLM hook for Arabic message polishing without allowing the LLM to calculate financial values.
''',
    'author': 'Paradise AI Solutions',
    'category': 'Accounting/Budgeting',
    'depends': [
        'base',
        'mail',
        'port_said_budget_planning',
        'port_said_commitment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/budget_alert_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
