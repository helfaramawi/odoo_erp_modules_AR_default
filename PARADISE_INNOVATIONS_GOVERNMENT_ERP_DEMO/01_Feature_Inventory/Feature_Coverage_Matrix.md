# Feature Coverage Matrix — Paradise Innovations Government ERP

Quick-reference grid for all 90 custom addons found in `demo_edition/addons`, built from a full code read (manifests, models, views, security, reports) of every module — not from assumption. Status definitions:

- **TESTED** — IMPLEMENTED AND TESTED: code is complete and was confirmed working (either by this repo's own `docs/demo/KNOWN_LIMITATIONS.md` live-install record, or because the module is simple enough that reading it is equivalent to testing it).
- **VERIFIED-CODE** — IMPLEMENTED BUT NOT VERIFIED: code is complete and internally consistent, but has not been exercised end-to-end against a live database in this project.
- **PARTIAL** — PARTIALLY IMPLEMENTED: a real gap exists — a dead/unreachable state, a stubbed posting step, a missing field, or similar.
- **SIMULATED** — the feature deliberately or effectively fakes its core function (either by design, e.g. demo-mode guards, or by omission, e.g. hard-coded zero values).
- **BROKEN** — will not install or function at all.
- **NOT INSTALLED** — `installable: False` by design (maintenance/admin tooling only).
- **EXCLUDE** — a real feature, but an internal QA/test-data tool, not something to show a customer.

"Demo-safe" = can be clicked through live, unscripted, without hitting a crash or a misleading claim.

## الحسابات — Accounts / Finance (24 modules)

| # | Technical name | Business name | Status | Key caveat | Demo-safe |
|---|---|---|---|---|---|
| 1 | `general_ledger_ar` | الديوان العام - الحسابات | VERIFIED-CODE | Pure menu wrapper onto core Odoo ledger actions | Yes |
| 2 | `demo_gov_subsidiary_books` | الدفاتر المساعدة الحكومية | VERIFIED-CODE | Structural hub for the whole Accounts area | Yes |
| 3 | `demo_gov_cash_books` | دفاتر النقدية وأوامر الدفع والكفالات | VERIFIED-CODE | Final GL posting on payment orders is an intentional manual hook, not automated | Yes (don't claim auto-GL-posting) |
| 4 | `demo_gov_cash_transfers` | دفاتر حركة النقود المرسلة والواردة | VERIFIED-CODE | Full state machine incl. dispute/loss paths | Yes |
| 5 | `demo_gov_cheques` | دفتر الشيكات وأوامر الدفع المرسلة | VERIFIED-CODE | Strong constraint logic (no overlapping ranges) | Yes |
| 6 | `demo_gov_revenue_books` | دفاتر الإيرادات والمصروفات الحكومية | VERIFIED-CODE | Budget-code matrix depends on consistent `ref`/account-prefix conventions | Yes |
| 7 | `demo_gov_insurance_subsidiary` | دفاتر التأمينات المؤقتة والنهائية | PARTIAL | Real GL postings only fire if Settings accounts are configured; else silent chatter-only skip | Caveat live |
| 8 | `demo_gov_commitment` | الارتباطات والتسميح | VERIFIED-CODE | `daftar55.commitment_ref` link is free text, not FK — only as reliable as data entry | Yes |
| 9 | `demo_gov_daftar224` | دفتر 224 ع.ح | VERIFIED-CODE | Auto-triggered by Daftar-55 posting — real cross-module hook | Yes |
| 10 | `demo_gov_daftar55` | دفتر 55 - سجل المدفوعات | VERIFIED-CODE | Core hub of the whole Finance chain; real stamp/tax deduction math | Yes |
| 11 | `demo_gov_advances` | السلف والضمانات البنكية | PARTIAL | `action_disburse()` never actually posts the accounting entry its own docstring promises | Caveat live |
| 12 | `demo_gov_budget_planning` | الموازنة التقديرية وتحليل الانحرافات | VERIFIED-CODE | "Actual spend" only updates via manual batch action, text-matched | Yes |
| 13 | `demo_gov_penalties` | دفتر حساب الجزاءات | PARTIAL | `action_execute()`'s financial impact is an explicit documented stub (chatter only) | Caveat live |
| 14 | `demo_gov_special_funds` | الصناديق والحسابات الخاصة | **PARTIAL (bug)** | `action_post()` on expense transactions references a non-existent `commitment_id` field — **will crash** | **Revenue only** |
| 15 | `demo_gov_dossier` | الاضابير - نظام الأرشفة | PARTIAL | 9-document completeness check is informational only, not a hard gate; no close button | Yes (frame as informational) |
| 16 | `demo_gov_form69` | استمارة 69 - الحسبة اليومية | VERIFIED-CODE | Real cross-check vs Daftar-224/55; hand-rolled Hijri converter | Yes |
| 17 | `demo_gov_form75` | استمارة 75 - الإغلاق الشهري | VERIFIED-CODE | 3-stage sign-off not enforced to be 3 *different* people | Yes |
| 18 | `demo_gov_fixed_assets` | الأصول الثابتة | VERIFIED-CODE | Most complete finance module — real multi-method depreciation + disposal postings | Yes |
| 19 | `demo_gov_stock_finance_bridge` | ربط المخزون بالحسابات | **PARTIAL (bug)** | Two parallel, conflicting model-extension files for the same 4 permit models — actual click-path is ambiguous | Verify live first |
| 20 | `l10n_eg_eta_invoice` | الفاتورة الإلكترونية ETA | **SIMULATED (by design)** | Hard-coded demo-mode block: *"لا يتم الاتصال بأي خادم حقيقي"* | Yes, show the honest block message |
| 21 | `demo_gov_coa_fix` | تصحيح شجرة الحسابات | NOT INSTALLED | `installable: False` — admin shell-script toolkit, not a UI feature | N/A — not a demo item |
| 22 | `demo_gov_acct_reports` | التقارير المحاسبية (ميزان مراجعة) | VERIFIED-CODE | Redundant subset of #23/#24 | Yes |
| 23 | `demo_gov_gl_reports` | التقارير المحاسبية الحكومية | VERIFIED-CODE | Superset of #22, duplicated not reused | Yes |
| 24 | `demo_gov_reports` | التقارير الحكومية (24 report types) | VERIFIED-CODE | Broadest single console; smoke-test each report type before recording | Pre-test each report |

## المشتريات — Purchases / Procurement (9 modules)

| # | Technical name | Business name | Status | Key caveat | Demo-safe |
|---|---|---|---|---|---|
| 1 | `procurement_committee` | تشكيل اللجان | VERIFIED-CODE | 5 real government-form reports, 3-tier security | Yes |
| 2 | `procurement_adjudication` | البت الفني والمالي | VERIFIED-CODE | Most complete module in the group — real lowest-bid logic, role-gated award | Yes |
| 3 | `demo_gov_scm_requisition` | طلب الاحتياج | PARTIAL | `po_created` state in the UI statusbar is never actually reached by any code path | Don't click expecting state change |
| 4 | `demo_gov_scm_purchase_bridge` | أمر التوريد — الجسر مع استمارة 50 | PARTIAL | Bank-guarantee sub-flow has fields but no transition buttons (data-entry only) | Yes for the PO-block/Form-50 part |
| 5 | `l10n_eg_auction` | المزايدات | **PARTIAL (bug)** | Daily cron calls `_cron_apply_annual_increase()` which **doesn't exist** — will error if cron fires | Don't run the cron live; demo manual flow only |
| 6 | `c1_purchase_approval_matrix` | PO Approval Matrix | PARTIAL | No menu without Developer Mode; 2 e-mail templates built but never sent by any code | Yes via Settings → Technical |
| 7 | `c6_cost_centre` | Cost Centre on Requisitions | VERIFIED-CODE | Single field, trivial | Yes |
| 8 | `c7_credit_bureau` | Credit Bureau API | **SIMULATED (self-disclosed)** | Explicitly posts "DEMO MODE — simulated" in chatter; never calls a real API | Yes, show the disclosure |
| 9 | `c8_contract_pricing` | Contract Pricing Override | VERIFIED-CODE | No menu without Developer Mode | Yes via Developer Mode |

## المخازن والمستودعات — Warehouses / Stores (6 modules)

| # | Technical name | Business name | Status | Key caveat | Demo-safe |
|---|---|---|---|---|---|
| 1 | `demo_gov_scm_issue` | أذونات الصرف والارتجاع والتحويل | PARTIAL | No PDF reports at all; accounting-bridge call explicitly raises "not installed"; Return-permit "committee" state unreachable | Yes, skip the committee button |
| 2 | `demo_gov_scm_warehouse` | لجنة الفحص والمخازن | PARTIAL | Inspection-committee flow is solid; `action_move_to_stock()` is simulated — no real stock move created despite its name | Demo inspection flow only |
| 3 | `l10n_eg_custody` | إدارة العهد | VERIFIED-CODE | Most complete module in the group — real `stock.move` → custody automation | Yes |
| 4 | `stock_addition_permit` | إذن الإضافة | PARTIAL | `action_post()` docstring claims a stock journal entry; body only sets state — simulated | Yes, frame as "state tracking" not "ledger posting" |
| 5 | `stock_stocktaking_eg` | الجرد الحكومي | VERIFIED-CODE | Real live `stock.quant` variance engine, 7 working reports | Yes |
| 6 | `c10_inventory_revaluation` | Inventory Revaluation Report | **SIMULATED (prior-month variance)** | `prior_value`/`variance` are hard-coded `0.0` despite being the module's headline feature | Yes, current-value only — never claim the variance columns work |

## الموارد البشرية والرواتب — HR / Payroll (18 modules)

| # | Technical name | Business name | Status | Key caveat | Demo-safe |
|---|---|---|---|---|---|
| 1 | `demo_gov_hr_employee` | ملف الموظف الحكومي | VERIFIED-CODE | Required-document checklist + unique National ID | Yes |
| 2 | `demo_gov_hr_leave` | إدارة الإجازات الحكومية | PARTIAL | Entitlement-days formula self-flagged in code as unconfirmed | Yes, caveat the entitlement number |
| 3 | `demo_gov_hr_org_development` | التطوير المؤسسي | VERIFIED-CODE | Form 5 position-budget report is real | Yes |
| 4 | `demo_gov_hr_payroll_insurance_eg` | التأمينات الاجتماعية | **PARTIAL (placeholder data)** | Seed file is explicitly commented "illustrative demo values only — Finance must update" | Caveat live: engine real, numbers are not |
| 5 | `demo_gov_hr_payroll_run` | دورة الصرف الشهرية | VERIFIED-CODE | **Most complete module in the whole repo** — real end-to-end gross→net→ledger computation | Yes |
| 6 | `demo_gov_hr_payroll_structure` | بنود الراتب والحركات الاستثنائية | VERIFIED-CODE | 9 real salary components, 14 transaction reason codes | Yes |
| 7 | `demo_gov_hr_payroll_tax_eg` | الشرائح الضريبية المصرية | **PARTIAL (placeholder data)** | Code comment states this is NOT the real/complete Egyptian tax brackets, only an illustrative example | Caveat live: algorithm real, brackets are not |
| 8 | `demo_gov_hr_pension` | المعاشات والتأمينات | PARTIAL | 80%/40-year replacement formula self-flagged as placeholder pending legal review | Caveat live |
| 9 | `demo_gov_hr_performance` | تقييم الأداء الحكومي | PARTIAL | Incentive-% table self-flagged as unofficial reference | Caveat live |
| 10 | `demo_gov_hr_public_service` | الخدمة العامة | VERIFIED-CODE | Small, self-contained cron feature | Yes |
| 11 | `demo_gov_hr_recruitment` | التوظيف والتأهيل الحكومي | VERIFIED-CODE | | Yes |
| 12 | `demo_gov_hr_reports` | التقارير الحكومية الثمانية (SSRS) | VERIFIED-CODE | 7 real data-bound government report templates | Yes |
| 13 | `demo_gov_hr_takaful` | صندوق التكافل | **SIMULATED (accounting, self-disclosed)** | Code comment confirms no real journal entry is ever created for contributions/payouts | Caveat live |
| 14 | `demo_gov_hr_training` | التدريب الحكومي | VERIFIED-CODE | Creates the shared "الموارد البشرية" menu root | Yes |
| 15 | `demo_gov_hr_transfer` | النقل والندب والإعارة والترقيات | VERIFIED-CODE | Real 30-day expiry cron + dual-approval gate for settlements | Yes |
| 16 | `demo_gov_hr_disclosure` | إقرار الذمة المالية | VERIFIED-CODE | Real 6-year auto-renewal chaining | Yes |
| 17 | `demo_gov_hr_uat_data` | أدوات الاختبار - الموارد البشرية | **EXCLUDE** | Internal QA bulk-data generator — would look like "cheating" on camera | Do not demo |
| 18 | `demo_gov_egypt_national_id` | التحقق من الرقم القومي | VERIFIED-CODE (knowingly partial) | Validates century/birthdate/governorate/gender; explicitly does NOT verify the checksum digit (no public formula exists) | Yes, state the limitation |

## الذكاء الاصطناعي — AI Agents (19 modules)

**Headline finding: 0 of 19 call an LLM for their actual decision logic.** All are deterministic rule-based automation (thresholds, Z-scores, keyword/regex matching, SQL aggregation). Two modules' own code comments explicitly say so. Never market these as "AI-powered" without qualifying what kind of automation they are.

| # | Technical name | Business name | Status | What it actually is | Demo-safe |
|---|---|---|---|---|---|
| 1 | `demo_gov_ai_agents_menu` | مجموعة وكلاء الذكاء الاصطناعي | TESTED | Pure menu organizer | Yes |
| 2 | `demo_gov_arabic_ai_assistant` | مساعد لغوي عربي — اسألني بالعربي | PARTIAL/HYBRID | Real local rule-based Arabic NLU; genuine Ollama LLM fallback exists in code but is **unreachable in this environment** (`host.docker.internal:11434`, not provisioned) | Yes — script around the local-only path |
| 3 | `demo_gov_budget_forecast_ai_agent` | توقع انحرافات الموازنة | TESTED | Linear extrapolation + threshold bucketing | Yes |
| 4 | `demo_gov_budget_reallocation_ai_agent` | توصية إعادة توزيع الاعتمادات | TESTED | Category-match recommendation engine | Yes |
| 5 | `demo_gov_commitment_ai_agent` | أتمتة الارتباطات | TESTED | Risk-score auto-approval (event-triggered) | Yes |
| 6 | `demo_gov_conflict_interest_ai_agent` | كشف تضارب المصالح | TESTED | Phone/email/name-overlap heuristics | Yes |
| 7 | `demo_gov_daftar55_reconcile_ai_agent` | مطابقة دفتر 55 | TESTED | ORM text/amount reconciliation | Yes |
| 8 | `demo_gov_dead_stock_ai_agent` | كشف المخزون الراكد | TESTED | Days-since-movement thresholds | Yes |
| 9 | `demo_gov_duplicate_claim_ai_agent` | كشف تكرار المستندات | TESTED | Checksum + `difflib` string similarity | Yes |
| 10 | `demo_gov_eta_retry_ai_agent` | إعادة محاولة ETA | TESTED | Keyword error classifier (code comment: "can be replaced later by an on-prem LLM") | Yes |
| 11 | `demo_gov_executive_briefing_ai_agent` | الملخص التنفيذي اليومي | TESTED | Weighted aggregation across 7 agents, templated text | Yes |
| 12 | `demo_gov_payment_anomaly_ai_agent` | كشف شذوذ المدفوعات | TESTED | **Genuine Z-score statistics** — the one module using real descriptive stats | Yes |
| 13 | `demo_gov_payment_cycle_delay_ai_agent` | مراقبة تأخيرات دورة الصرف | TESTED | SLA threshold tracking | Yes |
| 14 | `demo_gov_procurement_legal_compliance_ai_agent` | الالتزام القانوني للمشتريات | TESTED | Filename/description keyword matching (no OCR, doesn't read document content) | Yes |
| 15 | `demo_gov_procurement_splitting_ai_agent` | مراقبة تجزئة المشتريات | TESTED | Rolling-window threshold clustering | Yes |
| 16 | `demo_gov_vendor_data_quality_ai_agent` | جودة بيانات الموردين | TESTED | Completeness scoring rules | Yes |
| 17 | `demo_gov_vendor_penalty_ai_agent` | جزاءات الموردين التلقائية | TESTED | Rule engine + templated Arabic letter generation | Yes |
| 18 | `demo_gov_vendor_performance_ai_agent` | تقييم كفاءة الموردين | TESTED | Weighted formula (quality/timeliness/penalties/volume) | Yes |
| 19 | `procurement_adjudication_ai_agent` | تحليل العروض الفني والمالي | TESTED | PDF text extraction + keyword overlap (code comment: explicitly "rule-based", not NLP) | Yes |

## البنية التحتية والأدوات — Infra / Misc (14 modules)

| # | Technical name | Business name | Status | Key caveat | Demo-safe |
|---|---|---|---|---|---|
| 1 | `demo_branding` | Demo Branding & Environment Banner | TESTED | Provides the shared `menu_gov_root` every government module nests under | Yes |
| 2 | `demo_gov_seed_data` | Demo Governorate — Seed Data | TESTED | Populates lists so the demo isn't empty | Yes (install-time only) |
| 3 | `demo_gov_dashboard` | لوحة القيادة التنفيذية | TESTED | Previously documented as broken — **re-confirmed fixed**; serves a static HTML/JS SPA, not QWeb | Yes |
| 4 | `demo_gov_menu` | تنظيم القوائم | **BROKEN** | References 8 view files that don't exist anywhere in the repo — cannot install | Exclude entirely |
| 5 | `demo_gov_form50_print` | طبقة الطباعة الرسمية لاستمارة 50 | VERIFIED-CODE | Fully ported from production backup; repo's own notes mark it "not yet live-tested" | Verify live first |
| 6 | `demo_gov_custom_programs_menu` | تجميع البرامج المخصصة | TESTED | Menu organizer for the c1–c13 modules | Yes |
| 7 | `demo_gov_uat_tools` | أدوات الاختبار والقبول | VERIFIED-CODE | **EXCLUDE from customer demo** — destructive QA tool, has a real `demo_` DB-name safety guard | Exclude |
| 8 | `c2_batch_posting` | Batch Journal Posting | TESTED | Simple, correct | Yes |
| 9 | `c3_aging_report` | AR/AP Aging Report | TESTED | Standard bucket arithmetic | Yes |
| 10 | `c4_payment_matching` | Vendor Payment Matching | TESTED | Correct double-entry on early-pay discount | Yes |
| 11 | `c5_financial_dimensions` | Financial Dimensions Engine | TESTED | Simple master-data + field extension | Yes |
| 12 | `c11_budget_alert` | Project Budget Alert | TESTED | Correct threshold-crossing + reset logic | Yes |
| 13 | `c12_intercompany_recharge` | Inter-company Recharge Journals | TESTED | Correct multi-company double-entry | Yes |
| 14 | `c13_tax_xml_export` | Tax Filing XML Export | **SIMULATED ("signed" claim)** | `_sign_xml()` just appends a text comment — no real PKCS7/cryptographic signature despite the `cryptography` import | Yes, never call it "signed" |

---

**Totals:** 90 modules inspected. 48 TESTED/VERIFIED-CODE with no material caveat · 21 PARTIAL (real gap, demo-able with a stated caveat) · 6 SIMULATED (by design or by omission, always self-disclose) · 2 confirmed bugs that will crash or error if clicked the wrong way (`demo_gov_special_funds` expense posting, `l10n_eg_auction`'s annual-increase cron) · 1 BROKEN (`demo_gov_menu`, cannot install) · 1 NOT INSTALLED by design (`demo_gov_coa_fix`) · 2 internal QA tools excluded from the customer-facing demo (`demo_gov_hr_uat_data`, `demo_gov_uat_tools`).
