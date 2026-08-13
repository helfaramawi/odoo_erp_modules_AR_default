base = '/mnt/extra-addons'

# Create proper README.rst files
open(f'{base}/c1_purchase_approval_matrix/README.rst', 'w').write(
    'PO Approval Matrix\n==================\n\nMulti-tier PO approval workflow.\n'
)
open(f'{base}/c6_cost_centre/README.rst', 'w').write(
    'Cost Centre\n===========\n\nCost centre field on purchase orders.\n'
)

# Also patch the manifests to remove any description that could cause RST issues
import ast, re

for mod in ['c1_purchase_approval_matrix', 'c6_cost_centre']:
    path = f'{base}/{mod}/__manifest__.py'
    with open(path) as f:
        content = f.read()
    # Remove description key entirely
    content = re.sub(r"\s*'description'\s*:\s*['\"][^'\"]*['\"],?", "", content)
    content = re.sub(r'\s*"description"\s*:\s*"[^"]*",?', "", content)
    with open(path, 'w') as f:
        f.write(content)
    print(f'Fixed manifest: {mod}')

# Verify manifests are valid Python
import py_compile
for mod in ['c1_purchase_approval_matrix', 'c6_cost_centre']:
    path = f'{base}/{mod}/__manifest__.py'
    try:
        py_compile.compile(path, doraise=True)
        print(f'Manifest OK: {mod}')
    except Exception as e:
        print(f'Manifest ERROR: {mod}: {e}')

print('Done')
