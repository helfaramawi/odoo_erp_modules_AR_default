# Demo Conversion Plan

## Scope decision

This conversion was scoped, by explicit choice of the repository owner, to:

> **Anonymize + package**: rename all client/vendor references to neutral
> demo branding, centralize branding config, write demo seed-data
> modules, add Docker/compose + docs. Do **not** attempt to stand up a
> live Odoo instance inside the build sandbox — deployment/testing
> happens in the user's own environment.

This was chosen over two alternatives: (a) also standing up a local
Odoo+Postgres instance to smoke-test end to end, and (b) stopping after
discovery docs only. The reason: the build sandbox has no cloud account
and no pre-existing Odoo runtime, so "full 55-point spec including live
cloud deployment and UI smoke tests" was not achievable there regardless;
static, file-level work (anonymization, config, seed data, Docker
scaffolding, docs) is fully achievable and was prioritized.

**Consequence**: everything in this Demo Edition has been verified
*statically* (every `.py` parses, every `.xml` is well-formed, every
manifest `depends` resolves to a real module, no leftover identifying
strings) but **not** by actually booting Odoo against it. Treat the first
install as the real first test — see
[`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md).

## What was found (Phase 1 — Discovery)

- 36 installable custom Odoo 17 addon modules (plus one orphaned,
  manifest-less module) implementing a government financial/ERP system:
  general ledger, budget, fixed assets, procurement/tenders, custody,
  auctions, cheques, cash/revenue books, inventory, insurance, penalties,
  and ~30 statutory report forms — mostly in Arabic.
- Real client identity baked into module technical names, manifests,
  report headers/footers, and a base64-embedded governorate seal image
  (found in 55 places across 34 files) — not just prose.
- Real vendor identity (company name + website + email) in every
  manifest's `author`/`website` field and most report footers.
- Seven synthetic-looking but real-domain (`@<client>.gov.eg`) demo user
  accounts with named individuals in `l10n_eg_custody/data/demo_users.xml`.
- Two live external integrations: Egyptian Tax Authority (ETA) e-invoicing
  (`l10n_eg_eta_invoice`, hardcoded `https://api.invoicing.eta.gov.eg` /
  preprod URLs) and a configurable Credit Bureau API (`c7_credit_bureau`).
  No hardcoded secret *values* — credential fields ship empty.
  See [`INTEGRATIONS.md`](INTEGRATIONS.md).
- No Dockerfile, CI/CD, requirements.txt, or odoo.conf anywhere in the
  repo — it's a raw addons drop with no deployment scaffolding at all.

Full detail: [`ARCHITECTURE.md`](ARCHITECTURE.md), [`FEATURE_INVENTORY.md`](FEATURE_INVENTORY.md), [`BRANDING.md`](BRANDING.md).

## What was executed

| Phase | Status | Notes |
|---|---|---|
| 1. Discovery | Done | This document set |
| 2. Isolation | Done | `demo_edition/` is a separate copy; separate Docker Compose stack, separate `.env`, separate DB naming convention (`demo_*`, enforced by `demo-reset.sh`) |
| 3. Anonymization | Done | See `BRANDING.md` for the full before/after mapping |
| 4. Demo data | Done (master data) / Deferred (transactional) | See `DEMO_DATA.md` |
| 5. Feature repair | Partial | Anonymization-breaking issues fixed; two pre-existing, unrelated defects documented, not fixed (`KNOWN_LIMITATIONS.md`) |
| 6. Cloud preparation | Done (Docker) / Deferred (actual cloud deploy) | No cloud account available in the build environment |
| 7. Testing | Static only | No live Odoo instance available in the build environment; see below |
| 8. Documentation | Done | This folder |
| 9. Final acceptance | See `KNOWN_LIMITATIONS.md` | Honest punch list, not a clean bill of health |

## Verification performed (no live Odoo available)

- Every `.py` file in `demo_edition/addons/` parses with `ast.parse`.
- Every `.xml` file parses as well-formed XML (one pre-existing exception,
  present in production too — see `KNOWN_LIMITATIONS.md`).
- Every module's `depends` list resolves to either a real module folder in
  the tree or a standard Odoo 17 core module.
- Every `ir.model.access.csv` model reference matches its module's renamed
  model technical names.
- Repository-wide grep confirms zero remaining occurrences of the original
  client name, governorate name, vendor name, or their variants (see
  `BRANDING.md` for the exact search terms used).
- The one base64-embedded logo image was found and replaced at the byte
  level (MD5-verified before/after), not just at the filename level.

## What was explicitly not done

- Not actually installed against a running Odoo — no cloud credentials or
  pre-existing Odoo runtime were available in the build sandbox.
- Transactional demo scenario data (a completed purchase requisition to
  invoice flow, an awarded auction, a posted custody assignment) was not
  scripted — those custom models carry state-machine validation that's
  only safe to satisfy through the real business logic. `DEMO_DATA.md`
  and `DEMO_GUIDE.md` describe how to create this once, through the UI,
  on top of the seeded master data.
- No cloud deployment was performed (no account available). `DEPLOYMENT.md`
  gives instructions for AWS/Azure/GCP/DigitalOcean equivalent to the
  Docker Compose stack, untested against an actual account.
- No automated test suite was added.
