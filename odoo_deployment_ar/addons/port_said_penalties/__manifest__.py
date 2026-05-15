# -*- coding: utf-8 -*-
{
    'name': 'دفتر حساب الجزاءات',
    'summary': 'C-FM-14: Penalties Book — Form 39',
    'description': """
        دفتر حساب الجزاءات — استمارة 39 ع.ح

        يُغطي الدفتر القانوني المطلوب من وزارة المالية لتسجيل الجزاءات الحكومية.
        الدفتر يتتبع نوعين من الجزاءات:

        1. جزاءات تأديبية على الموظفين (HR disciplinary penalties)
           — إنذار، خصم من الأجر، حرمان من العلاوة، خصم من الإجازات
           — وفقاً لقانون الخدمة المدنية 81 لسنة 2016

        2. جزاءات تعاقدية على الموردين/المقاولين (Vendor contract penalties)
           — غرامة تأخير، خصم نسبة جودة، خصم من الضمان
           — وفقاً لقانون المناقصات 182 لسنة 2018

        المعمارية: نموذج واحد port_said.penalty مع حقل subject_type يُميِّز
        بين الموظف والمورد. Form 39 legal printout يعمل لكلا النوعين.

        دورة الحياة:
        draft → recorded → approved → executed → (appealed → resolved)
                                              → (cancelled if void)

        السنة المالية: 1 يوليو – 30 يونيو
    """,
    'version': '17.0.1.0.0',
    'category': 'الديوان العام/المحاسبة',
    'author': 'Paradise Integrated Solutions',
    'website': 'https://paradise.solutions.com',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'hr',                            # for employee subject
        'port_said_daftar55',           # integration with payment orders
        'port_said_subsidiary_books',   # memo classifications
        'port_said_menu',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/violation_type_data.xml',
        'views/penalty_views.xml',
        'views/violation_type_views.xml',
        'views/appeal_views.xml',
        'views/menu.xml',
        'wizard/bulk_penalty_wizard_views.xml',
        'wizard/print_register_wizard_views.xml',
        'reports/report_paperformat.xml',
        'reports/report_actions.xml',
        'reports/report_penalty_decision_template.xml',
        'reports/report_penalty_register_template.xml',
    ],
    'assets': {
        'report.assets_common': [
            'port_said_penalties/static/src/css/penalty_register.css',
        ],
    },
    'installable': True,
    'application': False,
}
