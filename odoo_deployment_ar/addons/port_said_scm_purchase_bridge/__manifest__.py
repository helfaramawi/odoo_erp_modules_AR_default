{
    'name': 'أمر التوريد — الجسر مع استمارة 50',
    'summary': 'C-SCM-02: Purchase Order Bridge — Auto-generate Form 50 (Daftar 55)',
    'version': '17.0.1.0.0',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': ['purchase', 'port_said_daftar55', 'port_said_commitment', 'port_said_scm_requisition'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_ext_views.xml',
    ],
    'installable': True,
}
