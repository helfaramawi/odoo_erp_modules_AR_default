{
    'name': 'الرواتب الحكومية — بنود الراتب والحركات الاستثنائية',
    'summary': 'C-PR-01: Salary component structure (earnings/deductions) and exceptional-effects transactions (FR-2/FR-10)',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الرواتب',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_hr_employee', 'demo_branding'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/component_data.xml',
        'views/hr_payroll_component_views.xml',
        'views/hr_payroll_transaction_views.xml',
        'views/hr_payroll_menu.xml',
    ],
    'installable': True,
    'application': False,
}
