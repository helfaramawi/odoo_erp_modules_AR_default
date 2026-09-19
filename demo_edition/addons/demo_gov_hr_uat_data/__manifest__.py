{
    'name': 'أدوات الاختبار — الموارد البشرية والرواتب (المحافظة التجريبية)',
    'version': '17.0.1.0.0',
    'category': 'Technical',
    'summary': 'يضيف بيانات اختبار الموارد البشرية والرواتب إلى معالج توليد بيانات UAT الحكومي',
    'description': """
        إضافة غير هدّامة (_inherit) على وحدة demo_gov_uat_tools — تضيف
        خيارات توليد بيانات اختبار واقعية لحزمة الموارد البشرية والرواتب
        الحكومية الكاملة (إجازات، تدريب، توظيف، تقييم أداء، نقل وترقيات،
        رواتب ودورة مرحّلة، صندوق تكافل، معاشات، إفصاح مالي، موازنة
        وظائف) من غير ما تعدّل أي ملف في الموديول الأصلي.
    """,
    'author': 'Enterprise Solutions Demo',
    'website': 'https://example.com',
    'depends': [
        'demo_gov_uat_tools',
        'demo_gov_hr_employee',
        'demo_gov_hr_leave',
        'demo_gov_hr_training',
        'demo_gov_hr_recruitment',
        'demo_gov_hr_performance',
        'demo_gov_hr_transfer',
        'demo_gov_hr_payroll_structure',
        'demo_gov_hr_payroll_tax_eg',
        'demo_gov_hr_payroll_insurance_eg',
        'demo_gov_hr_payroll_run',
        'demo_gov_hr_takaful',
        'demo_gov_hr_pension',
        'demo_gov_hr_disclosure',
        'demo_gov_hr_org_development',
    ],
    'data': [
        'views/uat_generate_wizard_hr_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
