# -*- coding: utf-8 -*-
{
    'name': 'دفاتر حركة النقود المرسلة والواردة',
    'summary': 'C-FM-15: Outgoing and Incoming Cash Transfers — Form 39',
    'description': """
        الوحدة القانونية لدفتري حركة النقود في بورسعيد:

        1. دفتر حساب حركة النقود المرسلة (استمارة 39 ع.ح)
           — تحويلات النقد من خزينة المحافظة إلى وحدات تابعة أو خارجية
        2. دفتر حساب حركة النقود الواردة (استمارة 39 ع.ح)
           — استلام النقد من الجهات الممولة أو الوحدات التابعة

        الفارق الجوهري عن دفاتر النقدية (port_said_cash_books):
        - تلك تتبع حركات الحساب البنكي (account.bank.statement.line)
        - هذه تتبع نقل النقدية الفعلي بين عهدة وأخرى (Chain of Custody)

        السمات الرئيسية:
        - تتبع سلسلة العهدة (مرسل، ناقل، مستلم) مع التوقيت
        - التكامل مع دفتر 55 لأوامر الصرف التي تنتج تحويلات نقدية
        - حالة "فقدان" استثنائية تتطلب محضر شرطة
        - فولية شهرية برصيد مرحَّل (نفس نمط الدفاتر الأخرى)

        السنة المالية: 1 يوليو – 30 يونيو
    """,
    'version': '17.0.1.0.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Paradise Integrated Solutions',
    'website': 'https://paradise.solutions.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'hr',                          # for custody holders (employees)
        'port_said_cash_books',        # sibling - shares cash.book infrastructure
        'port_said_daftar55',          # integration with payment orders
        'port_said_menu',
        'general_ledger_ar',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/cash_transfer_views.xml',
        'views/transfer_folio_views.xml',
        'views/menu.xml',
        'wizard/print_register_wizard_views.xml',
        'reports/report_paperformat.xml',
        'reports/report_actions.xml',
        'reports/report_transfer_slip_template.xml',
        'reports/report_transfer_register_template.xml',
    ],
    'assets': {
        'report.assets_common': [
            'port_said_cash_transfers/static/src/css/transfer_register.css',
        ],
    },
    'installable': True,
    'application': False,
}
