{
    'name': 'Credit Bureau API / واجهة برمجة مكتب الائتمان',
    'version': '17.0.1.0.0',
    'category': 'الديوان العام/المشتريات',
    'summary': 'Credit check on sale orders via Credit Bureau API — Green/Amber/Red logic',
    'author': 'ERP Migration Team',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/credit_bureau_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}