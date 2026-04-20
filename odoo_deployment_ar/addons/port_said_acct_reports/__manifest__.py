{
    'name': 'التقارير المحاسبية — ميزان مراجعة وكشوف حسابات',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'port_said_daftar55'],
    'data': [
        'security/ir.model.access.csv',
        'views/wizard_views.xml',
        'reports/report_actions.xml',
        'reports/report_trial_balance.xml',
        'reports/report_partner_ledger.xml',
    ],
    'assets': {
        'report.assets_common': [
            'port_said_acct_reports/static/src/css/arabic_report_font.css',
        ],
    },
    'installable': True,
    'application': False,
}
