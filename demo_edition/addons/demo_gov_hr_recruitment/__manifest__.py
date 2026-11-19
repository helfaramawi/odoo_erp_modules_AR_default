{
    'name': 'التوظيف والتأهيل الحكومي',
    'summary': 'C-HR-04: Recruitment projects linked to job openings, onboarding checklist extension, government termination types',
    'version': '17.0.1.0.0',
    'category': 'الخدمات الحكومية التجريبية/الموارد البشرية',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['hr_recruitment', 'demo_gov_hr_employee', 'demo_branding'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_recruitment_project_views.xml',
        'views/hr_applicant_views_inherit.xml',
        'views/hr_employee_termination_views_inherit.xml',
        'views/hr_recruitment_menu.xml',
    ],
    'installable': True,
    'application': False,
}
