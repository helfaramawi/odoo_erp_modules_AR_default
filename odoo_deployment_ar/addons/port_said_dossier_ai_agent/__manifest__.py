# -*- coding: utf-8 -*-
{
    'name': 'وكيل فحص اكتمال الإضبارة قبل الصرف',
    'version': '17.0.1.0.0',
    'summary': 'منع اعتماد دفتر 55 قبل اكتمال مستندات الإضبارة والتحقق الذكي من المرفقات',
    'description': '''
وكيل فحص اكتمال الإضبارة قبل الصرف
==================================
يقوم الموديول بمنع اعتماد/صرف دفتر 55 إذا كانت الإضبارة المرتبطة غير مكتملة،
مع تسجيل سجل تدقيق كامل لكل محاولة فحص.

المزايا:
- التكامل مع action_approve في port_said.daftar55.
- منع الصرف عند نقص مرفقات الإضبارة.
- إظهار أسماء المرفقات الناقصة للمستخدم.
- سجل Audit Log لكل فحص.
- Hook جاهز للتحقق الذكي من محتوى الفاتورة والمرفقات.
- إعدادات لتفعيل أو تعطيل التحقق الذكي/الصارم.
''',
    'author': 'Paradise AI Solutions',
    'category': 'Accounting/Government',
    'depends': [
        'base',
        'mail',
        'port_said_dossier',
        'port_said_daftar55',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/dossier_audit_log_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
