{
    'name': 'التقارير المحاسبية — ميزان مراجعة وكشوف حسابات',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/التقارير الحكومية',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['base', 'account', 'demo_gov_daftar55'],
    'data': [
        'security/ir.model.access.csv',
        'views/wizard_views.xml',
        'reports/report_actions.xml',
        'reports/report_trial_balance.xml',
        'reports/report_partner_ledger.xml',
    ],
    'assets': {
        'report.assets_common': [
            'demo_gov_acct_reports/static/src/css/arabic_report_font.css',
        ],
    },
    'installable': True,
    'application': False,
}
