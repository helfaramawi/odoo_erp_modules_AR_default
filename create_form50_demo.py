#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إنشاء بيانات تجريبية لطباعة استمارة 50 ع.ح
بدون أي قيود محاسبية — للحذف بعد الاختبار
"""
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

    # ── 1. مورد تجريبي ──────────────────────────────────────────────────────
    partner = env['res.partner'].search(
        [('name', '=', '[TEST] شركة الاختبار — استمارة 50')], limit=1
    )
    if not partner:
        partner = env['res.partner'].create({
            'name':       '[TEST] شركة الاختبار — استمارة 50',
            'street':     'شارع 23 يوليو، حي الزهور',
            'city':       'بورسعيد',
            'is_company': True,
        })
        print(f'  ✔ تم إنشاء مورد: {partner.name}')
    else:
        print(f'  ← مورد موجود: {partner.name}')

    # ── 2. سجل دفتر 55 ──────────────────────────────────────────────────────
    rec = env['port_said.daftar55'].create({
        'form50_ref':      'TEST-FORM50-001',
        'department_name': 'إدارة الشؤون المالية — [بيانات اختبار]',
        'division_name':   'قسم المحاسبة العامة',
        'date_received':   '2026-05-15',
        'vendor_id':       partner.id,
        'budget_line':     '001/12/03/05',
        'amount_gross':    5250.00,
        'bank_name':       'بنك مصر — فرع بورسعيد',
        'bank_account_no': '123456789012',
        'commitment_ref':  'ارتباط/2026/TEST-001',
        'transaction_type': 'inventory_purchase',
        # حقول التوقيعات — اختياري، للظهور في الطباعة
        'writer_assigned':  'محمد أحمد',
        'register_z_ref':   'ز/2026/55',
        'payment_order_ref': 'د.م/2026/001',
    })

    print(f'  ✔ تم إنشاء سجل دفتر 55: seq={rec.sequence_number}, id={rec.id}')

    # ── 3. سطور الفواتير (لجدول فواتير استمارة 50) ──────────────────────────
    env['port_said.form50.invoice.line'].create([
        {
            'daftar55_id':    rec.id,
            'sequence':       10,
            'invoice_ref':    'INV-TEST-001',
            'invoice_date':   '2026-04-10',
            'description':    'توريد مستلزمات مكتبية',
            'amount_pounds':  3000,
            'amount_piasters': 0,
        },
        {
            'daftar55_id':    rec.id,
            'sequence':       20,
            'invoice_ref':    'INV-TEST-002',
            'invoice_date':   '2026-04-25',
            'description':    'توريد أجهزة طباعة',
            'amount_pounds':  2250,
            'amount_piasters': 0,
        },
    ])
    print(f'  ✔ تم إضافة 2 سطر فواتير')

    cr.commit()

    print()
    print('═' * 55)
    print(f'  رقم المسلسل : {rec.sequence_number}')
    print(f'  ID الداخلي  : {rec.id}')
    print(f'  السنة المالية: {rec.fiscal_year}')
    print(f'  الإجمالي    : {rec.amount_gross} جنيه')
    print(f'  الصافي      : {rec.amount_net} جنيه')
    print(f'  التفقيط     : {rec.amount_words}')
    print('═' * 55)
    print()
    print('  لحذف هذا السجل بعد الاختبار:')
    print(f'  ابحث عن form50_ref = "TEST-FORM50-001" في دفتر 55')
    print('  أو شغّل: delete_form50_demo.py')
