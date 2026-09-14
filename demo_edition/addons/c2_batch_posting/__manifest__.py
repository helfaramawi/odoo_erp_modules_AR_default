{
    'name': 'Batch Journal Posting / ترحيل دفعي للقيود',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Scheduled nightly batch posting of draft journal entries',
    'author': 'ERP Migration Team',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/batch_posting_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
