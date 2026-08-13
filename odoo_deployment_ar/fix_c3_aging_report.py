# -*- coding: utf-8 -*-
"""
Fix c3_aging_report QWeb crash:
TypeError: 'NoneType' object is not subscriptable
Cause: template uses data['...'] while report is sometimes rendered with data=None.

Run inside Odoo container:
python3 /tmp/fix_c3_aging_report.py
"""

from pathlib import Path
import re
import shutil

BASE = Path("/mnt/extra-addons/c3_aging_report")
BACKUP = Path("/mnt/extra-addons/_backup_c3_aging_report_fix")
BACKUP.mkdir(parents=True, exist_ok=True)

if not BASE.exists():
    raise SystemExit("ERROR: /mnt/extra-addons/c3_aging_report not found")

patterns = [
    "*.xml",
    "*.py",
]

changed = []

def patch_text(text):
    original = text

    # QWeb/Python expressions like data['report_type'] or data["date_to"]
    text = re.sub(
        r"data\[['\"]([^'\"]+)['\"]\]",
        r"(data or {}).get('\1')",
        text,
    )

    # Also handle escaped XML variants if any.
    text = re.sub(
        r"data\[\&quot;([^&]+)\&quot;\]",
        r"(data or {}).get('\1')",
        text,
    )
    text = re.sub(
        r"data\[\&#39;([^&]+)\&#39;\]",
        r"(data or {}).get('\1')",
        text,
    )

    return text, text != original

for pat in patterns:
    for path in BASE.rglob(pat):
        if "__pycache__" in str(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if "data[" not in text and "data[&quot;" not in text and "data[&#39;" not in text:
            continue

        new_text, did_change = patch_text(text)
        if did_change:
            rel = path.relative_to(BASE)
            backup_path = BACKUP / rel
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path)
            path.write_text(new_text, encoding="utf-8")
            changed.append(str(path))

print("DONE")
print("Changed files:")
for p in changed:
    print("-", p)

if not changed:
    print("No files changed. The template may already be fixed or uses another pattern.")
