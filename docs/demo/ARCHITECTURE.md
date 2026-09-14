# Architecture

## Stack

| Layer | Technology |
|---|---|
| Application framework | Odoo 17 (Community) — Python 3, its own ORM, QWeb templating |
| Database | PostgreSQL 13+ |
| Backend language | Python 3 |
| Frontend | Odoo's own web client (OWL framework) + server-rendered QWeb reports (PDF via wkhtmltopdf/WeasyPrint) |
| Reporting | QWeb PDF reports (Arabic RTL, Amiri/Cairo/Noto fonts), one module (`demo_gov_reports`/`demo_gov_gl_reports`) overrides the PDF engine to WeasyPrint for two report types |
| Authentication | Odoo's built-in `res.users` (session-based); no external identity provider integrated |
| Authorization | Odoo `res.groups` + `ir.model.access.csv` + record rules, per module (see `ROLE_MATRIX.md`) |
| Background jobs | Odoo `ir.cron` (one scheduled job found: `l10n_eg_auction` auction closing cron) |
| External integrations | Egyptian Tax Authority e-invoicing (ETA) REST API; a configurable Credit Bureau REST API — see `INTEGRATIONS.md` |
| Deployment (production repo) | None present — no Dockerfile, CI/CD, or `odoo.conf` in the source tree; `odoo_deployment_ar/addons/install.sh` is a manual shell installer only |
| Deployment (Demo Edition) | Added: Dockerfile (official `odoo:17.0` base) + `docker-compose.demo.yml` (Odoo + Postgres) |

The repository ships **addons only** — it depends on an Odoo 17 core
checkout that is not part of this repo (see `demo_edition/README.md` for
how to obtain it).

## Module dependency structure (Demo Edition naming)

```mermaid
flowchart TB
    subgraph core["Odoo 17 core"]
        base & account & stock & purchase & sale & hr & mail
    end

    subgraph gl["General Ledger core chain"]
        daftar55["demo_gov_daftar55<br/>(sequential payment register)"]
        daftar224["demo_gov_daftar224<br/>(dual daily register)"]
        commitment["demo_gov_commitment<br/>(budget commitment)"]
        subsidiary["demo_gov_subsidiary_books"]
        gla["general_ledger_ar"]
    end

    subgraph menu["Unified UI"]
        gov_menu["demo_gov_menu<br/>(single-tab menu structure)"]
        dashboard["demo_gov_dashboard<br/>(executive KPIs)"]
    end

    subgraph procurement["Procurement & Tenders"]
        committee["procurement_committee"]
        adjudication["procurement_adjudication"]
        auction["l10n_eg_auction"]
        requisition["demo_gov_scm_requisition"]
        po_bridge["demo_gov_scm_purchase_bridge"]
        warehouse_cmt["demo_gov_scm_warehouse"]
    end

    subgraph inventory["Inventory & Custody"]
        custody["l10n_eg_custody"]
        addition["stock_addition_permit"]
        stocktaking["stock_stocktaking_eg"]
        scm_issue["demo_gov_scm_issue"]
        stock_bridge["demo_gov_stock_finance_bridge"]
    end

    subgraph finance["Cash, Cheques, Advances, Assets"]
        cash["demo_gov_cash_books"]
        cheques["demo_gov_cheques"]
        transfers["demo_gov_cash_transfers"]
        advances["demo_gov_advances"]
        assets["demo_gov_fixed_assets"]
        funds["demo_gov_special_funds"]
        insurance["demo_gov_insurance_subsidiary"]
        penalties["demo_gov_penalties"]
        revenue["demo_gov_revenue_books"]
    end

    subgraph reporting["Reporting & Compliance"]
        reports["demo_gov_reports /<br/>demo_gov_gl_reports /<br/>demo_gov_acct_reports"]
        budget["demo_gov_budget_planning"]
        eta["l10n_eg_eta_invoice"]
        form69["demo_gov_form69 -> demo_gov_form75"]
    end

    subgraph generic["Generic add-ons (c1-c13)"]
        c_mods["Approval matrix, batch posting,<br/>aging, financial dimensions,<br/>cost centre, credit bureau,<br/>contract pricing, tax XML export, ..."]
    end

    subgraph demoinfra["Demo Edition additions"]
        branding["demo_branding<br/>(centralized config + banner + /api/health)"]
        seed["demo_gov_seed_data<br/>(synthetic users/partners/items)"]
    end

    core --> gl
    core --> procurement
    core --> inventory
    core --> finance
    core --> generic
    gl --> menu
    procurement --> menu
    inventory --> menu
    finance --> menu
    gl --> finance
    gl --> reporting
    gl --> eta
    committee --> adjudication
    committee --> auction
    requisition --> po_bridge --> warehouse_cmt
    custody --> assets
    custody --> scm_issue
    branding --> seed
    core --> branding
```

## Report layout convention

Most printed reports (`demo_gov_reports`, `demo_gov_fixed_assets`,
`demo_gov_daftar55`, etc.) share a single header/footer template
(`demo_gov_reports/reports/gov_shared_layout.xml`) rather than each
defining its own. That shared template is exactly where the anonymized
governorate seal and generic identity text live — see `BRANDING.md`.

## Notable design characteristics

- **State-machine-heavy custom models**: procurement adjudication,
  auctions, and Form 75 monthly closing all implement explicit workflow
  states (draft → ... → posted/awarded/closed) enforced in Python, not
  just UI hints. This is why transactional demo data was not scripted as
  raw XML (see `DEMO_DATA.md`) — it must go through the real transitions.
- **One shared PDF engine override** (`weasyprint_override.py`, present
  in `demo_gov_reports` and `demo_gov_gl_reports`) routes specific report
  names through WeasyPrint instead of Odoo's default wkhtmltopdf, for
  better Arabic shaping.
