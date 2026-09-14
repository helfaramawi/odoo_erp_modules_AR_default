# -*- coding: utf-8 -*-
{
    'name': 'وكيل مراجعة الالتزام القانوني لمستندات المشتريات',
    'version': '17.0.1.0.0',
    'summary': 'Procurement Legal Compliance Agent',
    'description': 'وكيل رقابي لمراجعة اكتمال المستندات القانونية لعمليات المشتريات.',
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': ['base', 'mail', 'purchase', 'procurement_committee', 'procurement_adjudication', 'demo_gov_dossier', 'demo_gov_ai_agents_menu',],
    'data': ['security/ir.model.access.csv', 'views/procurement_legal_compliance_views.xml', 'data/cron.xml'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
