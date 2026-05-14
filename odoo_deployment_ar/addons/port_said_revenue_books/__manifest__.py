# -*- coding: utf-8 -*-
{
    'name': 'دفاتر الإيرادات والمصروفات الحكومية',
    'summary': 'C-FM-10: Revenue & Expense Books — نموذج 10 حسابات + Form 81 (الموارد/الاستخدامات)',
    'description': """
        محرك دفاتر الإيرادات والمصروفات الحكومية:

        1. دفتر الإيرادات والمصروفات (نموذج 10 حسابات)
           — تخطيط cross-tab يومي × بنود الموازنة

        2. دفتر حساب الموارد (استمارة 81 ع.ح)
           — أبواب 7-9 (الإيرادات الضريبية، المنح، إيرادات أخرى)

        3. دفتر حساب الاستخدامات (استمارة 81 ع.ح)
           — أبواب 1-6 (الأجور، السلع، الفوائد، الدعم، مصروفات أخرى، الاستثمارات)

        4. دفتر الإيرادات والتسويات
           — مزيج من الإيرادات الفعلية والتسويات المرحَّلة

        كل الدفاتر تقرأ من account.move.line المرحَّل، مجمَّعة بـ budget_line_code
        على مستوى الفصل (4 أرقام: باب/فصل) أو البند الكامل (8 أرقام).

        السنة المالية تبدأ 1 يوليو وفق التقويم المالي الحكومي المصري.
    """,
    'version': '17.0.1.0.0',
    'category': 'الديوان العام/المحاسبة',
    'author': 'Paradise Integrated Solutions',
    'website': 'https://paradise.solutions.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'port_said_daftar55',
        'port_said_daftar224',
        'port_said_budget_planning',  # مصدر تعريف budget_line
        'port_said_subsidiary_books', # نمشي على نفس النمط
        'port_said_menu',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/book_definition_data.xml',
        'views/revenue_book_views.xml',
        'views/revenue_folio_views.xml',
        'views/menu.xml',
        'wizard/print_wizard_views.xml',
        'reports/report_paperformat.xml',
        'reports/report_actions.xml',
        'reports/report_form10_template.xml',
        'reports/report_form81_template.xml',
    ],
    'assets': {
        'report.assets_common': [
            'port_said_revenue_books/static/src/css/budget_register.css',
        ],
    },
    'installable': True,
    'application': False,
}
