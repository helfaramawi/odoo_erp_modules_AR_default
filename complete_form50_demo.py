#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تكملة بيانات الـ demo: اضبارة + 10 مرفقات وهمية + تغيير الحالة
يُشغَّل مرة واحدة فقط بعد create_form50_demo.py
"""
import sys, base64
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
odoo.tools.config.parse_config([
    '--db_host=odoo17_db', '--db_port=5432',
    '--db_user=odoo', '--db_password=odoo_secure_pass',
    '-d', 'odoo17_db',
])

from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

# PDF صغير صالح (1 صفحة فارغة) — يعمل مع wkhtmltopdf
TINY_PDF_B64 = (
    "JVBERi0xLjAKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2Jq"
    "CjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2Jq"
    "CjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCAzIDNd"
    "ID4+CmVuZG9iagp4cmVmCjAgNAowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMDkgMDAwMDAgbi"
    "AKMDAwMDAwMDA1OCAwMDAwMCBuIAowMDAwMDAwMTE1IDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUg"
    "NCAvUm9vdCAxIDAgUiA+PgpzdGFydHhyZWYKMTkwCiUlRU9GCg=="
)

ATTACHMENT_TYPES = [
    ('national_id',       'صورة بطاقة الرقم القومي'),
    ('bank_letter',       'خطاب معتمد من البنك'),
    ('commitment_form',   'طلب الارتباط'),
    ('purchase_memo',     'مذكرة شراء'),
    ('supply_order',      'أمر التوريد'),
    ('invoices',          'الفواتير'),
    ('store_declaration', 'إقرار أمين المخازن'),
    ('committee_report',  'محضر لجنة الفحص'),
    ('addition_permit',   'إذن إضافة'),
    ('tender_docs',       'كراسة الشروط'),
]

registry = Registry('odoo17_db')

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # ── ابحث عن السجل التجريبي ───────────────────────────────────────────────
    rec = env['port_said.daftar55'].search(
        [('form50_ref', '=', 'TEST-FORM50-001')], limit=1
    )
    if not rec:
        print('❌ لم يُعثر على السجل التجريبي. شغّل create_form50_demo.py أولاً.')
        sys.exit(1)

    print(f'  ← السجل: {rec.sequence_number} (id={rec.id})')

    # ── 1. تغيير الحالة إلى "مُسمَّح" وضبط رقم دفتر 224 ────────────────────
    rec.write({
        'state':              'cleared',
        'daftar224_sequence': 'د224/2026/0001',
        'reviewer_stamp_date': '2026-05-15',
    })
    print('  ✔ الحالة: مُسمَّح | رقم دفتر 224: د224/2026/0001')

    # ── 2. إنشاء اضبارة ──────────────────────────────────────────────────────
    dossier = env['port_said.dossier'].search(
        [('daftar55_id', '=', rec.id)], limit=1
    )
    if not dossier:
        dossier = env['port_said.dossier'].create({
            'daftar55_id': rec.id,
            'budget_line': '001/12/03/05',
            'fiscal_year': 2026,
        })
        print(f'  ✔ اضبارة: {dossier.dossier_number}')
    else:
        print(f'  ← اضبارة موجودة: {dossier.dossier_number}')

    # ── 3. إنشاء 10 مرفقات وهمية (PDF فارغ) ─────────────────────────────────
    existing_types = set(dossier.attachment_ids.mapped('attachment_type'))
    created = 0
    for att_type, att_label in ATTACHMENT_TYPES:
        if att_type in existing_types:
            continue
        # ir.attachment
        ir_att = env['ir.attachment'].create({
            'name':      f'[TEST] {att_label}.pdf',
            'type':      'binary',
            'datas':     TINY_PDF_B64,
            'mimetype':  'application/pdf',
            'res_model': 'port_said.dossier',
            'res_id':    dossier.id,
        })
        # dossier attachment line
        env['port_said.dossier.attachment'].create({
            'dossier_id':      dossier.id,
            'attachment_type': att_type,
            'attachment_id':   ir_att.id,
        })
        created += 1

    print(f'  ✔ تم إنشاء {created} مرفق وهمي (PDF)')

    cr.commit()

    # ── تحقق من الجاهزية ─────────────────────────────────────────────────────
    rec.invalidate_recordset()
    print()
    print('═' * 55)
    print(f'  الحالة          : {rec.state}')
    print(f'  رقم دفتر 224    : {rec.daftar224_sequence}')
    print(f'  المرفقات مكتملة : {rec.attachments_complete}')
    print(f'  جاهز للطباعة    : {rec.can_final_print}')
    if not rec.can_final_print:
        print(f'  ملاحظات         :\n{rec.print_readiness_notes}')
    print('═' * 55)
    print()
    print('  الآن اضغط "طباعة نهائية استمارة 50" في السجل.')
