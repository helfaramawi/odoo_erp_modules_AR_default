{
    'name': 'Project Budget Alert / تنبيه ميزانية المشروع',
    'version': '17.0.1.0.0',
    'category': 'Project',
    'summary': 'Nightly budget threshold alerts for projects',
    'author': 'ERP Migration Team',
    'depends': ['project', 'account', 'mail'],
    'data': ['security/ir.model.access.csv','data/cron.xml','views/budget_alert_views.xml'],
    'installable': True,
    'license': 'LGPL-3',
}