# -*- coding: utf-8 -*-
import logging
from odoo.modules.module import get_module_path

_logger = logging.getLogger(__name__)

from . import models
from . import controllers


def post_init_hook(env):
    """
    يُنفَّذ مرة واحدة عند تثبيت الـ addon
    يقوم بفهرسة جميع الـ addons المثبتة وتحميل بيانات القوانين الأساسية
    """
    # 1. فهرسة جميع الـ addons المثبتة
    try:
        indexer = env['gov.kb.indexer']
        installed_modules = env['ir.module.module'].search([
            ('state', '=', 'installed')
        ])
        for module in installed_modules:
            addon_path = get_module_path(module.name, raise_not_found=False)
            if addon_path:
                try:
                    indexer.index_addon_source(addon_path, module.name)
                except Exception as e:
                    _logger.warning(
                        'gov_ai_guide: فشل فهرسة الـ addon %s: %s',
                        module.name, str(e)
                    )

        # 2. تحميل بيانات القوانين الأساسية
        indexer.load_seed_legal_kb()
        _logger.info('gov_ai_guide: تمت فهرسة قاعدة المعرفة بنجاح')
    except Exception as e:
        _logger.error('gov_ai_guide: خطأ في الفهرسة الأولية: %s', str(e))

    # 3. التحقق من الـ API key
    api_key = env['ir.config_parameter'].sudo().get_param('gov_ai_guide.api_key')
    if not api_key:
        _logger.warning(
            'gov_ai_guide: لم يتم تعيين Anthropic API Key. '
            'افتح: الإعدادات > المعلمات التقنية > gov_ai_guide.api_key'
        )
