# Arabic System Manual & Setup Handbook — Generator

This directory generates **two distinct Arabic deliverables** for the Port
Said Governorate Odoo 17 finance/supply-chain system, both sharing the same
docx infrastructure (`common.py`) and extracted-facts database
(`tools/modules_data.json`):

1. **System Manual** (`build.py` → `output/Paradise_AI_PortSaid_Odoo_System_Manual.docx`)
   — the end-user/functional ISO-grade manual (cover, document control, auto
   TOC, 15 chapters, numbered figures/tables, screenshot placeholders).
2. **Setup & Configuration Handbook** (`handbook_build.py` →
   `output/Paradise_AI_PortSaid_Setup_Configuration_Handbook.docx`) — a
   reverse-engineering-grade technical handbook for implementation/DBA/audit
   teams: full ACL dump, record rules, SQL constraints, cron jobs, a flat
   database catalogue, BPMN-style workflows, and explicit file-path
   citations for every fact. Anything that is genuinely runtime data (not in
   the source) is marked with the required sentence in `handbook_meta.NOT_FOUND`
   instead of being invented.

## Build

```bash
pip install -r requirements.txt
python3 tools/extract_modules.py   # refresh tools/modules_data.json from odoo_deployment_ar/addons
python3 build.py                   # writes the System Manual
python3 handbook_build.py          # writes the Setup & Configuration Handbook
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
- `content/chNN_*.py` — System Manual chapters, each exposing `build(mb)`.
  Chapters 6, 8 and 13 are data-driven off `modules_data.json` combined with
  hand-written narrative (purpose/business-need/limitations per module);
  the rest are authored directly.
- `build.py` — wires the System Manual chapters together and writes the `.docx`.
- `handbook_meta.py` / `handbook_content/chNN_*.py` / `handbook_build.py` —
  the Setup & Configuration Handbook's own metadata, chapters, and entry
  point. `common.py` additions specific to this handbook:
  `ManualBuilder.config_doc()` (the Purpose/Business Need/.../Best Practices
  config-page template) and `ManualBuilder.workflow_doc()` (the BPMN-style
  Actors/Inputs/Outputs/.../Related Security template), plus
  `add_index_entry()` / `ManualBuilder.index_entry()` / `add_index_section()`
  which wire up a real Word alphabetical `INDEX` field (distinct from the
  TOC) driven by hidden `XE` fields planted at every module/model in
  Chapter 6.

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
