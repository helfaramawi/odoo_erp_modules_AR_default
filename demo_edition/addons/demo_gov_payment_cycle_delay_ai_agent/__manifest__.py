# -*- coding: utf-8 -*-
{
    'name': 'وكيل مراقبة التأخيرات الإدارية في دورة الصرف',
    'version': '17.0.1.0.0',
    'summary': 'Payment Cycle Bottleneck Agent',
    'description': '''
وكيل رقابي لمراقبة التأخيرات الإدارية في دورة الصرف.
يتابع الإضبارة، دفتر 55، أوامر الدفع، الشيكات، والقيود المحاسبية، ويكشف مراحل التعطل طبقًا لقواعد SLA.
''',
    'category': 'Demo Governorate/AI Agents',
    'author': 'Enterprise Solutions Demo',
    'depends': [
        'base',
        'mail',
        'account',
        'demo_gov_daftar55',
        'demo_gov_dossier',
        'demo_gov_cheques',
        'demo_gov_cash_books', 'demo_gov_ai_agents_menu',],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_cycle_delay_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
