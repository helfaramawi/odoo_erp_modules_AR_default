{
    'name': 'ملف الموظف الحكومي — بيانات ومستندات',
    'summary': 'C-HR-01: Government employee record extensions — national ID, permanent number, employment type, required documents',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الموارد البشرية',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
}
