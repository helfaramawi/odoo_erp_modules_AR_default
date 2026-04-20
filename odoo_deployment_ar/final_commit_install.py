import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo.tools import config

config.parse_config([
    '--config=/etc/odoo/odoo.conf',
    '--database=odoo17',
    '--no-http',
])

import odoo.sql_db
import odoo.modules.registry as registry_mod

db = odoo.sql_db.db_connect('odoo17')

# Step 1: commit the to-install state in its own transaction
with db.cursor() as cr:
    cr.execute("""
        UPDATE ir_module_module 
        SET state = 'to install' 
        WHERE name IN ('c1_purchase_approval_matrix', 'c6_cost_centre')
    """)
    cr.commit()
    print("Committed to-install state")

# Step 2: close all connections and reload
odoo.sql_db.close_db('odoo17')

# Step 3: load with update_module=True in fresh registry
import odoo.modules.loading as loading
import odoo.modules.registry as reg_module

try:
    # Force a new registry that processes to-install modules
    if 'odoo17' in reg_module.Registry.registries:
        del reg_module.Registry.registries['odoo17']
    
    registry = reg_module.Registry.new('odoo17', update_module=True)
    print("SUCCESS: modules should now be installed")
    
    # Verify
    db2 = odoo.sql_db.db_connect('odoo17')
    with db2.cursor() as cr:
        cr.execute("SELECT name, state FROM ir_module_module WHERE name IN ('c1_purchase_approval_matrix','c6_cost_centre')")
        for row in cr.fetchall():
            print(f"  {row[0]}: {row[1]}")
        cr.commit()

except Exception as e:
    import traceback
    print("ERROR:")
    traceback.print_exc()
    
    # Even if registry fails, check what happened to module state
    db3 = odoo.sql_db.db_connect('odoo17')
    with db3.cursor() as cr:
        cr.execute("SELECT name, state FROM ir_module_module WHERE name IN ('c1_purchase_approval_matrix','c6_cost_centre')")
        for row in cr.fetchall():
            print(f"  {row[0]}: {row[1]}")
