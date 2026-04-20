{
    'name': 'D365 War Room Finance',
    'version': '17.0.1.0.0',
    'summary': 'Finance control baseline for D365 to Odoo transition',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'depends': ['account', 'd365_war_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/war_finance_control_views.xml',
        'data/war_finance_seed.xml',
    ],
    'installable': True,
    'application': False,
}
