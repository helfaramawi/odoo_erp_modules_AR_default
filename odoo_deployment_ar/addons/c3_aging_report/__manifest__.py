{
    'name': 'AR/AP Aging Report / تقرير أعمار المدينين والدائنين',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Detailed AR and AP aging report with configurable buckets',
    'author': 'ERP Migration Team',
    'depends': ['account'],
    'data': ['security/ir.model.access.csv','views/aging_report_views.xml','report/aging_report_template.xml'],
    'installable': True,
    'license': 'LGPL-3',
}