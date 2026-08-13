import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo.tools import config
config.parse_config(['--config=/etc/odoo/odoo.conf', '--database=odoo17', '--no-http'])

import odoo.sql_db
db = odoo.sql_db.db_connect('odoo17')

with db.cursor() as cr:

    # Get admin user id
    cr.execute("SELECT id FROM res_users WHERE login='admin' LIMIT 1")
    admin_id = cr.fetchone()[0]

    # Check if our top menu already exists
    cr.execute("SELECT id FROM ir_ui_menu WHERE name='ERP Migration' AND parent_id IS NULL")
    existing = cr.fetchone()

    if existing:
        top_menu_id = existing[0]
        print(f"Top menu already exists: {top_menu_id}")
    else:
        # Create top-level menu
        cr.execute("""
            INSERT INTO ir_ui_menu (name, parent_id, sequence, active, web_icon)
            VALUES ('ERP Migration / ترحيل ERP', NULL, 99, true, 'fa-cogs')
            RETURNING id
        """)
        top_menu_id = cr.fetchone()[0]
        print(f"Created top menu: {top_menu_id}")

    # Get all our module actions
    modules_actions = [
        ('c1_purchase_approval_matrix', 'purchase.approval.threshold', 'Approval Matrix / مصفوفة الاعتماد', 10),
        ('c2_batch_posting', 'batch.posting.config', 'Batch Posting / الترحيل الدفعي', 20),
        ('c3_aging_report', 'aging.report.wizard', 'Aging Report / تقرير الأعمار', 30),
        ('c4_payment_matching', 'account.payment', 'Payment Matching / مطابقة المدفوعات', 40),
        ('c5_financial_dimensions', 'financial.dimension', 'Financial Dimensions / الأبعاد المالية', 50),
        ('c6_cost_centre', 'purchase.order', 'Cost Centre POs / مراكز التكلفة', 60),
        ('c7_credit_bureau', 'credit.bureau.config', 'Credit Bureau / مكتب الائتمان', 70),
        ('c8_contract_pricing', 'contract.price', 'Contract Prices / أسعار العقود', 80),
        ('c10_inventory_revaluation', 'inventory.revaluation.wizard', 'Inventory Revaluation / إعادة تقييم المخزون', 90),
        ('c11_budget_alert', 'project.project', 'Budget Alerts / تنبيهات الميزانية', 100),
        ('c12_intercompany_recharge', 'ic.recharge.rule', 'IC Recharge / إعادة التوزيع', 110),
        ('c13_tax_xml_export', 'tax.xml.wizard', 'Tax XML / ملف XML الضريبي', 120),
    ]

    for module, model, name, seq in modules_actions:
        # Check if model exists
        cr.execute("SELECT id FROM ir_model WHERE model = %s", (model,))
        model_row = cr.fetchone()
        if not model_row:
            print(f"  SKIP (model not found): {model}")
            continue
        model_id = model_row[0]

        # Create action if needed
        cr.execute("""
            SELECT id FROM ir_act_window 
            WHERE res_model = %s AND name = %s
        """, (model, name))
        action_row = cr.fetchone()

        if action_row:
            action_id = action_row[0]
        else:
            cr.execute("""
                INSERT INTO ir_act_window 
                (name, res_model, view_mode, type, binding_model_id)
                VALUES (%s, %s, 'tree,form', 'ir.actions.act_window', NULL)
                RETURNING id
            """, (name, model))
            action_id = cr.fetchone()[0]
            print(f"  Created action for: {model}")

        # Check if menu item already exists under our top menu
        cr.execute("""
            SELECT id FROM ir_ui_menu 
            WHERE name = %s AND parent_id = %s
        """, (name, top_menu_id))
        menu_row = cr.fetchone()

        if not menu_row:
            cr.execute("""
                INSERT INTO ir_ui_menu 
                (name, parent_id, sequence, active, action)
                VALUES (%s, %s, %s, true, %s)
                RETURNING id
            """, (name, top_menu_id, seq, f'ir.actions.act_window,{action_id}'))
            menu_id = cr.fetchone()[0]
            print(f"  Created menu: {name} (id={menu_id})")
        else:
            print(f"  Menu exists: {name}")

    cr.commit()
    print("\nAll done! Refresh Odoo to see the ERP Migration menu.")
