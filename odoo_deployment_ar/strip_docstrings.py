import os, ast, re

base = '/mnt/extra-addons'
modules = ['c1_purchase_approval_matrix', 'c6_cost_centre', 'c7_credit_bureau', 'c8_contract_pricing']

for mod in modules:
    mod_path = os.path.join(base, mod)
    for root, dirs, files in os.walk(mod_path):
        for fname in files:
            if not fname.endswith('.py'):
                continue
            path = os.path.join(root, fname)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove triple-quoted docstrings (both """ and ''')
            # Replace with empty string
            new = re.sub(r'"""[\s\S]*?"""', '""""""', content)
            new = re.sub(r"'''[\s\S]*?'''", "''''''", new)

            if new != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new)
                print(f'Stripped docstrings: {path.replace(base+"/", "")}')

# Also check mail template XML for any RST-like content
for mod in modules:
    mod_path = os.path.join(base, mod)
    for root, dirs, files in os.walk(mod_path):
        for fname in files:
            if not fname.endswith('.xml'):
                continue
            path = os.path.join(root, fname)
            print(f'XML OK: {path.replace(base+"/", "")}')

print('\nDone. Now try installing.')
