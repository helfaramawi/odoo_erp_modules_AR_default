{
    'name': 'PO Approval Matrix',
    'version': '17.0.1.0.0',
    'category': 'Purchase',
    'depends': ['purchase', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/approval_matrix_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}