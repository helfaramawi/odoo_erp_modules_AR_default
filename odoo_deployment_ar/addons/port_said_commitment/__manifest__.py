{
    'category': 'الديوان العام/المحاسبة',
    'name': 'الارتباطات والتسميح - رقابة الموازنة',
    'summary': 'C-FM-06: Budget Commitment & Clearance (ارتباط → تجنيب → تسميح)',
    'version': '17.0.1.0.0',
    'author': 'Paradise Integrated Solutions',
    'license': 'LGPL-3',
    'depends': ['mail', 'port_said_daftar55'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/commitment_views.xml',
        'reports/commitment_report.xml',
        'reports/commitment_template.xml',
        'reports/commitment_report.xml',
        'reports/commitment_template.xml',
    ],
    'installable': True,
}
