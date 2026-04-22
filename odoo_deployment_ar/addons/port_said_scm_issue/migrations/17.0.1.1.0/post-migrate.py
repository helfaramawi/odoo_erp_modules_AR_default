# -*- coding: utf-8 -*-
"""
Post-migration: إنشاء سطور سجل الصرف للأذونات المرحَّلة المسبقة
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # التحقق من وجود جدول stock_issue_register_line (يُنشأ من النموذج الجديد)
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'stock_issue_register_line'
        )
    """)
    if not cr.fetchone()[0]:
        _logger.warning("Post-migration: stock_issue_register_line table not found yet — skipping")
        return

    # إيجاد الأذونات المرحَّلة التي ليس لها قيد في سجل الصرف بعد
    cr.execute("""
        SELECT sip.id, sip.issue_date, sip.requesting_dept,
               sip.reference_no, sip.purpose, sip.total_value,
               sip.warehouse_id, sip.storekeeper_id, sip.issue_type
        FROM stock_issue_permit sip
        LEFT JOIN stock_issue_register_line sirl ON sirl.issue_permit_id = sip.id
        WHERE sip.state = 'posted'
          AND sirl.id IS NULL
    """)
    permits = cr.fetchall()

    if not permits:
        _logger.info("Post-migration: no unregistered posted permits found — nothing to do")
        return

    _logger.info(f"Post-migration: creating register lines for {len(permits)} existing posted permits")

    # الحصول على تسلسل ISR
    cr.execute("""
        SELECT id FROM ir_sequence WHERE code = 'stock.issue.register' LIMIT 1
    """)
    seq_row = cr.fetchone()

    type_labels = {
        'consumption': 'استهلاك',
        'custody': 'عهدة',
        'project': 'مشروع',
        'maintenance': 'صيانة',
        'other': 'أخرى',
    }

    for permit in permits:
        permit_id, issue_date, dept, form50, purpose, total, wh_id, sk_id, itype = permit
        year = str(issue_date.year) if issue_date else ''
        type_label = type_labels.get(itype, itype or '')

        # توليد رقم مسلسل بسيط
        if seq_row:
            cr.execute("""
                SELECT nextval((
                    SELECT CONCAT('ir_sequence_', LPAD(id::text, 3, '0'))
                    FROM ir_sequence WHERE code = 'stock.issue.register' LIMIT 1
                ))
            """)
            seq_val = cr.fetchone()
            seq_num = f"ISR/{year}/{str(seq_val[0]).zfill(4)}" if seq_val else f"ISR/{year}/MIGR"
        else:
            seq_num = f"ISR/{year}/MIGR-{permit_id}"

        cr.execute("""
            INSERT INTO stock_issue_register_line
                (sequence_number, fiscal_year, issue_permit_id, issue_date,
                 issue_type, warehouse_id, requesting_dept, form50_ref,
                 purpose, storekeeper_id, total_value,
                 currency_id, company_id, create_date, write_date, create_uid, write_uid)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                 (SELECT id FROM res_currency WHERE name='EGP' LIMIT 1),
                 (SELECT id FROM res_company LIMIT 1),
                 NOW(), NOW(), 1, 1)
            ON CONFLICT (issue_permit_id) DO NOTHING
            RETURNING id
        """, (seq_num, year, permit_id, issue_date, type_label,
               wh_id, dept, form50, purpose, sk_id, total or 0))

        row = cr.fetchone()
        if row:
            # ربط السجل بالإذن
            cr.execute("""
                UPDATE stock_issue_permit
                SET issue_register_line_id = %s
                WHERE id = %s
            """, (row[0], permit_id))
            _logger.info(f"Post-migration: created register line {seq_num} for permit id={permit_id}")

    _logger.info("Post-migration 17.0.1.1.0 complete")
