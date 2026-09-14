# -*- coding: utf-8 -*-
{
    'name': 'وكيل الملخص التنفيذي اليومي للقيادة العليا',
    'version': '17.0.1.0.0',
    'summary': 'Executive Daily Briefing Agent',
    'description': '''
وكيل ملخص تنفيذي يومي للقيادة العليا.
يجمع مؤشرات المخاطر والاستثناءات من الموازنة، الارتباطات، دفتر 55، الشيكات، الجزاءات، المشتريات، والفواتير، ويكتب ملخصًا عربيًا تنفيذيًا مع إجراءات مطلوبة وروابط للسجلات.
''',
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': [
        'base',
        'mail',
        'demo_gov_dashboard',
        'demo_gov_budget_planning',
        'demo_gov_commitment',
        'demo_gov_daftar55',
        'demo_gov_cheques',
        'demo_gov_penalties',
        'procurement_adjudication', 'demo_gov_ai_agents_menu',],
    'data': [
        'security/ir.model.access.csv',
        'views/executive_briefing_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
