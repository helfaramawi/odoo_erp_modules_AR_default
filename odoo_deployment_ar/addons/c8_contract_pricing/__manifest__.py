{
    'name': 'Contract Pricing Override / تجاوز تسعير العقود',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Contract-based price override on sale order lines with date validation',
    'author': 'ERP Migration Team',
    'depends': ['sale'],
    'data': ['security/ir.model.access.csv','views/contract_pricing_views.xml','views/sale_order_views.xml'],
    'installable': True,
    'license': 'LGPL-3',
}