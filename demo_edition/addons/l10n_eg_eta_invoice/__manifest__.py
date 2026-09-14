{
    'name': 'الفاتورة الإلكترونية ETA — المحافظة التجريبية',
    'summary': 'تكامل منظومة الفاتورة الإلكترونية مع هيئة الضرائب المصرية — B2B/B2G',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'demo_gov_daftar55',
        'general_ledger_ar',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/eta_config_data.xml',
        'views/eta_config_views.xml',
        'views/eta_invoice_views.xml',
        'views/eta_menu.xml',
        'reports/report_actions.xml',
        'reports/report_eta_invoice.xml',
    ],
    'installable': True,
    'application': False,
}
