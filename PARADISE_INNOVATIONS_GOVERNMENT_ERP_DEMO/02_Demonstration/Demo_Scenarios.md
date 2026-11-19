# Demo Scenarios — Consolidated End-to-End Flows

Five real, code-verified cross-module chains, used as the backbone for both video scripts. Each step names the exact module, the exact button/menu label, and flags any caveat to state on camera. See `01_Feature_Inventory/Complete_Custom_Addons_Inventory.md` for full per-module detail.

## Flow A — Budget-to-Payment Cycle (الحسابات)
The strongest Finance storyline — touches real, automatic cross-module hooks, not just shared menus.

1. **`demo_gov_budget_planning`** — define the annual budget line and approved ceiling.
2. **`demo_gov_commitment`** — raise a commitment (ارتباط), تقديم → اعتماد → تجنيب → تسميح (the budget-control gate).
3. **`demo_gov_daftar55`** — create the payment register entry, type the commitment number into `رقم الارتباط`; show the automatic stamp-duty/tax deduction breakdown and Arabic amount-in-words; ترحيل.
4. **`demo_gov_daftar224`** — show the dual journal entry (gross + itemised deductions) that was **automatically** created by step 3's posting — call this out explicitly: "شاهدوا هذا يحدث تلقائيًا، بدون أي زر" (watch this happen automatically, no button needed) — it's the one fully-wired cross-module automation in the whole Accounts group.
5. **`demo_gov_dossier`** — "حفظ بالاضابير" on the posted Daftar-55 to auto-create its archive dossier, attach supporting documents, show the missing-documents tracker (state: informational in this build, not a blocking gate).
6. **`demo_gov_cheques`** / **`demo_gov_cash_books`** — issue the cheque or payment order that disburses the funds.
7. **`demo_gov_subsidiary_books`** / **`general_ledger_ar`** — show the same transaction live in the subsidiary ledger and general ledger; close a monthly folio.
8. **`demo_gov_reports`** — finish on the master report console: trial balance + commitment-status report.

Capital-purchase variant: splice in **`demo_gov_fixed_assets`** (acquire against the same payment, activate, post depreciation) and **`l10n_eg_eta_invoice`** (show the honest "disabled in demo environment" block message — do not call it a bug, it's by design).

**Avoid live and unrehearsed:** `demo_gov_special_funds` expense postings (confirmed crash — missing field) and the `demo_gov_stock_finance_bridge` issue-permit journal-entry button (two conflicting implementations — verify which one is actually active first).

## Flow B — Procurement Chain (المشتريات)
The best single demo flow in the whole repo for "modules genuinely talking to each other."

1. **`demo_gov_scm_requisition`** — a department raises a need (طلب احتياج), تقديم → "✅ موافقة + إنشاء ارتباط" — watch the budget commitment get created automatically in the chatter.
2. **`procurement_committee`** — form the Technical, Financial and Opening committees, add members (one chairman each), activate.
3. **`procurement_adjudication`** — attach those three committees to the tender, "📂 فتح المظاريف الفنية" (mark suppliers pass/fail), "💰 فتح المظاريف المالية" (enter bids), "⚖ مقارنة العروض والترسية" (watch the system auto-select the lowest valid bid), as a director: "🏆 إخطار الترسية", "📋 إنشاء أمر التوريد".
4. **`demo_gov_scm_purchase_bridge`** — try to confirm the PO before the commitment is approved (blocked with an Arabic error), then confirm it once approved and show the auto-spawned "استمارات 50" Form-50 draft.
5. Optional governance layer: **`c1_purchase_approval_matrix`** (monetary-tier approval) and **`c6_cost_centre`** (spend tagging) — both reachable only via Developer Mode, mention this plainly.

**Separate scenario, not stitched into the above:** **`l10n_eg_auction`** — government disposal/lease. Create a sale-type auction, تأكيد → فتح الجلسة → بدء تسجيل العروض, add bids, قبول the highest, الترسية (show the auto-created Sale Order). For contrast, a lease-type request to show the auto-generated multi-year payment schedule with annual increase. **Do not let the daily "annual increase" cron fire on camera** — it calls a method that doesn't exist and will error.

**Sales-side aside, flag as simulated:** **`c7_credit_bureau`** — click "Credit Check" and show the chatter explicitly disclosing "DEMO MODE — simulated."

## Flow C — Warehouse & Custody Chain (المخازن والمستودعات)

1. **`demo_gov_scm_warehouse`** or **`stock_addition_permit`** — goods arrive; an inspection committee records accepted/rejected quantities (Form 12), signs, finalizes and auto-files into the dossier. (Or the parallel path: Inspection Report → auto-created إذن إضافة Form 1 + استمارة 50.)
2. **`demo_gov_scm_issue`** — issue the received stock out to a department/employee under a formal "إذن الصرف", تقديم → اعتماد → ترحيل — تنفيذ الصرف; show the auto-created, undeletable "سجل الصرف" audit register.
3. **`l10n_eg_custody`** — if the issued item is durable (مستديم), run the 4-step "➕ عهدة جديدة" wizard with a valid 14-digit national ID; show the printed استمارة 193. Transfer it to a second employee via "تحويل عهدة" and show the custody's current holder change.
4. **`stock_stocktaking_eg`** — periodic physical count: "📦 تحميل المخزون الحالي" (loads live stock), adjust a couple of counts to create surplus/deficit, "✓ ترحيل الجرد" then "🔒 اعتماد الجرد", print "نموذج 6" and "كشف الزيادة والعجز".

**Honest caveats to state once, briefly, not as a blocker to the flow:** the addition-permit "posting" step and the warehouse-addition "move to stock" step are both state-only (no real stock ledger movement is created) — frame this as "status tracking" rather than "automatic stock posting."

**Separate quick aside:** **`c10_inventory_revaluation`** — current stock valuation table (never claim the "prior month variance" columns mean anything; they're hard-coded zero).

## Flow D — HR & Payroll Chain (الموارد البشرية والرواتب)

1. **`demo_gov_hr_recruitment`** — create a recruitment project, publish, link applicants, move through screening → interviewing → closed.
2. **`demo_gov_hr_employee`** — open the hired employee's file, fill the "بيانات حكومية" tab; show **`demo_gov_egypt_national_id`** reject an invalid governorate code, then accept a valid national ID.
3. **`demo_gov_hr_payroll_structure`** — assign salary components (BASIC/HOUS/TRANS...).
4. **`demo_gov_hr_payroll_insurance_eg`** + **`demo_gov_hr_payroll_tax_eg`** — show the bracket/component tables feeding the calculation — **state plainly these are illustrative example figures pending Finance sign-off, not official current rates.**
5. **`demo_gov_hr_payroll_run`** — run the monthly payroll: compute payslips, mark completed, submit → approve → ترحيل; open "دفتر 129 سايرة" to show the auto-created disbursement ledger entry; print Form 132 (single employee + bulk run totals).
6. Satellite modules, pick 2-3 for time: **`demo_gov_hr_leave`** (9 statutory leave types + leave-dept confirmation), **`demo_gov_hr_performance`** (appraisal → grievance), **`demo_gov_hr_transfer`** (secondment with 30-day expiry alert, promotion), **`demo_gov_hr_disclosure`** (6-year auto-renewing anti-corruption filing), **`demo_gov_hr_pension`** (retirement settlement → Form 15), **`demo_gov_hr_takaful`** (solidarity fund, caveat: no real accounting posting).
7. **`demo_gov_hr_reports`** — close on SSRS-08's color-coded disclosure-compliance table across several employees, a strong "at a glance" moment.

**Never demo live:** `demo_gov_hr_uat_data` — it's a bulk test-data generator, not a feature; seed data with it off-camera only.

## Flow E — Intelligent Automation Layer (الذكاء الاصطناعي)
Position this honestly as "rule-based intelligent automation," not generative AI, with one clear exception noted.

1. **`demo_gov_payment_anomaly_ai_agent`** — the one agent using genuine Z-score statistics. Create a cheque far outside a vendor's historical average, show the Z-score flag with the computed mean/stdev.
2. **`demo_gov_vendor_penalty_ai_agent`** — record an inspection with result "rejected" on a PO, show the auto-created penalty with a ready-to-send Arabic notification letter.
3. **`demo_gov_conflict_interest_ai_agent`** — seed a supplier and committee member sharing an email domain, show the "domain_match" alert.
4. **`demo_gov_executive_briefing_ai_agent`** — with a few alerts already seeded, "Generate Now" to produce one consolidated Arabic executive brief with a ranked action list.
5. **`demo_gov_arabic_ai_assistant`** — type "ما هو عدد الموردين؟" and get an instant answer tagged "Local" — **do not claim this is live LLM inference**; the Ollama fallback it contains in code is not reachable in this environment.

## Flow F — Reporting & Governance Close-out
**`demo_gov_reports`** (master 24-report console) → **`demo_gov_gl_reports`** (chart of accounts with live balances) → **`demo_gov_dashboard`** (executive KPI dashboard — drill into a tab). Mention the security model in passing: custom `res.groups` with multi-tier manager/user/chairman roles and `ir.rule` record-rule scoping appear consistently across almost every module (e.g. `l10n_eg_custody`'s storekeepers only seeing their own records).
