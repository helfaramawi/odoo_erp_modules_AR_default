{
    'category': 'الديوان العام/المخازن',
    'name': 'أذونات الصرف والارتجاع والتحويل',
    'summary': 'إدارة أذونات الصرف والارتجاع والتحويل بين المخازن — الديوان العام بورسعيد',
    'version': '17.0.1.1.0',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'account',
        'hr',
        'mail',
        'port_said_scm_warehouse',
        'l10n_eg_custody',
        'port_said_fixed_assets',
        'port_said_commitment',
        'port_said_daftar55',  # مؤقت: لازم علشان الـ daftar55_id field لسه موجود
        # port_said_daftar55 dependency removed:
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
