{
    'name': 'أمر التوريد — الجسر مع استمارة 50',
    'category': 'الخدمات الحكومية التجريبية/المشتريات',
    'summary': 'C-SCM-02: Purchase Order Bridge — Auto-generate Form 50 (Daftar 55)',
    'version': '17.0.1.0.0',
    'author': 'Enterprise Solutions Demo',
    'license': 'LGPL-3',
    'depends': ['purchase', 'demo_gov_daftar55', 'demo_gov_commitment', 'demo_gov_scm_requisition'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_ext_views.xml',
    ],
    'installable': True,
}
