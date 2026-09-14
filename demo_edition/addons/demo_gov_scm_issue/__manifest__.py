{
    'name': 'أذونات الصرف والارتجاع والتحويل',
    'category': 'الخدمات الحكومية التجريبية/المخازن والمستودعات',
    'summary': 'إدارة أذونات الصرف والارتجاع والتحويل بين المخازن — الديوان العام المحافظة التجريبية',
    'version': '17.0.1.1.0',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'account',
        'hr',
        'mail',
        'demo_gov_scm_warehouse',
        'l10n_eg_custody',
        'demo_gov_fixed_assets',
        'demo_gov_commitment',
        'demo_gov_daftar55',  # مؤقت: لازم علشان الـ daftar55_id field لسه موجود
        # demo_gov_daftar55 dependency removed:
        # دفتر 55 ع.ح هو سجل مدفوعات للموردين وليس له علاقة بأذونات الصرف المخزونية.
        # سجل حركات الصرف المخزوني (stock.issue.register.line) مُعرَّف في هذه الوحدة.
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/issue_permit_views.xml',
        'views/return_permit_views.xml',
        'views/transfer_permit_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
}
