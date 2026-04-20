{
    'name': 'الفاتورة الإلكترونية ETA — محافظة بورسعيد',
    'summary': 'تكامل منظومة الفاتورة الإلكترونية مع هيئة الضرائب المصرية — B2B/B2G',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'port_said_daftar55',
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
