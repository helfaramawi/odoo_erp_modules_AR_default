{
    'name': 'أدوات الاختبار والقبول - UAT Demo (محافظة بورسعيد)',
    'version': '17.0.1.0.0',
    'category': 'Technical',
    'summary': 'تنظيف بيانات الحركات وتوليد بيانات اختبار حكومية عربية احترافية',
    'description': """
        وحدة إعداد بيئة اختبار القبول للجهات الحكومية العربية.
        تتيح هذه الوحدة:
        - تنظيف بيانات الحركات بأمان (مع وضع التجربة الجافة)
        - توليد بيانات اختبار عربية حكومية واقعية
        - تغطية جميع مسارات العمل والسيناريوهات
        - مرجع دفعة الاختبار: UAT-AR-GOV-2026
    """,
    'author': 'محافظة بورسعيد - فريق نظم المعلومات',
    'depends': [
        'base',
        'mail',
        'account',
        'purchase',
        'stock',
        'hr',
        'project',
        'port_said_budget_planning',
        'port_said_commitment',
        'port_said_daftar55',
        'port_said_dossier',
        'port_said_scm_requisition',
        'port_said_daftar224',
        'port_said_advances',
        'port_said_cash_books',
        'port_said_cheques',
        'procurement_committee',
        'procurement_adjudication',
        'port_said_scm_warehouse',
        'port_said_scm_issue',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/uat_sequences.xml',
        'views/uat_cleanup_views.xml',
        'views/uat_generate_views.xml',
        'views/uat_scenario_views.xml',
        'views/uat_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
