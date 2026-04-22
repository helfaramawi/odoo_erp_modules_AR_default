{
    'name': 'التقارير المحاسبية الحكومية — ميزان مراجعة وكشوف حسابات',
    'summary': 'ميزان المراجعة الحكومي + كشف حساب مورد/عميل + تقرير الأستاذ العام',
    'version': '17.0.2.0.0',
    'category': 'Accounting/Egypt Government',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': [
        'base', 'mail', 'account',
        'port_said_daftar55',
        'port_said_commitment',
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
            'port_said_gl_reports/static/src/css/arabic_report_font.css',
        ],
    },
    'installable': True,
    'application': False,
}
