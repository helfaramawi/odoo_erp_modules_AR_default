{
    'name': 'ربط المخزون بالحسابات — محافظة بورسعيد',
    'summary': 'قيود محاسبية تلقائية + أبعاد مالية لكل حركة مخزنية',
    'version': '17.0.1.1.0',
    'category': 'الديوان العام/المخازن',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account', 'stock',
        'port_said_scm_issue',
        # port_said_daftar55 dependency removed — دفتر 55 هو سجل مدفوعات للموردين
        # وليس له علاقة مباشرة بمحرك الربط المحاسبي للمخزون
        'c5_financial_dimensions',
        'stock_addition_permit',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/default_rules.xml',
        'views/account_rule_views.xml',
        'views/dimension_rule_views.xml',
        'views/journal_entry_views.xml',
        'views/stock_permit_extensions.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
}
