# -*- coding: utf-8 -*-
{
    'name': 'المرشد الحكومي الذكي — Gov AI Guide',
    'version': '17.0.1.0.0',
    'category': 'Government/AI',
    'summary': 'مساعد ذكي مدمج في جميع النماذج لتوجيه موظفي الحكومة المصرية',
    'description': """
        المرشد الحكومي الذكي
        ====================
        نظام توجيه ذكي مدمج في Odoo يوفر إرشادات حكومية مصرية فورية
        لكل حقل في النماذج، مع مراجع قانونية دقيقة وتحذيرات من المخالفات.

        المميزات:
        - اتصال WebSocket دائم (بدون polling)
        - قاعدة معرفة مزدوجة: كود المصدر + وثائق قانونية
        - ردود بالعربية الرسمية مع مراجع تشريعية
        - شريط جانبي ثابت بتصميم حكومي احترافي
        - فهرسة تلقائية ليلية لقاعدة المعرفة
    """,
    'author': 'Gov ERP Team',
    'website': '',
    'depends': [
        'base',
        'web',
        'mail',
        'account',
        'purchase',
        'hr',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/kb_seed.xml',
        'data/cron_indexer.xml',
        'views/kb_document_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'gov_ai_guide/static/src/css/guide_sidebar.css',
            'gov_ai_guide/static/src/xml/guide_sidebar.xml',
            'gov_ai_guide/static/src/js/agent_connector.js',
            'gov_ai_guide/static/src/js/field_tracker.js',
            'gov_ai_guide/static/src/js/guide_sidebar.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['anthropic', 'numpy', 'pymupdf'],
    },
}
