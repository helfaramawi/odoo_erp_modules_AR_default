# -*- coding: utf-8 -*-
{
    'name': 'دفاتر التأمينات المؤقتة والنهائية',
    'summary': 'C-FM-13: Insurance/Guarantee Subsidiary Books — Form 78 (Provisional & Final)',
    'description': """
        الوحدة القانونية لدفاتر التأمينات الحكومية — استمارة 78 ع.ح.

        تُغطي دفترين قانونيين من الفهرس الرسمي (الصفوف #19 و #20):
        1. دفتر حسابات التأمينات المؤقتة مقابل خطاب ضمان / نقد / شيك (استمارة 78 ع.ح)
        2. دفتر حسابات التأمينات النهائية مقابل خطاب ضمان / نقد / شيك (استمارة 78 ع.ح)

        المعمارية: تمديد لا تكرار
        =========================
        تمدِّد port_said_advances.bank.guarantee القائم لإضافة:
        - أنواع التأمين النقدية والشيكات (ليست خطاب ضمان فقط)
        - إنشاء القيود المحاسبية تلقائياً عند التفعيل والإفراج
        - الترقيم القانوني لدفتر 78
        - ربط بالمورد/المقاول لتوليد فولية الدفتر

        نماذج جديدة:
        - port_said.insurance_deposit: إيداعات نقدية أو شيكات كتأمين (سبق أن لم تكن مدعومة)
        - port_said.insurance.folio: فولية الدفتر القانوني (مثال: مجموع تأمينات المورد الشهرية)
        - port_said.insurance.movement: حركة إيداع أو استرداد (للعرض في الفولية)

        المصدر القانوني:
        - قانون المناقصات والمزايدات 182/2018
        - اللائحة التنفيذية للمحاسبة الحكومية

        السنة المالية: 1 يوليو – 30 يونيو
    """,
    'version': '17.0.1.0.0',
    'category': 'الديوان العام/المحاسبة',
    'author': 'Paradise Integrated Solutions',
    'website': 'https://paradise.solutions.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'port_said_advances',        # النموذج الأساسي bank.guarantee
        'port_said_cash_books',      # cheque model للإيداع بشيك
        'port_said_subsidiary_books',# تصنيف الحسابات النظامية
        'port_said_menu',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/accounting_config_data.xml',
        'views/bank_guarantee_inherit_views.xml',
        'views/insurance_deposit_views.xml',
        'views/insurance_folio_views.xml',
        'views/insurance_movement_views.xml',
        'views/menu.xml',
        'wizard/generate_folio_wizard_views.xml',
        'wizard/release_wizard_views.xml',
        'reports/report_paperformat.xml',
        'reports/report_actions.xml',
        'reports/report_insurance_folio_template.xml',
        'reports/report_insurance_receipt_template.xml',
    ],
    'assets': {
        'report.assets_common': [
            'port_said_insurance_subsidiary/static/src/css/insurance_register.css',
        ],
    },
    'installable': True,
    'application': False,
}
