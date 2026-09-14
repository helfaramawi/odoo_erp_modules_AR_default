# Demo Data

## Shipped automatically (module install)

Installing `demo_gov_seed_data` loads:

**7 user accounts** (`l10n_eg_custody/data/demo_users.xml`, `noupdate="1"`):

| Login | Role (Arabic name shown in UI) | Key group |
|---|---|---|
| `demo.admin` | مدير عام - حساب تجريبي (Director General) | system admin, all managers |
| `demo.contracts_manager` | مدير التعاقدات (Contracts Manager) | contract manager, adjudication director, auction manager |
| `demo.contracts_officer` | موظف التعاقدات (Contracts Officer) | contract user, adjudication member |
| `demo.adjudication_chairman` | رئيس لجنة البت (Adjudication Chairman) | adjudication chairman |
| `demo.warehouse_manager` | مدير المخازن (Warehouse Manager) | custody manager, warehouse manager |
| `demo.storekeeper` | أمين المخزن (Storekeeper) | custody user, storekeeper |
| `demo.inspector` | مفتش المخزن (Inspector) | inspector |

Password: `DEMO_USERS_PASSWORD` env var if set at install time, otherwise
the shipped default `Demo@2024` (demo-only, documented, not meant for a
public-internet deployment without changing it — see `SECURITY_REVIEW.md`).

**7 HR employee records**, `EMP-0001`–`EMP-0007`, one per user above, each
named `EMP-000N — <Role> (Demo)`.

**4 vendors**: Supplier One, Supplier Two, National Demo Supplies,
Technology Demo Services (all `@*.example` email domains).

**3 customers/beneficiaries**: Customer A, Customer B, Service Beneficiary 001.

**6 inventory items**: Office Laptop (`DEMO-ITEM-001`), Printer, Office
Chair, Paper A4, Network Switch, Storage Cabinet — with list/standard
prices so valuation and stock reports have real numbers to show.

None of the above represents a real person, company, or government
entity — verified per `BRANDING.md`'s search process.

## Not shipped: transactional scenario data

Purchase requisitions through invoices, an awarded auction, a posted
custody assignment, a closed Form 75 month-end — these were **not**
scripted as raw `<record>` XML, because the modules that own them
(`procurement_adjudication`, `l10n_eg_auction`, `l10n_eg_custody`,
`demo_gov_form75`, ...) enforce explicit workflow state machines in
Python (draft → committee → adjudicated → awarded → po_created, etc.).
Inserting rows directly in a state past `draft` risks creating data the
application's own logic would never produce, which would make the demo
less trustworthy, not more. It also cannot be verified without a live
Odoo instance, which was out of scope for this pass.

**Recommended approach** (documented, not automated): after
`scripts/demo-seed/demo-reset.sh`, walk each scenario once through the UI
using the seeded accounts and master data above — see `DEMO_GUIDE.md` for
the exact sequence per module. Leave the resulting records in the demo
database; that's what gives dashboards and reports non-empty, realistic
numbers for a live presentation. Because `demo-reset.sh` only touches
databases named `demo_*`, this "golden" demo database can be snapshotted
(`pg_dump`) and restored before each demo session instead of re-walking
the scenarios every time.

## End-to-end scenarios supported by this codebase

```
Procurement:  Requisition -> Committee formation -> RFQ/Adjudication
              (technical + financial envelopes) -> Award -> Purchase Order
              -> Goods Receipt (Addition Permit) -> Vendor Bill

Auction:      Auction request -> Committee -> Session/deposit -> Bids
              -> Path A (Sale: auto sale.order) or
                 Path B (Lease: contract + payment schedule)

Custody:      Custody assignment (Form 193) -> Durable item tracking
              -> Transfer between employees -> Stocktaking (Form 6)
              -> Surplus/Deficit report

Finance:      Budget (planning) -> Commitment -> Daftar 55/224 entries
              -> Form 69 daily reckoning -> Form 75 monthly/annual
              closing -> GL reports (trial balance, general ledger)
```

These match the modules' actual state machines (verified from their
Python source, not assumed) rather than the generic scenario shapes in
the original conversion brief.
