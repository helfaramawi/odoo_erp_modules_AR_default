# -*- coding: utf-8 -*-
{
    'name': 'وكيل مراجعة الالتزام القانوني لمستندات المشتريات',
    'version': '17.0.1.0.0',
    'summary': 'Procurement Legal Compliance Agent',
    'description': 'وكيل رقابي لمراجعة اكتمال المستندات القانونية لعمليات المشتريات.',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': ['base', 'mail', 'purchase', 'procurement_committee', 'procurement_adjudication', 'port_said_dossier'],
    'data': ['security/ir.model.access.csv', 'views/procurement_legal_compliance_views.xml', 'data/cron.xml'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
