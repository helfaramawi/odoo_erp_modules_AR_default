# Feature Inventory

One row per module (its primary feature), verified against each module's
`__manifest__.py`, directory contents, and dependency graph — not against
a running instance (see `DEMO_CONVERSION_PLAN.md`). "Status" reflects
static findings only (files present, syntax valid, dependencies resolve);
it is not a claim that the feature was exercised end to end.

Names below are the **Demo Edition** (anonymized) module names; see
`BRANDING.md` for the mapping back to original technical names.

## General Ledger & Core Accounting

| Module | Feature | Backend | Role | Demo Required | Status | Demo Data Required | External Dependency |
|---|---|---|---|---|---|---|---|
| `general_ledger_ar` | Unified "General Diwan > Accounts" menu root | menu only | All finance roles | Yes | Working | No | No |
| `demo_gov_daftar55` | Daftar 55 sequential payment register | `demo_gov.daftar55` | Accountant/Manager | Yes | Working | Yes | No |
| `demo_gov_daftar224` | Daftar 224 dual daily register (expenditures + adjustments) | `demo_gov.daftar` | Accountant | Yes | Working | Yes | No |
| `demo_gov_form69` | Form 69 daily reckoning | depends on daftar224 | Accountant | Yes | Working | Yes | No |
| `demo_gov_form75` | Form 75 monthly/annual closing, 3-stage sequential | depends on form69 | Manager | Yes | Working | Yes | No |
| `demo_gov_commitment` | Budget commitment & clearance (ارتباط → تجنيب → تسميح) | `demo_gov.commitment` | Budget officer | Yes | Working | Yes | No |
| `demo_gov_subsidiary_books` | Subsidiary books engine, Forms 29/39/71 | shared engine | Accountant | Yes | Working | Yes | No |
| `demo_gov_budget_planning` | Estimated budget + execution + variance analysis | links to `c5_financial_dimensions` | Budget officer/Manager | Yes | Working | Yes | No |
| `demo_gov_acct_reports` / `demo_gov_gl_reports` / `demo_gov_reports` | Trial balance, partner ledger, general ledger, ~20 government-format reports (QWeb PDF) | report actions | Accountant/Auditor | Yes | Working | Yes | No |
| `demo_gov_special_funds` | Ring-fenced special funds accounting | `demo_gov.special_fund` | Accountant | Optional | Working | No | No |

## Cash, Cheques & Advances

| Module | Feature | Backend | Role | Demo Required | Status | Demo Data Required | External Dependency |
|---|---|---|---|---|---|---|---|
| `demo_gov_cash_books` | Cash, central bank, payment orders, CAU, sureties | `demo_gov.cash*` | Cashier | Yes | Working | Yes | No |
| `demo_gov_cheques` | Cheques register (Form 56) + outgoing payment orders | `demo_gov.cheque` | Cashier | Optional | Working | No | No |
| `demo_gov_cash_transfers` | Outgoing/incoming cash transfers (Form 39) | `demo_gov.cash_transfer` | Cashier | Optional | Working | No | No |
| `demo_gov_advances` | Permanent advances (Form 62), down payments, bank guarantees | `demo_gov.advance` | Finance officer | Yes | Working | Yes | No |
| `demo_gov_insurance_subsidiary` | Temporary/final insurance/guarantee subsidiary books (Form 78) | `demo_gov.insurance_deposit` | Finance officer | Optional | Working | No | No |
| `demo_gov_penalties` | Penalties book (Form 39) | `demo_gov.penalty` | HR/Finance | Optional | Working | No | No |
| `demo_gov_revenue_books` | Revenue & expense books (Form 10, Form 81) | `demo_gov.revenue` | Accountant | Optional | Working | No | No |

## Fixed Assets

| Module | Feature | Backend | Role | Demo Required | Status | Demo Data Required | External Dependency |
|---|---|---|---|---|---|---|---|
| `demo_gov_fixed_assets` | Fixed asset register, depreciation (EAS #10), disposal, asset cards | `demo_gov.asset*` | Asset manager | Yes | Working | Yes | No |
| `demo_gov_form50_print` | Print-layer extension for Form 50 (no accounting logic) | extends daftar55 | — | No | **Broken — not installable, ships no `__manifest__.py`** | No | No |

## Procurement, Committees & Tenders (Egypt Gov. Law 182/2018)

| Module | Feature | Backend | Role | Demo Required | Status | Demo Data Required | External Dependency |
|---|---|---|---|---|---|---|---|
| `procurement_committee` | Committee formation mixin (RFQ/PO/Auction), roles: chairman/member/secretary | mixin | Contracts manager | Yes | Working | Yes | No |
| `procurement_adjudication` | Dual-envelope technical/financial adjudication, state machine draft→awarded | `adjudication.*` | Adjudication chairman | Yes | Working | Yes | No |
| `l10n_eg_auction` | Government auctions (sale or lease/usufruct), bid recording, award | `auction.*` | Auction manager | Yes | Working | Yes | No |
| `demo_gov_scm_requisition` | Purchase requisition with auto budget commitment | `requisition.*` | Requisitioner | Yes | Working | Yes | No |
| `demo_gov_scm_purchase_bridge` | PO bridge — auto-generates Form 50 from Daftar 55 | bridges to daftar55 | Procurement officer | Yes | Working | Yes | No |
| `demo_gov_scm_warehouse` | Inspection committee + warehouse forms (Form 12) | `demo_gov.warehouse*` | Inspector | Optional | Working | No | No |

## Inventory & Custody (Egypt Gov. Warehouse Regulations / GAFI)

| Module | Feature | Backend | Role | Demo Required | Status | Demo Data Required | External Dependency |
|---|---|---|---|---|---|---|---|
| `l10n_eg_custody` | Custody assignment (Form 193), durable item tracking, transfers | `custody.*` | Warehouse manager | Yes | Working | Yes (ships `demo_users.xml`) | No |
| `stock_addition_permit` | Two-step goods receipt: inspection + إذن إضافة (Form 1) | `addition.permit` | Storekeeper | Yes | Working | Yes | No |
| `stock_stocktaking_eg` | Government stocktaking (Form 6), surplus/deficit, write-off (Form 4) | `stocktaking.*` | Inspector | Yes | Working | Yes | No |
| `demo_gov_scm_issue` | Issue/return/transfer permits between warehouses | `demo_gov.outgoing_po` etc. | Storekeeper | Optional | Working | No | No |
| `demo_gov_stock_finance_bridge` | Auto GL entries + financial dimensions per stock move | bridges to `c5_financial_dimensions` | — (system) | Optional | Working | No | No |

## Compliance & Filing

| Module | Feature | Backend | Role | Demo Required | Status | Demo Data Required | External Dependency |
|---|---|---|---|---|---|---|---|
| `l10n_eg_eta_invoice` | Egyptian Tax Authority e-invoice submission/validation/cancel | `eta.config`, `eta.invoice` | Finance manager | Optional (simulated) | Working, **live calls disabled in demo** | No | **Yes — real gov API, blocked in demo** (see `INTEGRATIONS.md`) |
| `c13_tax_xml_export` | Signed tax filing XML export for government portal | — | Finance manager | Optional | Working | No | No (offline file export) |

## Executive Dashboard & Menu

| Module | Feature | Backend | Role | Demo Required | Status | Demo Data Required | External Dependency |
|---|---|---|---|---|---|---|---|
| `demo_gov_menu` | Unified single-tab menu structure tying all modules together | menu/views only | All | Yes | Working | No | No |
| `demo_gov_dashboard` | Executive KPI dashboard (real-time) | controller + OWL | Director general | Yes | **Partial — one pre-existing XML well-formedness defect** (see `KNOWN_LIMITATIONS.md`) | Yes | No |

## Generic Financial Add-ons (c1–c13)

| Module | Feature | Role | Demo Required | Status |
|---|---|---|---|---|
| `c1_purchase_approval_matrix` | PO approval matrix | Manager | Optional | Working |
| `c2_batch_posting` | Scheduled nightly batch posting of draft journal entries | Accountant | Optional | Working |
| `c3_aging_report` | AR/AP aging report, configurable buckets | Accountant | Optional | Working |
| `c4_payment_matching` | Manual vendor payment matching + early-pay discount journals | Accountant | Optional | Working |
| `c5_financial_dimensions` | Department/Project/Region dimensions engine on journal entries | — (infra) | Optional | Working |
| `c6_cost_centre` | Cost centre on requisitions | Requisitioner | Optional | Working |
| `c7_credit_bureau` | Credit check on sale orders (Green/Amber/Red) | Sales | Optional (simulated) | Working, **live calls simulated in demo** | **Yes — external API, mocked in demo** |
| `c8_contract_pricing` | Contract-based price override with date ranges | Sales | Optional | Working |
| `c10_inventory_revaluation` | Inventory revaluation report with prior-month variance | Accountant | Optional | Working |
| `c11_budget_alert` | Nightly budget threshold alerts for projects | Project manager | Optional | Working |
| `c12_intercompany_recharge` | Automated inter-company recharge journals | Accountant | Optional | Working |

## Totals

```
Total modules inspected:      37 (36 installable + 1 orphaned/broken)
Fully working (static check): 35
Partial:                       1  (demo_gov_dashboard — pre-existing XML defect)
Broken / not installable:      1  (demo_gov_form50_print — no manifest)
```
"Working" here means: manifest parses, all Python/XML files in the module
parse without error, and all declared dependencies resolve. It is **not**
a claim that the module was installed and exercised in a running Odoo —
see `DEMO_CONVERSION_PLAN.md`.
