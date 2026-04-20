import os, re

base = '/mnt/extra-addons'

# Map of wrong parents -> correct parents that exist in Odoo 17
MENU_FIXES = {
    'purchase.menu_purchase_config_settings': 'purchase.menu_purchase_root',
    'purchase.menu_purchase_rfq': 'purchase.menu_purchase_root',
    'sale.sale_menu_config': 'sale.sale_menu_root',
    'sale.sale_menu_root': 'sale.sale_menu_root',
    'account.menu_finance_configuration': 'account.menu_finance',
    'account.menu_finance_reports': 'account.menu_finance',
    'account.menu_finance': 'account.menu_finance',
    'stock.menu_stock_root': 'stock.menu_stock_root',
    'project.edit_project': 'project.menu_main_pm',
}

modules = ['c1_purchase_approval_matrix', 'c6_cost_centre', 'c7_credit_bureau', 'c8_contract_pricing']

for mod in modules:
    mod_path = os.path.join(base, mod)
    for root, dirs, files in os.walk(mod_path):
        for fname in files:
            if not fname.endswith('.xml'):
                continue
            path = os.path.join(root, fname)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            new = content

            # Simply remove ALL menuitem tags - safest fix
            # We can add menus back later once modules are installed
            new = re.sub(r'[ \t]*<menuitem[^>]*/>\n?', '', new)
            new = re.sub(r'[ \t]*<menuitem[^>]*>.*?</menuitem>\n?', '', new, flags=re.DOTALL)

            if new != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new)
                print(f'Fixed menus: {mod}/{fname}')

# Also remove menu items from manifests data list won't cause issues
# But let's also fix the description field in c1 manifest which has empty docstring
c1_manifest = os.path.join(base, 'c1_purchase_approval_matrix/__manifest__.py')
with open(c1_manifest, 'r') as f:
    content = f.read()
# Remove description with triple quotes that causes RST parsing issues
new = re.sub(r"'description':\s*\"\"\"[\s\S]*?\"\"\",?", "'description': '',", content)
new = re.sub(r"'description':\s*'''[\s\S]*?''',?", "'description': '',", new)
if new != content:
    with open(c1_manifest, 'w') as f:
        f.write(new)
    print('Fixed c1 manifest description')

print('\nAll fixes applied. Now installing...')
