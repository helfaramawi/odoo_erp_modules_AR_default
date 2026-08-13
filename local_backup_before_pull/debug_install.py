import sys, traceback
sys.path.insert(0, '/usr/lib/python3/dist-packages')

import odoo
from odoo.tools import config

config.parse_config([
    '--config=/etc/odoo/odoo.conf',
    '--database=odoo17',
    '--no-http',
    '--log-level=debug',
])

import odoo.modules.registry as registry_mod
import odoo.sql_db

db = odoo.sql_db.db_connect('odoo17')

# First check what error c1 gives
with db.cursor() as cr:
    cr.execute("UPDATE ir_module_module SET state='to install' WHERE name IN ('c1_purchase_approval_matrix','c6_cost_centre')")
    cr.commit()

print("Attempting install with full traceback...")
try:
    reg = registry_mod.Registry.new('odoo17', update_module=True)
    print("SUCCESS")
except Exception as e:
    print("FULL ERROR:")
    traceback.print_exc()

with db.cursor() as cr:
    cr.execute("SELECT name, state FROM ir_module_module WHERE name IN ('c1_purchase_approval_matrix','c6_cost_centre')")
    for row in cr.fetchall():
        print(f"{row[0]}: {row[1]}")
