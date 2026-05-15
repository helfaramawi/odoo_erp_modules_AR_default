#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""حذف البيانات التجريبية لاستمارة 50 بعد انتهاء الاختبار"""
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
odoo.tools.config.parse_config([
    '--db_host=odoo17_db', '--db_port=5432',
    '--db_user=odoo', '--db_password=odoo_secure_pass',
    '-d', 'odoo17_db',
])

from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

registry = Registry('odoo17_db')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    recs = env['port_said.daftar55'].search([('form50_ref', '=', 'TEST-FORM50-001')])
    if recs:
        for r in recs:
            print(f'  حذف: {r.sequence_number} (id={r.id})')
        recs.unlink()
        print(f'  ✔ تم حذف {len(recs)} سجل')
    else:
        print('  لم يُعثر على بيانات اختبار')

    partner = env['res.partner'].search(
        [('name', '=', '[TEST] شركة الاختبار — استمارة 50')], limit=1
    )
    if partner:
        partner.unlink()
        print('  ✔ تم حذف المورد التجريبي')

    cr.commit()
    print('  تم التنظيف.')
