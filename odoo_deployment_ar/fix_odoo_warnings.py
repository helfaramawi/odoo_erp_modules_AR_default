# -*- coding: utf-8 -*-
from pathlib import Path
import re
import shutil

backup_dir = Path('/mnt/extra-addons/_backup_warning_fix')
backup_dir.mkdir(parents=True, exist_ok=True)

def backup_file(p):
    p = Path(p)
    if p.exists():
        dst = backup_dir / (p.name + '.bak')
        shutil.copy2(p, dst)
        print(f"backup: {p} -> {dst}")
        return True
    print(f"missing, skipped backup: {p}")
    return False

def remove_kwarg_from_file(path, kwarg):
    p = Path(path)
    if not p.exists():
        print(f"missing: {p}")
        return
    backup_file(p)
    txt = p.read_text(encoding='utf-8')
    before = txt

    # Remove forms like:
    # , invisible="..."
    # invisible="...",
    # , password=True
    # tracking=True,
    txt = re.sub(rf",\s*\n\s*{kwarg}\s*=\s*(['\"]).*?\1", "", txt)
    txt = re.sub(rf",\s*\n\s*{kwarg}\s*=\s*True", "", txt)
    txt = re.sub(rf"\s+{kwarg}\s*=\s*(['\"]).*?\1\s*,?", "", txt)
    txt = re.sub(rf"\s+{kwarg}\s*=\s*True\s*,?", "", txt)

    p.write_text(txt, encoding='utf-8')
    print(f"fixed {kwarg}: {p} | changed={before != txt}")

# 1) invisible wrongly used in Python fields
for file_path in [
    '/mnt/extra-addons/l10n_eg_auction/models/auction_request.py',
    '/mnt/extra-addons/port_said_advances/models/advance.py',
    '/mnt/extra-addons/stock_addition_permit/models/addition_permit.py',
]:
    remove_kwarg_from_file(file_path, 'invisible')

# 2) password=True wrongly used in Python fields
remove_kwarg_from_file('/mnt/extra-addons/l10n_eg_eta_invoice/models/eta_config.py', 'password')

# 3) tracking=True warnings
for file_path in [
    '/mnt/extra-addons/port_said_form69/models/form69.py',
    '/mnt/extra-addons/procurement_adjudication/models/adjudication.py',
    '/mnt/extra-addons/port_said_scm_warehouse/models/warehouse_addition.py',
]:
    remove_kwarg_from_file(file_path, 'tracking')

# 4) translated stored related field warning
p = Path('/mnt/extra-addons/l10n_eg_custody/models/custody_assignment.py')
if p.exists():
    backup_file(p)
    txt = p.read_text(encoding='utf-8')
    before = txt
    # Remove store=True only near product_description definition block.
    pattern = r"(product_description\s*=\s*fields\.\w+\([\s\S]*?\))"
    def fix_block(m):
        block = m.group(1)
        block = re.sub(r",\s*\n\s*store\s*=\s*True", "", block)
        block = re.sub(r"\s+store\s*=\s*True\s*,?", "", block)
        return block
    txt = re.sub(pattern, fix_block, txt, count=1)
    p.write_text(txt, encoding='utf-8')
    print(f"fixed product_description store=True: {p} | changed={before != txt}")
else:
    print(f"missing: {p}")

print("DONE")
