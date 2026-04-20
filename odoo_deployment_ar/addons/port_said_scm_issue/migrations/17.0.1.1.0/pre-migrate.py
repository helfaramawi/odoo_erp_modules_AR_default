# -*- coding: utf-8 -*-
"""
Migration: 17.0.1.0.0 -> 17.0.1.1.0
يُزيل حقل daftar55_id الخاطئ من جدول stock_issue_permit
ويُنظِّف الـ views القديمة من قاعدة البيانات
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # 1. حذف العمود القديم من جدول قاعدة البيانات
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'stock_issue_permit'
          AND column_name = 'daftar55_id'
    """)
    if cr.fetchone():
        _logger.info("Migration: dropping stale column daftar55_id from stock_issue_permit")
        cr.execute("ALTER TABLE stock_issue_permit DROP COLUMN IF EXISTS daftar55_id")

    # 2. حذف الـ views القديمة من ir.ui.view حتى يُعيد Odoo بناءها من الملفات
    stale_view_names = [
        'stock.issue.permit.form',
        'stock.issue.permit.list',
        'stock.issue.permit.form.sfb',
    ]
    for view_name in stale_view_names:
        cr.execute("""
            DELETE FROM ir_ui_view
            WHERE name = %s AND model = 'stock.issue.permit'
        """, (view_name,))
        deleted = cr.rowcount
        if deleted:
            _logger.info(f"Migration: deleted stale ir.ui.view '{view_name}' ({deleted} records)")

    # 3. حذف ir.model.fields القديم إن كان مُسجَّلاً
    cr.execute("""
        DELETE FROM ir_model_fields
        WHERE model = 'stock.issue.permit'
          AND name = 'daftar55_id'
    """)
    if cr.rowcount:
        _logger.info("Migration: deleted stale ir.model.fields entry for daftar55_id")

    _logger.info("Migration 17.0.1.1.0 pre-migrate complete")
