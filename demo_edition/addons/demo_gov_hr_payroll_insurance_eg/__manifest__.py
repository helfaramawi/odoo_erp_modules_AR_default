{
    'name': 'الرواتب الحكومية — التأمينات الاجتماعية',
    'summary': 'C-PR-03: Insurable wage min/max ceiling and employee/employer contribution split per year (FR-2/1-2)',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الرواتب',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_hr_payroll_structure', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payroll_insurance_views.xml',
        'views/hr_payroll_insurance_menu.xml',
        'data/insurance_seed_data.xml',
    ],
    'installable': True,
    'application': False,
}
