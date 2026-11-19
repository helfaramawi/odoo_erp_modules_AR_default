{
    'name': 'أدوات الاختبار والقبول - UAT Demo (الجهة الحكومية التجريبية)',
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

        ملاحظة أمان: أداة التنظيف الفعلي مقيّدة بقواعد بيانات نسخة العرض
        التجريبي فقط (اسم قاعدة البيانات يبدأ بالبادئة ``demo_`` ومتغير
        البيئة APP_ENV يساوي demo) — نفس القيد المطبق في
        scripts/demo-seed/demo-reset.sh.
    """,
    'author': 'Enterprise Solutions Demo',
    'website': 'https://example.com',
    'depends': [
        'base',
        'mail',
        'account',
        'purchase',
        'stock',
        'hr',
        'project',
        # Only depend on modules confirmed installed in this DB
        'demo_gov_commitment',
        'demo_gov_daftar55',
        'demo_gov_dossier',
        'demo_gov_scm_requisition',
        'demo_gov_daftar224',
        'demo_gov_advances',
        'procurement_committee',
        'procurement_adjudication',
        'demo_gov_scm_warehouse',
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
