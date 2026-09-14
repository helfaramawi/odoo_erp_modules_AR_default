# Branding & Anonymization

## Centralized branding config

The Demo Edition ships a `demo_branding` module (`demo_edition/addons/demo_branding/`)
as the single source of truth for identity strings, instead of each
report/screen hard-coding them. Backed by a dedicated `demo.branding.config`
record, editable at **Settings > Demo Branding** (a standalone screen
rather than an addition to Odoo's own General Settings page — see
`KNOWN_LIMITATIONS.md` for why):

```json
{
  "application_name": "Enterprise Digital Operations Platform",
  "organization_name": "Public Services Organization",
  "environment": "demo",
  "support_email": "support@example.com",
  "support_phone": "+000 000 0000"
}
```

Any module can read it via `self.env['demo.branding'].get_all()` /
`get_value(key)`. It currently drives:
- the login-screen "DEMO ENVIRONMENT" banner (`demo_branding/views/webclient_templates.xml`)
- the `/api/health` response's `environment` field
- the demo-mode gate in the two external integrations (`INTEGRATIONS.md`)

**Not yet wired dynamically**: the ~30 printed report templates still
carry their (now-anonymized) identity text as static strings rather than
pulling live from `demo.branding`. They are safe (no real identity left
in them — see below) but not centrally editable without a code change.
Recorded as a follow-up in `KNOWN_LIMITATIONS.md` rather than attempted
here, because verifying report-template QWeb context wiring needs a live
Odoo instance, which was out of scope for this pass.

## What was found and replaced

All replacements were applied file-by-file across `demo_edition/addons/`
(the original `odoo_deployment_ar/` tree is untouched). Search terms used
to confirm zero remaining occurrences, run after every change:
`port_said`, `portsaid`, `Port Said`, `PORT SAID`, `Paradise`, `بورسعيد`.

| Category | Original | Replaced with | Where found |
|---|---|---|---|
| Client (governorate) name, English | "Port Said Governorate General Diwan", "Port Said Governorate", "Port Said" | "Demo Governorate General Diwan", "Demo Governorate" | ~120 occurrences: manifests, `README.md`, report footers |
| Client (governorate) name, Arabic | "محافظة بورسعيد", "بورسعيد" | "المحافظة التجريبية" ("the Demo Governorate") | ~180 occurrences: report headers/footers across nearly every module |
| Governorate seal/emblem (image) | Real Port Said Governorate flag/seal — PNG file (`port_said_logo.png`, identical MD5 across 6 modules) **and** the same seal embedded as base64 inside QWeb templates (55 occurrences across 34 report files) | Generic neutral placeholder badge (navy circle + abstract document mark, no state iconography) | `static/img/` in 6 modules; `gov_shared_layout.xml` and every report inheriting it |
| Vendor/implementer name | "Paradise AI Solutions", "Paradise Integrated Solutions", "Paradise AI" (inconsistent across files) | "Enterprise Solutions Demo" | Every module's `author` manifest field (36 modules), ~20 report footers |
| Vendor website | `https://paradise-solutions.com`, `https://paradise.solutions.com` (two inconsistent domains in source) | `https://example.com` (IANA-reserved documentation domain) | `website` manifest field, 8 modules |
| Vendor contact email | `info@paradise-solutions.com` | `support@example.com` | `README.md` |
| Government staff emails | `<name>@portsaid.gov.eg` (7 addresses, real government domain pattern) | `<role>@demo-gov.example` | `l10n_eg_custody/data/demo_users.xml` |
| Named individuals (demo users) | 7 real-looking Arabic full names (e.g. "أشرف محمد علي", "نادية عبد السلام") tied to specific job titles | Role-labeled accounts only: "مدير عام - حساب تجريبي" (Director General — demo account), logins `demo.admin`, `demo.contracts_manager`, etc. | `l10n_eg_custody/data/demo_users.xml` (rewritten, not just find-replaced) |
| Module technical-name prefix | `port_said_*` (26 modules), `portsaid_dashboard`, model names `port_said.*`, XML ID namespaces, `ir.model.access.csv` model refs, `/portsaid/dashboard` HTTP route, Python identifiers (`PORT_SAID_PREFIXES`, `is_port_said`) | `demo_gov_*`, `demo_gov.*`, `/demo_gov/dashboard`, `DEMO_GOV_PREFIXES`/`is_demo_gov` | Directory names + every cross-reference (manifests, XML `ref=`, CSV, Python) |
| Demo account password | Hard-coded `Diwan@2024` for all 7 accounts | `Demo@2024` default, overridable via `DEMO_USERS_PASSWORD` env var applied by a post-install hook | `l10n_eg_custody/data/demo_users.xml`, `demo_gov_seed_data/__init__.py` |

## What was intentionally kept

- **Regulatory/legal citations** (Law 182/2018, Min. Finance Decree
  692/2019, GAFI, "Egyptian Government" in module descriptions, "ETA" /
  Egyptian Tax Authority as the integration target, `l10n_eg_*` module
  naming). These describe the *regulatory framework* the feature set
  implements (an Odoo Egypt-localization convention, `l10n_eg_` is the
  standard prefix used by many public Odoo community modules), not the
  specific client. Removing them would misrepresent what the software
  actually does. Only the *client's own* identity (the governorate,
  vendor) was removed.
- **"الديوان العام" (General Diwan/Bureau)** — a generic Egyptian
  government-accounting term used by any governorate's central
  secretariat, not unique to the original client. Kept as functional
  terminology, same treatment as keeping "Finance Department" in the
  spec's own examples.
- **Module icons** (`static/description/icon.png/svg`) — generic
  filing-box style icons, not client-identifying; verified visually
  before deciding to keep them.

## Verification method

1. Automated ordered string-replacement across all text files
   (`.py .xml .csv .md .rst .html .css .js .sh .bat .conf`), longest/most
   specific phrases first to avoid partial-word corruption (e.g. the
   Arabic construct "لمحافظة بورسعيد" needed a grammar fix pass after the
   literal replacement — caught by re-reading a sample of affected files).
2. Every embedded image was checked by MD5 (static files) or by
   decoding+viewing (the base64 case) before and after — not assumed safe
   from the surrounding text alone. The base64 case would have been
   missed by a files-only sweep; it was only found by grepping for
   `data:image/...;base64,` inside `.xml`/`.py` and clustering by hash.
3. Final repository-wide grep for all search terms above, and for
   emails/phone numbers/IP addresses, returned zero hits in
   `demo_edition/` (see `SECURITY_REVIEW.md` for the full command list).
