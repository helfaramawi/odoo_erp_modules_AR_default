# -*- coding: utf-8 -*-
{
    'name': 'وكيل جودة بيانات الموردين',
    'version': '17.0.1.0.1',
    'summary': 'Vendor Master Data Quality Agent',
    'description': '''
وكيل جودة بيانات الموردين قبل التعامل.
يقوم بحساب درجة جودة بيانات المورد بناءً على اكتمال الرقم الضريبي، الحساب البنكي، العنوان،
بيانات الاتصال، تكرار الرقم الضريبي، الجزاءات المفتوحة، وجاهزية الفاتورة الإلكترونية.
يمنع اعتماد أمر الشراء إذا كانت درجة جودة المورد أقل من الحد المحدد.
''',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'purchase',
        'account',
        'port_said_penalties',
        'l10n_eg_eta_invoice',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/vendor_data_quality_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
