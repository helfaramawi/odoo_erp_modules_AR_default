import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo.tools import config
config.parse_config(['--config=/etc/odoo/odoo.conf', '--database=odoo17', '--no-http'])

import odoo.sql_db
db = odoo.sql_db.db_connect('odoo17')

with db.cursor() as cr:

    # Check if our top menu already exists
    cr.execute("SELECT id FROM ir_ui_menu WHERE name LIKE 'ERP Migration%' AND parent_id IS NULL")
    existing = cr.fetchone()

    if existing:
        top_menu_id = existing[0]
        print(f"Top menu already exists: {top_menu_id}")
    else:
        # Create top-level menu without web_icon
        cr.execute("""
            INSERT INTO ir_ui_menu (name, parent_id, sequence, active)
            VALUES ('ERP Migration / ترحيل ERP', NULL, 99, true)
            RETURNING id
        """)
        top_menu_id = cr.fetchone()[0]
        print(f"Created top menu id: {top_menu_id}")

    modules_actions = [
        ('purchase.approval.threshold', 'Approval Matrix / مصفوفة الاعتماد', 10),
        ('batch.posting.config', 'Batch Posting / الترحيل الدفعي', 20),
        ('aging.report.wizard', 'Aging Report / تقرير الأعمار', 30),
        ('financial.dimension', 'Financial Dimensions / الأبعاد المالية', 50),
        ('credit.bureau.config', 'Credit Bureau / مكتب الائتمان', 70),
        ('contract.price', 'Contract Prices / أسعار العقود', 80),
        ('inventory.revaluation.wizard', 'Inventory Revaluation / إعادة تقييم المخزون', 90),
        ('ic.recharge.rule', 'IC Recharge / إعادة التوزيع', 110),
        ('tax.xml.wizard', 'Tax XML / ملف XML الضريبي', 120),
    ]

    for model, name, seq in modules_actions:
        cr.execute("SELECT id FROM ir_model WHERE model = %s", (model,))
        model_row = cr.fetchone()
        if not model_row:
            print(f"  SKIP (model not found): {model}")
            continue

        # Create action
        cr.execute("SELECT id FROM ir_act_window WHERE res_model = %s LIMIT 1", (model,))
        action_row = cr.fetchone()
        if action_row:
            action_id = action_row[0]
        else:
            cr.execute("""
                INSERT INTO ir_act_window (name, res_model, view_mode, type)
                VALUES (%s, %s, 'tree,form', 'ir.actions.act_window')
                RETURNING id
            """, (name, model))
            action_id = cr.fetchone()[0]

        # Create menu
        cr.execute("SELECT id FROM ir_ui_menu WHERE name = %s AND parent_id = %s", (name, top_menu_id))
        if not cr.fetchone():
            cr.execute("""
                INSERT INTO ir_ui_menu (name, parent_id, sequence, active, action)
                VALUES (%s, %s, %s, true, %s)
            """, (name, top_menu_id, seq, f'ir.actions.act_window,{action_id}'))
            print(f"  Created: {name}")
        else:
            print(f"  Already exists: {name}")

    cr.commit()
    print("\nDone! Refresh browser to see ERP Migration menu.")
