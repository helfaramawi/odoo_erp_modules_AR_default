# -*- coding: utf-8 -*-
{
    'name': 'دفاتر النقدية وأوامر الدفع والكفالات',
    'summary': 'C-FM-11: Cash, Central Bank, Payment Orders, CAU, and Sureties Registers (Form 78 family)',
    'description': """
        محرك دفاتر Form 78 — عائلة الدفاتر النقدية والبنكية وأوامر الدفع:

        1. دفتر حساب النقدية (استمارة 78 ع.ح)
           — يقرأ من account.bank.statement.line على يوميات النقدية

        2. دفتر حساب جاري البنك المركزي المصري (استمارة 78 ع.ح)
           — يقرأ من يومية الحساب الجاري بالبنك المركزي

        3. دفتر حساب الوحدة الحسابية المركزية (استمارة 78 ع.ح)
           — حساب جاري مع CAU (الجهاز المركزي للمحاسبات / وزارة المالية)

        4. دفتر حساب أوامر الدفع الواردة (استمارة 78 ع.ح)
           — تسجيل وتتبع كل أمر دفع وارد من الوزارة أو الجهات الأخرى

        5. دفتر حساب الكفالات (استمارة 78 ع.ح)
           — تسجيل كفالات النقدية والعهد

        التصميم المعماري:
        - الدفاتر 1-3: طبقة تقرير (reporting layer) فوق
          account.bank.statement.line — نفس نمط محرك الدفاتر المساعدة.
        - الدفتر 4: نموذج مستقل (port_said.payment_order) بدورة حياة كاملة
          (received → registered → cleared → posted).
        - الدفتر 5: نموذج مستقل (port_said.surety) — كفالات نقدية/موظفين.

        الشيكات تُسجَّل في نموذج port_said.cheque الأساسي (lightweight) في هذه الوحدة،
        ليُمدَّد في C-FM-12 port_said_cheques (الدفتر 56).

        السنة المالية: 1 يوليو – 30 يونيو.
    """,
    'version': '17.0.1.0.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Paradise Integrated Solutions',
    'website': 'https://paradise.solutions.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'port_said_daftar55',
        'port_said_daftar224',
        'port_said_subsidiary_books',
        'port_said_menu',
        'general_ledger_ar',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/book_definition_data.xml',
        'views/cash_book_views.xml',
        'views/cash_folio_views.xml',
        'views/payment_order_views.xml',
        'views/surety_views.xml',
        'views/cheque_views.xml',
        'views/menu.xml',
        'wizard/print_wizard_views.xml',
        'reports/report_paperformat.xml',
        'reports/report_actions.xml',
        'reports/report_cash_register_template.xml',
        'reports/report_payment_order_template.xml',
        'reports/report_surety_template.xml',
    ],
    'assets': {
        'report.assets_common': [
            'port_said_cash_books/static/src/css/cash_register.css',
        ],
    },
    'installable': True,
    'application': False,
}
