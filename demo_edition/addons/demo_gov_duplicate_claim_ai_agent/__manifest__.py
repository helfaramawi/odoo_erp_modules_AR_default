# -*- coding: utf-8 -*-
{
    'name': 'وكيل كشف تكرار المستندات والمطالبات',
    'version': '17.0.1.0.0',
    'summary': 'Duplicate Claims & Document Fraud Agent',
    'description': '''
وكيل رقابي لاكتشاف تكرار المستندات والمطالبات.
يعتمد على checksum للملفات، ومطابقة المورد، المبلغ، التاريخ، رقم الفاتورة أو المرجع، وتشابه اسم الملف.
''',
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': [
        'base',
        'mail',
        'account',
        'purchase',
        'demo_gov_dossier',
        'demo_gov_daftar55', 'demo_gov_ai_agents_menu',],
    'data': [
        'security/ir.model.access.csv',
        'views/duplicate_claim_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
