# -*- coding: utf-8 -*-
{
    'name': 'دفتر الشيكات وأوامر الدفع المرسلة',
    'summary': 'C-FM-12: Cheques Register (Form 56) + Outgoing Payment Orders (Form 56) + Cheques-for-Collection (Form 78)',
    'description': """
        الوحدة القانونية لدفاتر الشيكات الحكومية. تمدِّد نموذج demo_gov.cheque
        الأساسي من demo_gov_cash_books لتغطي ثلاثة دفاتر قانونية:

        1. دفتر حساب الشيكات (استمارة 56 ع.ح)
           — كل شيك صادر يُقيَّد في هذا الدفتر بترقيم متسلسل قانوني
           — يُطابَق مع دفتر الشيكات الورقي (كعوب مسبقة الطباعة)

        2. دفتر حساب أوامر الدفع المرسلة (استمارة 56 ع.ح)
           — أوامر الدفع الصادرة من المحافظة إلى المستفيدين
           — تكامل مع دفتر 55 (أذون الصرف)

        3. دفتر حساب الشيكات رسم التحصيل (استمارة 78 ع.ح)
           — الشيكات المُستلَمة قيد الإيداع للتحصيل
           — تتبع رسوم التحصيل البنكية

        المكونات الإضافية:
        - demo_gov.cheque.book: إدارة دفاتر الشيكات الورقية (نطاقات الأرقام)
        - demo_gov.outgoing_po: نموذج أوامر الدفع المرسلة بدورة حياة
        - متابعة الشيكات المرتدة (Bounced Cheques) مع إجراءات الاسترداد

        السنة المالية: 1 يوليو – 30 يونيو.
    """,
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الحسابات',
    'author': 'Enterprise Solutions Demo',
    'website': 'https://example.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'demo_gov_cash_books',    # يعتمد على نموذج الشيك الأساسي
        'demo_gov_daftar55',      # ربط مع أذون الصرف
        'demo_gov_daftar224',     # ربط مع اليومية العامة
        'general_ledger_ar',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/cheque_book_views.xml',
        'views/cheque_inherit_views.xml',
        'views/outgoing_po_views.xml',
        'views/bounced_followup_views.xml',
        'views/menu.xml',
        'wizard/form56_print_wizard_views.xml',
        'wizard/form78_collection_wizard_views.xml',
        'reports/report_paperformat.xml',
        'reports/report_actions.xml',
        'reports/report_form56_cheques_template.xml',
        'reports/report_form56_outgoing_po_template.xml',
        'reports/report_form78_collection_template.xml',
        'reports/report_bounced_followup_template.xml',
    ],
    'assets': {
        'report.assets_common': [
            'demo_gov_cheques/static/src/css/cheques_register.css',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
