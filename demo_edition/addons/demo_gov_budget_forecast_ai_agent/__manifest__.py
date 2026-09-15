# -*- coding: utf-8 -*-
{
    'name': 'وكيل توقع انحرافات الموازنة السنوية',
    'version': '17.0.1.0.0',
    'summary': 'Budget annual deviation forecasting using Daftar55 actuals and linear extrapolation',
    'description': '''
وكيل توقع انحرافات الموازنة السنوية:
- يجمع الصرف الفعلي الشهري من دفتر 55 المرحل/المحفوظ.
- يقارن الصرف الفعلي بالمستهدف الشهري.
- يتوقع موقف نهاية السنة المالية بطريقة Linear Extrapolation.
- يحدد البنود المرشحة للعجز أو الفائض.
- يكتب تقريراً عربياً رسمياً.
- يصدر PDF جاهز للطباعة والتوقيع.
''',
    'category': 'Accounting/Budget',
    'author': 'Enterprise Solutions Demo',
    'depends': [
        'base',
        'mail',
        'demo_gov_budget_planning',
        'demo_gov_commitment',
        'demo_gov_daftar55', 'demo_gov_ai_agents_menu',],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/cron.xml',
        'views/budget_forecast_views.xml',
        'views/budget_forecast_menu.xml',
        'report/budget_forecast_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
