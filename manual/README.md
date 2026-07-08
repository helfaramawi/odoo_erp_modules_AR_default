# Arabic System Manual — Generator

Generates `output/Paradise_AI_PortSaid_Odoo_System_Manual.docx`, the Arabic
system manual for the Port Said Governorate Odoo 17 finance/supply-chain
system, per the ISO-grade spec requested (cover, document control, auto TOC,
15 chapters, numbered figures/tables, screenshot placeholders, etc.).

## Build

```bash
pip install -r requirements.txt
python3 tools/extract_modules.py   # refresh tools/modules_data.json from odoo_deployment_ar/addons
python3 build.py                   # writes output/Paradise_AI_PortSaid_Odoo_System_Manual.docx
```

## Layout

- `common.py` — docx building blocks: RTL styling, cover page, document
  control, real Word TOC/List-of-Figures/List-of-Tables fields, numbered
  headings/figures/tables, screen/report/field/module documentation
  templates.
- `meta.py` — cover page & document control data (system name, revisions,
  approvals, distribution list). Fields marked `__________` are placeholders
  for the client to fill in.
- `tools/extract_modules.py` — parses every addon under
  `odoo_deployment_ar/addons/` (manifest, models, fields, menus, actions,
  reports, buttons, workflow states) via AST/XML into `tools/modules_data.json`.
  Re-run this after any change to the addons so Chapter 6/8/13 stay accurate.
- `content/chNN_*.py` — one module per chapter, each exposing `build(mb)`.
  Chapters 6, 8 and 13 are data-driven off `modules_data.json` combined with
  hand-written narrative (purpose/business-need/limitations per module);
  the rest are authored directly.
- `build.py` — wires everything together and writes the final `.docx`.

## Notes

- Chapter 7 (AI Agents) documents, truthfully, that no AI/LLM code exists in
  the inspected repository — it keeps the full required section structure as
  placeholders for future work rather than inventing content.
- Sections the repository doesn't cover (e.g. Manufacturing/Fleet/Rental in
  Chapter 5, infra specifics in Chapter 2) are marked `[عنصر نائب]`
  (placeholder) per the manual's own instruction to mark unavailable
  information explicitly rather than invent it.
- Screenshot placeholders are text boxes reading `[لقطة شاشة هنا — ...]`
  with a numbered "شكل" caption; real screenshots need to be captured from a
  running instance and dropped in before final client delivery.
