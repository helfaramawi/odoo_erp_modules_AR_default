import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo.tools import config

config.parse_config([
    '--config=/etc/odoo/odoo.conf',
    '--database=odoo17',
    '--no-http',
])

import odoo.modules.registry as registry_mod
from odoo.modules.loading import load_modules
import odoo.service.db

modules_to_install = [
    'c1_purchase_approval_matrix',
    'c6_cost_centre', 
    'c7_credit_bureau',
    'c8_contract_pricing',
]

db = odoo.sql_db.db_connect('odoo17')

with db.cursor() as cr:
    # Mark modules as to_install
    names = ','.join("'%s'" % m for m in modules_to_install)
    cr.execute("UPDATE ir_module_module SET state='to install' WHERE name IN (%s)" % names)
    cr.execute("SELECT name, state FROM ir_module_module WHERE name IN (%s)" % names)
    rows = cr.fetchall()
    for name, state in rows:
        print(f"  {name}: {state}")
    cr.commit()
    print("Marked as to install. Triggering load...")

# Now trigger module loading
try:
    reg = registry_mod.Registry.new('odoo17', update_module=True)
    print("SUCCESS: Registry updated")
except Exception as e:
    print(f"Error during registry update: {e}")

# Check final state
with db.cursor() as cr:
    cr.execute("SELECT name, state FROM ir_module_module WHERE name IN (%s) ORDER BY name" % names)
    print("\nFinal states:")
    for name, state in cr.fetchall():
        print(f"  {name}: {state}")
