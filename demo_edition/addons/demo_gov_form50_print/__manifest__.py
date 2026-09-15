{
    'name': 'طباعة استمارة 50 ع.ح',
    'summary': 'طبقة الطباعة الرسمية لاستمارة 50 — معاينة ونهائية مع التحقق من المرفقات',
    'version': '17.0.1.0.0',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': [
        'demo_gov_daftar55',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/form50_views_inherit.xml',
        'reports/form50_reports.xml',
        'reports/form50_templates.xml',
        'wizards/reprint_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'post_migrate': 'odoo.addons.demo_gov_form50_print.models.form50_print.post_migrate',
}
