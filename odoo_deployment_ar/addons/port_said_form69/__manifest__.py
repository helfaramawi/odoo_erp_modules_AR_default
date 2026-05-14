{
    'category': 'الديوان العام/المحاسبة',
    'name': 'استمارة 69 - الحسبة اليومية',
    'summary': 'C-FM-03: Form 69 Daily Reckoning (الحسبة اليومية)',
    'version': '17.0.1.2.0',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': [
        'port_said_daftar224',
        # port_said_scm_issue dependency removed:
        # استمارة 69 هي حسبة مالية يومية تقرأ من دفتر 55 ودفتر 224 — ليست مرتبطة بسجل الصرف المخزوني
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/form69_views.xml',
        'reports/form69_report.xml',
        'reports/form69_template.xml',
    ],
    'installable': True,
}
