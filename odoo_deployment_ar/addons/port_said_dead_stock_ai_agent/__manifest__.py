# -*- coding: utf-8 -*-
{
    'name': 'وكيل كشف المخزون الراكد وبطيء الحركة',
    'version': '17.0.1.0.1',
    'summary': 'Slow-Moving & Dead Stock Agent',
    'description': '''
وكيل ذكي لتحليل حركة المخزون وكشف الأصناف الراكدة وبطيئة الحركة.
يقوم بفحص آخر حركة صرف، عدد أيام الركود، قيمة المخزون المجمدة، وتقديم توصيات لإعادة التوزيع أو البيع أو تقليل الشراء.
''',
    'category': 'Port Said/AI Agents',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'stock',
        'stock_account',
        'c10_inventory_revaluation',
        'stock_stocktaking_eg',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/dead_stock_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
