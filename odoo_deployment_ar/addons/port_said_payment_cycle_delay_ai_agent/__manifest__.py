# -*- coding: utf-8 -*-
{
    'name': 'وكيل مراقبة التأخيرات الإدارية في دورة الصرف',
    'version': '17.0.1.0.0',
    'summary': 'Payment Cycle Bottleneck Agent',
    'description': '''
وكيل رقابي لمراقبة التأخيرات الإدارية في دورة الصرف.
يتابع الإضبارة، دفتر 55، أوامر الدفع، الشيكات، والقيود المحاسبية، ويكشف مراحل التعطل طبقًا لقواعد SLA.
''',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'account',
        'port_said_daftar55',
        'port_said_dossier',
        'port_said_cheques',
        'port_said_cash_books',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_cycle_delay_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
