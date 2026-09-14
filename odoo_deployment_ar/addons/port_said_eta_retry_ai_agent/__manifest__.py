# -*- coding: utf-8 -*-
{
    'name': 'وكيل ETA لإعادة المحاولة الذكية',
    'version': '17.0.1.0.0',
    'summary': 'Smart retry and Arabic error classification for Egyptian ETA invoices',
    'description': '''
وكيل ذكي للفواتير الإلكترونية المصرية ETA:
- فحص يومي للفواتير المرفوضة أو الفاشلة.
- تصنيف سبب الفشل: بيانات، شبكة، توقيع، هيئة الضرائب، غير معروف.
- ترجمة رسالة الخطأ التقنية إلى عربي مفهوم.
- إعادة محاولة تلقائية لأخطاء الشبكة والـ timeout باستخدام backoff.
- تحويل أخطاء البيانات إلى حالة تحتاج تصحيح.
- سجل رقابي لمحاولات إعادة الإرسال.
''',
    'category': 'Accounting/Localizations',
    'author': 'Paradise AI Solutions',
    'depends': [
        'base',
        'mail',
        'l10n_eg_eta_invoice',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/cron.xml',
        'views/eta_retry_log_views.xml',
        'views/eta_invoice_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
