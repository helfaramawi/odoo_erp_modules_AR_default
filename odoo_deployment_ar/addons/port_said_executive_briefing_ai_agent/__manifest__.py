# -*- coding: utf-8 -*-
{
    'name': 'وكيل الملخص التنفيذي اليومي للقيادة العليا',
    'version': '17.0.1.0.0',
    'summary': 'Executive Daily Briefing Agent',
    'description': '''
وكيل ملخص تنفيذي يومي للقيادة العليا.
يجمع مؤشرات المخاطر والاستثناءات من الموازنة، الارتباطات، دفتر 55، الشيكات، الجزاءات، المشتريات، والفواتير، ويكتب ملخصًا عربيًا تنفيذيًا مع إجراءات مطلوبة وروابط للسجلات.
''',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'portsaid_dashboard',
        'port_said_budget_planning',
        'port_said_commitment',
        'port_said_daftar55',
        'port_said_cheques',
        'port_said_penalties',
        'procurement_adjudication',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/executive_briefing_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
