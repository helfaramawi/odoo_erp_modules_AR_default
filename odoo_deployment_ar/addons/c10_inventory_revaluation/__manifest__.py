{
    'name': 'Inventory Revaluation Report / تقرير إعادة تقييم المخزون',
    'version': '17.0.1.0.0',
    'category': 'الديوان العام/المخازن',
    'summary': 'QWeb inventory revaluation report with prior month variance column',
    'author': 'ERP Migration Team',
    'depends': ['stock_account'],
    'data': ['security/ir.model.access.csv','views/revaluation_views.xml','report/revaluation_report.xml'],
    'installable': True,
    'license': 'LGPL-3',
}