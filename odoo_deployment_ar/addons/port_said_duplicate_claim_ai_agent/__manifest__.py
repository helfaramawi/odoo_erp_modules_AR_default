# -*- coding: utf-8 -*-
{
    'name': 'وكيل كشف تكرار المستندات والمطالبات',
    'version': '17.0.1.0.0',
    'summary': 'Duplicate Claims & Document Fraud Agent',
    'description': '''
وكيل رقابي لاكتشاف تكرار المستندات والمطالبات.
يعتمد على checksum للملفات، ومطابقة المورد، المبلغ، التاريخ، رقم الفاتورة أو المرجع، وتشابه اسم الملف.
''',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'account',
        'purchase',
        'port_said_dossier',
        'port_said_daftar55',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/duplicate_claim_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
