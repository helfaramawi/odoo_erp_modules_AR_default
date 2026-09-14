# -*- coding: utf-8 -*-
{
    'name': 'وكيل كشف جزاءات الموردين تلقائياً',
    'version': '17.0.1.0.0',
    'summary': 'إنشاء جزاءات تلقائية للموردين عند رفض أو مطابقة جزئية في محاضر لجنة الفحص',
    'description': 'وكيل يراقب نموذج 12 مخازن ومحاضر لجنة الفحص وينشئ جزاءً تلقائياً للمورد عند وجود رفض أو مطابقة جزئية.',
    'author': 'Paradise AI Solutions',
    'category': 'Purchases/Government',
    'depends': [
        'base',
        'mail',
        'purchase',
        'port_said_penalties',
        'port_said_scm_warehouse',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/penalty_agent_log_views.xml',
        'views/inspection_committee_views.xml',
        'views/inspection_menu_patch.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
