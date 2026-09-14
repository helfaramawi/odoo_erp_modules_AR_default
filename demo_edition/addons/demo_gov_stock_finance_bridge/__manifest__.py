{
    'name': 'ربط المخزون بالحسابات — المحافظة التجريبية',
    'summary': 'قيود محاسبية تلقائية + أبعاد مالية لكل حركة مخزنية',
    'version': '17.0.1.1.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account', 'stock',
        'demo_gov_scm_issue',
        # demo_gov_daftar55 dependency removed — دفتر 55 هو سجل مدفوعات للموردين
        # وليس له علاقة مباشرة بمحرك الربط المحاسبي للمخزون
        'c5_financial_dimensions',
        'stock_addition_permit',
        'general_ledger_ar',
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
