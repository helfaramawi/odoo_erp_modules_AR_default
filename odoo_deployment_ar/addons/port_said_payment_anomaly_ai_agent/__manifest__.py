# -*- coding: utf-8 -*-
{
    'name': 'وكيل كشف شذوذ المدفوعات والشيكات',
    'version': '17.0.1.0.0',
    'summary': 'Payment and cheque anomaly detection agent using Z-Score and rule-based controls',
    'description': '''
وكيل رقابي للكشف عن الشذوذ في الشيكات وأوامر الدفع والسلف.
- تحليل Z-Score حسب تاريخ المورد/المستفيد.
- كشف تكرار نفس المبلغ خلال 30 يوماً.
- كشف مدفوعات الجمعة/السبت.
- كشف مورد جديد بمبلغ كبير.
- كشف تراكم مدفوعات نهاية السنة المالية.
- كشف السلف المتأخرة دون تسوية.
''',
    'category': 'Accounting/Accounting',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'port_said_cash_books',
        'port_said_cheques',
        'port_said_advances',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/payment_anomaly_log_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
