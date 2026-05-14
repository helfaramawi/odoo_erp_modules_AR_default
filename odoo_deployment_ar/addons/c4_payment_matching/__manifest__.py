{
    'name': 'Vendor Payment Matching Override / تجاوز مطابقة مدفوعات الموردين',
    'version': '17.0.1.0.0',
    'category': 'الديوان العام/المحاسبة',
    'summary': 'Manual vendor payment matching with early-pay discount journal line',
    'author': 'ERP Migration Team',
    'depends': ['account', 'account_payment'],
    'data': ['security/ir.model.access.csv','views/payment_matching_views.xml'],
    'installable': True,
    'license': 'LGPL-3',
}