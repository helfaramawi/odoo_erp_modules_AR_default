{
    'name': 'الرواتب الحكومية — الشرائح الضريبية المصرية',
    'summary': 'C-PR-02: Progressive income tax categories/brackets, proportional stamp duty, flat tax, non-commercial-professions tax (FR-2/2..5)',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الرواتب',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['demo_gov_hr_payroll_structure'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payroll_tax_views.xml',
        'views/hr_payroll_tax_menu.xml',
        'data/tax_seed_data.xml',
    ],
    'installable': True,
    'application': False,
}
