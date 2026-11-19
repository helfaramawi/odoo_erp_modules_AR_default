# Demo Guide

Recommended sequence for a first-time presenter to build a working
"golden" demo database, and for anyone giving the demo afterward.

## 1. Build the golden database (once, before any presentation)

```bash
cd demo_edition/scripts/demo-seed
APP_ENV=demo DEMO_USERS_PASSWORD='<your-password>' ./demo-reset.sh
```

This installs the module set and loads the master data in `DEMO_DATA.md`.
Dashboards and reports will still look empty at this point — that's
expected, because transactional records aren't scripted (see
`DEMO_DATA.md` for why). Walk through the scenarios below once, in order,
using the demo accounts, then `pg_dump` this database and restore it
before each future presentation instead of repeating the walkthrough.

## 2. Walk each scenario once (produces the demo's transactional data)

1. **Login** as `demo.admin` — show the DEMO ENVIRONMENT banner on the
   login screen. (The unified "الديوان العام" single-tab menu structure,
   `demo_gov_menu`, is not part of this walkthrough — see
   `KNOWN_LIMITATIONS.md`; each module shows under Odoo's normal Apps
   menu instead.)
2. **Organization structure** — Settings > Users & Companies: show the
   seven role-based demo accounts and, in Settings > General Settings >
   Demo Branding, the centralized application/organization name config.
3. **Procurement workflow** — log in as `demo.contracts_officer`: create a
   purchase requisition (`demo_gov_scm_requisition`) against a demo
   vendor and item, then as `demo.contracts_manager` form a committee
   (`procurement_committee`), then as `demo.adjudication_chairman` run it
   through technical/financial envelope adjudication
   (`procurement_adjudication`) to award, then confirm the auto-generated
   Purchase Order.
4. **Inventory / custody** — log in as `demo.warehouse_manager`: receive
   the PO via `stock_addition_permit` (inspection report + Form 1), then
   assign custody of a durable item (`l10n_eg_custody`, Form 193) to
   another demo employee.
5. **Auction** — as `demo.contracts_manager`, create an auction request
   (`l10n_eg_auction`) for a surplus item, run the sale path through to
   an awarded bid.
6. **Finance** — as `demo.admin`: post the resulting entries through
   Daftar 55/224, show a Form 69 daily reckoning, and (if a full month of
   activity exists) a Form 75 monthly closing.
7. **Reporting** — run a trial balance and a general ledger report
   (`demo_gov_gl_reports`) as PDF; show they carry the Demo Edition's
   generic branding and seal, not the original client's.
8. **Stocktaking** — as `demo.inspector`, perform a stocktaking count
   (`stock_stocktaking_eg`, Form 6) and show the surplus/deficit report.
9. **Dashboard** — as `demo.admin`, open the executive dashboard
   (`demo_gov_dashboard`) and show the KPIs now reflect the scenarios above.
10. **Permission boundary** — log in as `demo.inspector` and attempt a
    warehouse-manager-only action to show it's refused — demonstrates the
    role matrix (`ROLE_MATRIX.md`) is enforced, not decorative.

## 3. Presenting to an audience

Use `DEMO_SCRIPT.md` for the shorter, presentation-paced version of this
sequence (screen / action / business value / expected result), once the
golden database above exists.

## Notes for the presenter

- Reset to the golden snapshot before each session if visitors are
  allowed to interact and change data.
- The ETA e-invoicing and Credit Bureau screens are safe to show — both
  are demo-mode-gated (`INTEGRATIONS.md`); the ETA screen will show a
  clear "simulated in Demo Edition" message rather than a real
  submission, which is itself worth narrating ("this integration is
  intentionally disabled in the demo environment for safety").
