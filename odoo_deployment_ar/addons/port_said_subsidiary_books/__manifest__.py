# -*- coding: utf-8 -*-
{
    'name': 'الدفاتر المساعدة الحكومية — محرك موحد',
    'summary': 'C-FM-09: Subsidiary Books Engine — Forms 29/39/71 (مفردات وإجمالي الحسابات الجارية والنظامية، مدينة ودائنة)',
    'description': """
        محرك موحد لتقديم ثمانية دفاتر مساعدة حكومية مطلوبة من وزارة المالية المصرية:
        1. دفتر مفردات الحسابات الجارية المدينة (39 ع.ح)
        2. دفتر مفردات الحسابات الجارية الدائنة (39 ع.ح)
        3. دفتر إجمالي الحسابات الجارية المدينة (71 مكرر ع.ح)
        4. دفتر إجمالي الحسابات الجارية الدائنة (71 ع.ح)
        5. دفتر مفردات الحسابات النظامية المدينة (39 مكرر ع.ح)
        6. دفتر مفردات الحسابات النظامية الدائنة (39 مكرر ع.ح)
        7. دفتر إجمالي الحسابات النظامية المدينة (78 مكرر ع.ح)
        8. دفتر إجمالي الحسابات النظامية الدائنة (78 مكرر ع.ح)

        المصدر الوحيد للبيانات: account.move.line المرحّل (state=posted) فقط.
        المحرك يقدم نفس البيانات تحت ثمانية تخطيطات قانونية مختلفة، مع:
        — رقم مسلسل قانوني لكل دفتر-سنة-فولية
        — ترحيل شهري (نقل بعده / من قبله)
        — تواقيع موظف الشطب ورئيس الحسابات
        — السنة المالية تبدأ 1 يوليو حسب التقويم المالي الحكومي المصري
    """,
    'version': '17.0.1.0.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Paradise Integrated Solutions',
    'website': 'https://paradise.solutions.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'port_said_daftar55',     # مرجعية لدفتر 55
        'port_said_daftar224',    # مرجعية ليومية 224
        'port_said_menu',         # القائمة الموحدة
        'general_ledger_ar',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/account_classification_data.xml',
        'data/book_definition_data.xml',
        'views/book_definition_views.xml',
        'views/account_classification_views.xml',
        'views/folio_views.xml',
        'views/menu.xml',
        'wizard/print_wizard_views.xml',
        'wizard/migrate_paper_wizard_views.xml',
        'reports/report_paperformat.xml',
        'reports/report_actions.xml',
        'reports/report_subsidiary_detail_template.xml',
        'reports/report_subsidiary_totals_template.xml',
        'reports/report_personal_dual_template.xml',
    ],
    'assets': {
        'report.assets_common': [
            'port_said_subsidiary_books/static/src/css/arabic_register.css',
        ],
    },
    'installable': True,
    'application': False,
}
