{
    'name': 'التقارير المحاسبية الحكومية — ميزان مراجعة وكشوف حسابات',
    'summary': 'ميزان المراجعة الحكومي + كشف حساب مورد/عميل + تقرير الأستاذ العام',
    'version': '17.0.2.0.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'demo_gov_daftar55',
        'demo_gov_commitment',
        'general_ledger_ar',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/gl_report_wizard_views.xml',
        'views/menu.xml',
        'reports/report_actions.xml',
        'reports/report_trial_balance.xml',
        'reports/report_partner_ledger.xml',
        'reports/report_general_ledger.xml',
        'reports/report_chart_of_accounts.xml',
    ],
    'assets': {
        'web.assets_common': [],
        'report.assets_common': [
            'demo_gov_gl_reports/static/src/css/arabic_report_font.css',
        ],
    },
    'installable': True,
    'application': False,
}
