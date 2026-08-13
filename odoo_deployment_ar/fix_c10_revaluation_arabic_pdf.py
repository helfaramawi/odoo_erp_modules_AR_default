# -*- coding: utf-8 -*-
from pathlib import Path
import shutil
from datetime import datetime

path = Path("/mnt/extra-addons/c10_inventory_revaluation/report/revaluation_report.xml")
backup_dir = Path("/mnt/extra-addons/_backup_c10_inventory_revaluation")
backup_dir.mkdir(parents=True, exist_ok=True)
backup = backup_dir / ("revaluation_report_%s.xml.bak" % datetime.now().strftime("%Y%m%d_%H%M%S"))

if not path.exists():
    raise SystemExit("ERROR: report file not found: %s" % path)

shutil.copy2(path, backup)

txt = path.read_text(encoding="utf-8")

old = """<t t-foreach="docs" t-as="wizard">
        <div style="direction:rtl; font-family:'Cairo',Arial,sans-serif; font-size:10px; padding:20px;">"""

new = """<t t-foreach="docs" t-as="wizard">
        <t t-call="web.basic_layout">
        <meta charset="utf-8"/>
        <div class="page" dir="rtl" lang="ar" style="direction:rtl; unicode-bidi:embed; text-align:right; font-family:'DejaVu Sans','Amiri',Arial,sans-serif; font-size:10px; padding:20px;">"""

if old not in txt and '<t t-call="web.basic_layout">' not in txt:
    print("WARNING: exact opening block not found. Applying fallback replacements.")
    txt = txt.replace(
        '<t t-foreach="docs" t-as="wizard">',
        '<t t-foreach="docs" t-as="wizard">\n        <t t-call="web.basic_layout">\n        <meta charset="utf-8"/>',
        1
    )
    txt = txt.replace(
        '<div style="direction:rtl; font-family:\'Cairo\',Arial,sans-serif; font-size:10px; padding:20px;">',
        '<div class="page" dir="rtl" lang="ar" style="direction:rtl; unicode-bidi:embed; text-align:right; font-family:\'DejaVu Sans\',\'Amiri\',Arial,sans-serif; font-size:10px; padding:20px;">',
        1
    )
elif old in txt:
    txt = txt.replace(old, new, 1)

# Close the inserted web.basic_layout only if not already closed
if '<t t-call="web.basic_layout">' in txt and '<!-- C10_BASIC_LAYOUT_CLOSED -->' not in txt:
    marker = """
        </div>
      </t>
    </t>"""
    replacement = """
        </div>
        <!-- C10_BASIC_LAYOUT_CLOSED -->
        </t>
      </t>
    </t>"""
    txt = txt.replace(marker, replacement, 1)

# Improve table direction and font, but avoid duplicating if already patched
txt = txt.replace(
    '<table style="width:100%; border-collapse:collapse; font-size:9px;">',
    '<table dir="rtl" style="width:100%; border-collapse:collapse; font-size:9px; direction:rtl; text-align:right; font-family:\'DejaVu Sans\',\'Amiri\',Arial,sans-serif;">'
)

path.write_text(txt, encoding="utf-8")

print("DONE")
print("Backup:", backup)
print("Patched:", path)
