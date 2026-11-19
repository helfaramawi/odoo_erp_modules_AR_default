# Complete Custom Addons Inventory — Paradise Innovations Government ERP

Repo: `demo_edition/addons` inside `helfaramawi/odoo_erp_modules_AR_default`. Every module below was inventoried by reading its actual code — `__manifest__.py`, every file under `models/`, `views/`, `reports/`, `security/`, `wizard/`, `data/` — not by assumption. Field names, method/button names, and menu labels are copied verbatim from the source, in the language (Arabic or English) the developers used. See `Feature_Coverage_Matrix.md` for a one-page scan; this document is the full per-module detail behind it.

Methodology for the "Implementation status" field: a module is only called **IMPLEMENTED AND TESTED** when there is concrete evidence of a successful end-to-end run (either this repo's own `docs/demo/KNOWN_LIMITATIONS.md` live-install record, or the module is trivial enough that reading the code is equivalent to testing it). Everything else is graded **IMPLEMENTED BUT NOT VERIFIED**, **PARTIALLY IMPLEMENTED** (a concrete gap found), **SIMULATED** (the core function is deliberately or effectively faked), **BROKEN**, or **NOT INSTALLED**.

---

# PART 1 — الحسابات — Accounts / Finance (24 modules)

## 1. `general_ledger_ar`
1. **Technical name:** `general_ledger_ar`
2. **Business module:** "الديوان العام - الحسابات" (General Ledger / Accounts Hub)
3. **Purpose:** A thin menu-only wrapper that surfaces Odoo's native accounting views (general ledger, partner ledgers, journal entries) inside the government "Accounts" menu tree, so users don't have to go through the standard Odoo Accounting app menu.
4. **Key features:** No own models. `views/menu_views.xml` adds 4 menu items under `demo_gov_subsidiary_books.menu_subsidiary_root`: "دفتر الأستاذ العام" (→ `account.action_move_line_select`), "دفتر مديونيات العملاء" and "دفتر دائنية الموردين" (both → `account.action_account_moves_ledger_partner`), "قيود اليومية" (→ `account.action_move_journal_line`).
5. **Menu path:** الديوان العام → الحسابات → الدفاتر المساعدة → (the 4 items above).
6. **Workflow:** None — no model, no state field.
7. **Reports:** None.
8. **Access/roles:** No security files; relies entirely on core `account.*` access rights.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — trivial but functionally complete menu wiring onto stable core actions.
10. **Demo scenario:** From "الديوان العام" open "دفتر الأستاذ العام" and show the live general ledger; then "قيود اليومية" to show the same postings as journal entries.

## 2. `demo_gov_subsidiary_books`
1. **Technical name:** `demo_gov_subsidiary_books`
2. **Business module:** "الدفاتر المساعدة الحكومية — محرك موحد" (Unified Subsidiary Books Engine)
3. **Purpose:** A single generic engine that reproduces all 8 legally-mandated Egyptian government subsidiary ledgers (Forms 29/39/71) — detail & totals books for current and memorandum (off-balance) accounts, debit and credit sides — by filtering live `account.move.line` data rather than duplicating postings.
4. **Key features:**
   - `demo_gov.subsidiary.book` defines each of the 8 books (`account_class`: current/memo/personal, `side`: debit/credit/both, `scope`: detail/totals/personal, `grouping_key`: partner/account/partner_account), auto-creates a fiscal-year `ir.sequence.date_range` (FY starts 1 July) on creation.
   - `demo_gov.subsidiary.account.classification` bridges `account.account` (via `x_subsidiary_classification_id`) to books; `action_auto_assign_by_prefix()` bulk-assigns accounts by code prefix.
   - `demo_gov.subsidiary.folio` = one legal page/month; computes opening/period debit-credit/closing balances live from `account.move.line` (`_fetch_lines()`), chains to the previous folio for carry-forward, and freezes once closed.
   - Cron jobs `cron_recompute_open_folios` and `cron_generate_monthly_folios` (monthly auto-folio creation per book×partner/account).
   - `migrate_paper_wizard.py` and `print_wizard.py` wizards for migrating legacy paper numbering and printing.
5. **Menu path:** الديوان العام → الحسابات → الدفاتر المساعدة (`menu_subsidiary_root`) → الفوليوهات / تعريف الدفاتر / تصنيفات الحسابات. This is the structural hub of the whole Accounts area — `general_ledger_ar`, `demo_gov_cash_books`, `demo_gov_revenue_books`, `demo_gov_insurance_subsidiary`, `demo_gov_cash_transfers`, `demo_gov_penalties`, `demo_gov_budget_planning`, `demo_gov_stock_finance_bridge`, `demo_gov_gl_reports`, `l10n_eg_eta_invoice` all nest their menus under it.
6. **Workflow (Folio):** `draft (مفتوحة) → closed (مُقفَلة) → audited (مراجَعة) → archived (مؤرشفة)`, via `action_close()` (requires `crossout_signed_by`), `action_audit()` (requires `accounts_head_signed_by`), `action_reopen()` (manager-only). `action_recompute()` re-reads lines without changing state.
7. **Reports:** `report_subsidiary_detail_template.xml`, `report_subsidiary_totals_template.xml`, `report_personal_dual_template.xml`.
8. **Roles/access:** `group_subsidiary_user` / `group_subsidiary_manager` (implies `account.group_account_manager`).
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — full CRUD, state machine, crons, wizards, reports and access rules all present and internally consistent.
10. **Demo scenario:** Open "تعريف الدفاتر" to show the 8 pre-seeded book definitions; open "الفوليوهات", create a new folio for the current month, click "إعادة الحساب" to show it live-pulling posted entries, then "إقفال" after filling in the crossout-clerk signature.

## 3. `demo_gov_cash_books`
1. **Technical name:** `demo_gov_cash_books`
2. **Business module:** "دفاتر النقدية وأوامر الدفع والكفالات" (Cash/CBE/CAU books, Payment Orders, Sureties — Form 78 family)
3. **Purpose:** Legal registers for cash-on-hand, Central Bank of Egypt current account, Central Accounting Unit account, incoming payment orders, and employee sureties/custody guarantees.
4. **Key features:**
   - `demo_gov.cash.book` per journal type (cash/cbe/cau/other_bank), auto-creates its own FY sequence.
   - `demo_gov.payment_order` (incoming): legal sequencing, FY auto-stamping, cheque-method consistency check.
   - `demo_gov.surety`: cash/personal/mixed sureties on employees, constraint that cash sureties' deposit must equal the amount.
   - `demo_gov.cheque`: lightweight base cheque model (incoming/outgoing) later extended by `demo_gov_cheques`.
5. **Menu path:** الدفاتر المساعدة → دفاتر النقدية والبنك والكفالات → فوليوهات النقدية والبنك / أوامر الدفع الواردة / الشيكات / الكفالات / تعريف الدفاتر (manager-only).
6. **Workflow:**
   - Payment order: `draft → received → registered → cleared → posted / cancelled`.
   - Surety: `draft → active → suspended/active → released / forfeited (manager-only)`.
   - Cheque: `draft → issued → endorsed (incoming only) → deposited → cleared → returned / cancelled`.
7. **Reports:** `report_cash_register_template.xml`, `report_payment_order_template.xml`, `report_surety_template.xml`.
8. **Roles/access:** `group_cash_user` / `group_cash_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED.** `action_post()` on payment order explicitly leaves accounting-entry creation as "a hook for the finance team" (*"نترك إنشاء القيد للفريق المحاسبي"*) — the **final GL posting step is an intentional manual hook, not automated**.
10. **Demo scenario:** Create an incoming Payment Order from "وزارة المالية", walk استلام → قيد بالدفتر → تحصيل → ترحيل, then open "الكفالات" and activate a treasury-custodian's surety.

## 4. `demo_gov_cash_transfers`
1. **Technical name:** `demo_gov_cash_transfers`
2. **Business module:** "دفاتر حركة النقود المرسلة والواردة" (Outgoing/Incoming Physical Cash Transfers — Form 39)
3. **Purpose:** Tracks physical movement of cash between custodies (treasury ↔ branch/other governorate/CBE) — chain-of-custody for cash in transit, including dispute and loss/theft handling.
4. **Key features:**
   - `demo_gov.cash_transfer`: full custody chain (sender/transporter/receiver), denomination-breakdown text, dispute and loss sub-flows, write-protection once confirmed/closed/lost.
   - `demo_gov.cash_transfer.folio`: monthly folio per direction with cumulative carry-forward, blocks closing while unresolved disputes exist.
   - Cron `cron_generate_monthly` auto-creates last month's folios.
5. **Menu path:** الدفاتر المساعدة → دفاتر حركة النقود → التحويلات النقدية / الفوليوهات.
6. **Workflow:** `draft → prepared → in_transit → delivered → confirmed`, branches `delivered → disputed → confirmed (manager-only resolution)` and `in_transit/disputed → lost (manager-only, requires police report)`; pre-delivery → `cancelled`; terminal → `closed`.
7. **Reports:** `report_transfer_slip_template.xml`, `report_transfer_register_template.xml`.
8. **Roles/access:** `group_transfer_user` / `group_transfer_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — full state machine incl. exception paths.
10. **Demo scenario:** Create an outgoing transfer, walk إعداد → اعتماد الإرسال → تسليم → تأكيد; then raise a "تنازع" to show the manager-only resolution step, and a third marked "فقدان" with a police-report number.

## 5. `demo_gov_cheques`
1. **Technical name:** `demo_gov_cheques`
2. **Business module:** "دفتر الشيكات وأوامر الدفع المرسلة" (Cheques Register Form 56, Outgoing Payment Orders Form 56, Cheques-for-Collection Form 78)
3. **Purpose:** Full paper-chequebook auditability (number ranges, no-overlap/duplicate enforcement), outgoing payment orders, and bounced-cheque legal follow-up/recovery.
4. **Key features:**
   - `demo_gov.cheque.book`: physical chequebook number range, overlap/duplicate validation against other books on the same bank.
   - `demo_gov.cheque` extension: `form56_sequence` generated **only after** `action_issue()` succeeds (so a failed issue never burns a legal number), auto-opens a `bounced_followup` whenever `action_return()` fires.
   - `demo_gov.outgoing_po`: sequenced, linked to `daftar55_id`, amount-must-match constraint.
   - `demo_gov.cheque.bounced_followup`: legal recovery workflow.
5. **Menu path:** الدفاتر المساعدة → دفتر الشيكات وأوامر الدفع → أوامر الدفع المرسلة / دفاتر الشيكات الورقية / الشيكات المرتدة.
6. **Workflow:** Outgoing PO: `draft → registered → sent → cleared / rejected / cancelled`. Bounced followup: `open → negotiating → legal_action → recovered / written_off (manager-only)`. Chequebook: `received → in_use → completed → archived`, or `lost` any time.
7. **Reports:** `report_form56_cheques_template.xml`, `report_form56_outgoing_po_template.xml`, `report_form78_collection_template.xml`, `report_bounced_followup_template.xml`.
8. **Roles/access:** `group_cheques_user` / `group_cheques_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — thorough constraint logic, full lifecycle, reports and security all present.
10. **Demo scenario:** Receive a new chequebook (100001–100050), start its use, issue cheque #100001 against an outgoing payment order, mark it returned to show an auto-created `bounced_followup`, walk تفاوض → إحالة قانونية → استرداد.

## 6. `demo_gov_revenue_books`
1. **Technical name:** `demo_gov_revenue_books`
2. **Business module:** "دفاتر الإيرادات والمصروفات الحكومية" (Revenue & Expense Books — Form 10 and Form 81)
3. **Purpose:** Produces the revenue/expense cross-tab register (Form 10: day × budget-item matrix) and the resources/uses ledgers (Form 81) directly from posted journal entries.
4. **Key features:**
   - `demo_gov.revenue.book`: direction (revenues/expenses/both/settlements), grouping level, bab-range filter.
   - `demo_gov.revenue.folio`: builds a day×budget-code JSON matrix from `account.move.line`, resolving each line's budget code via analytic distribution → `demo_gov.budget.line`, else move `ref` prefix, else account-code prefix; same close/audit/reopen governance as subsidiary folios.
5. **Menu path:** الدفاتر المساعدة → دفاتر الإيرادات والمصروفات → الفوليوهات / تعريف الدفاتر / طباعة دفتر.
6. **Workflow (folio):** `draft → closed → audited → [reopen→draft, manager-only]`.
7. **Reports:** `report_form10_template.xml`, `report_form81_template.xml`.
8. **Roles/access:** `group_revenue_user` / `group_revenue_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — the budget-code extraction fallback chain is clever but entirely dependent on `ref` formatting conventions or account-code prefixes being correct.
10. **Demo scenario:** Open a monthly Form-10 folio, show the printed cross-tab matrix built live from the month's posted entries, contrasted with a Form-81 folio limited to Babs 1-6.

## 7. `demo_gov_insurance_subsidiary`
1. **Technical name:** `demo_gov_insurance_subsidiary`
2. **Business module:** "دفاتر التأمينات المؤقتة والنهائية" (Provisional & Final Insurance/Guarantee Books — Form 78)
3. **Purpose:** Covers the two legal books for contractor/vendor security deposits (provisional ~5% and final ~10%) per Tenders Law 182/2018, with automatic accounting entries on deposit/release/forfeiture.
4. **Key features:**
   - Extends `demo_gov_advances.bank.guarantee` with real `account.move` creation on activate/release/forfeit — **but only if** the company's `guarantee_memo_dr_account_id`/`guarantee_memo_cr_account_id` settings are filled in; otherwise it posts a chatter warning and skips the entry.
   - `demo_gov.insurance_deposit`: cash/cheque deposits, same lifecycle and posting logic.
   - `demo_gov.insurance.movement`: append-only ledger of every deposit/withdrawal/forfeiture event.
5. **Menu path:** الدفاتر المساعدة → دفاتر التأمينات → الفوليوهات / إيداعات التأمينات / حركات التأمينات (manager-only).
6. **Workflow:** `draft → active → released / forfeited (manager-only)`.
7. **Reports:** `report_insurance_folio_template.xml`, `report_insurance_receipt_template.xml`.
8. **Roles/access:** `group_insurance_user` / `group_insurance_manager`.
9. **Status: PARTIALLY IMPLEMENTED** — business logic and legal numbering complete, but real accounting postings are conditional on company settings not guaranteed to be configured.
10. **Demo scenario:** Record a 5% provisional cash deposit, activate it (show the Form-78 sequence and memo entry if accounts are configured), release it at contract close.

## 8. `demo_gov_commitment`
1. **Technical name:** `demo_gov_commitment`
2. **Business module:** "الارتباطات والتسميح - رقابة الموازنة" (Budget Commitment & Clearance Control)
3. **Purpose:** Implements budget-commitment control (ارتباط → تجنيب → تسميح) so spending is reserved and cleared *before* payment — without depending on Odoo's own `account_budget`.
4. **Key features:** `_compute_consumed()` derives consumed/available balance by **text-matching** `demo_gov.daftar55.commitment_ref` against this record's number (loose text link, not a foreign key); `_check_budget()` blocks approval if the request exceeds the available balance.
5. **Menu path:** الديوان العام → الحسابات → الارتباطات والتسميح.
6. **Workflow:** `draft → submitted → approved → reserved → cleared → paid`; `cancelled` from any state except `paid`.
7. **Reports:** `commitment_report.xml` / `commitment_template.xml`.
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager` — no dedicated group.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — state machine and budget-ceiling check are solid; the link to actual spending is a manually-typed free-text field.
10. **Demo scenario:** Create a commitment for "توريد قرطاسية" against a budget line with a 50,000 EGP ceiling, تقديم → اعتماد → تجنيب → تسميح, then manually type the commitment number into a Daftar-55 entry to show `المُنصرَف حتى الآن` update.

## 9. `demo_gov_daftar224`
1. **Technical name:** `demo_gov_daftar224`
2. **Business module:** "دفتر 224 ع.ح — السجل اليومي المزدوج" (Daftar 224 Dual Daily Register)
3. **Purpose:** For every Daftar-55 payment, books one gross "صرفيات" entry and, if there are deductions, a parallel itemised "تسويات" entry.
4. **Key features:** `create_dual_entry_from_daftar55()` is called **automatically** from `Daftar55.action_post()` — this is the one genuine, fully-automatic cross-module integration found across the whole Accounts group. Records are immutable once created. `get_daily_totals(date)` feeds `demo_gov_form69`.
5. **Menu path:** الديوان العام → الحسابات → دفتر 224 ع.ح.
6. **Workflow:** No `state` field — created once and permanent.
7. **Reports:** `daftar224_report.xml` / `daftar224_template.xml`.
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — small, deterministic, directly exercised by the Daftar-55 posting flow.
10. **Demo scenario:** Post a Daftar-55 entry with deductions and immediately open دفتر 224 ع.ح to show both the gross and itemised-deduction rows auto-generated.

## 10. `demo_gov_daftar55`
1. **Technical name:** `demo_gov_daftar55`
2. **Business module:** "دفتر 55 - سجل المدفوعات المتسلسل" (Daftar 55 Sequential Payment Register)
3. **Purpose:** The core legal payment-register ledger of the whole suite — every supplier/beneficiary payment passes through here.
4. **Key features:** Auto-sequenced; `_compute_deductions()` computes 4 standard deductions (دمغة عادية 1%, دمغة إضافية ×3, دمغة نسبية 0.008 rounded to nearest 0.5, ضريبة أرباح 3%) unless `is_payroll_entry`; bespoke Arabic number-to-words; immutable once created.
5. **Menu path:** الديوان العام → الحسابات → دفتر 55 - سجل المدفوعات المتسلسل.
6. **Workflow:** `draft → received → reviewed → cleared → posted → archived`. `action_post()` requires `cleared` and triggers Daftar-224 creation.
7. **Reports:** `daftar55_report.xml` / `daftar55_template.xml`.
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — complete lifecycle, real computed deductions, genuine cross-module hook into Daftar 224.
10. **Demo scenario:** Create a Daftar-55 entry for a 100,000 EGP vendor invoice, show the automatic deduction breakdown and Arabic amount-in-words, "حفظ بالاضابير" to auto-create a Dossier, walk استلام→مراجعة→تسميح→ترحيل, watch Daftar-224 appear automatically.

## 11. `demo_gov_advances`
1. **Technical name:** `demo_gov_advances`
2. **Business module:** "السلف والضمانات البنكية" (Advances & Bank Guarantees)
3. **Purpose:** Manages permanent/travel/transport employee advances (Forms 62/51/170) and vendor advance payments, plus the base bank-guarantee model used by contract tendering.
4. **Key features:** `demo_gov.advance`: polymorphic type, `amount_outstanding` computed, `is_overdue` flag. `demo_gov.bank.guarantee`: types, `days_to_expiry`/`is_expiring_soon` (≤30 days), `action_extend()` only flips state.
5. **Menu path:** الديوان العام → الحسابات → السلف والضمانات البنكية.
6. **Workflow:** Advance: `draft → submitted → approved → disbursed → settled`. Guarantee: `draft → active → extended / released / forfeited`.
7. **Reports:** `report_advance_form62.xml`, `report_bank_guarantee.xml`, `report_advances_register.xml`.
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager`.
9. **Status: PARTIALLY IMPLEMENTED** — `action_disburse()`'s own docstring promises an accounting entry ("إذا توفر حساب السلف") but **no entry is ever actually created**; the `account_move_id` field exists but is never written to.
10. **Demo scenario:** Create a permanent advance, تقديم→اعتماد→صرف, then تسوية with a partial settled amount; issue a preliminary 5% bank guarantee and show its "ينتهي قريباً" flag.

## 12. `demo_gov_budget_planning`
1. **Technical name:** `demo_gov_budget_planning`
2. **Business module:** "الموازنة التقديرية وتحليل الانحرافات" (Budget Planning & Variance Analysis)
3. **Purpose:** Builds the annual estimated budget by Egyptian classification (باب/فصل/بند/نوع) and tracks committed vs. actual spend and variance.
4. **Key features:** `amount_committed` auto-computed by searching `demo_gov.commitment`; `amount_actual` requires a manual `action_compute_actual()` batch run, text-matched against Daftar-55.
5. **Menu path:** الدفاتر المساعدة → الموازنة التقديرية.
6. **Workflow:** `draft → submitted → approved → active → closed`.
7. **Reports:** `report_budget_summary.xml`, `report_budget_variance.xml`, `report_budget_execution.xml`.
8. **Roles/access:** `account.group_account_user` read-only, `account.group_account_manager` read/write/create.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — committed-amount linkage is real; actual-spend linkage is a manual batch job relying on text matching.
10. **Demo scenario:** Create a budget plan, add a line, تقديم→اعتماد→تفعيل, click "تحديث المصروف الفعلي" to show variance/execution-rate update live.

## 13. `demo_gov_penalties`
1. **Technical name:** `demo_gov_penalties`
2. **Business module:** "دفتر حساب الجزاءات" (Penalties Book — Form 39)
3. **Purpose:** One unified legal register for employee disciplinary penalties and vendor/contractor contractual penalties, with a full appeal process.
4. **Key features:** Polymorphic subject type; `_check_amount_within_legal_limit()`; a catalogue of violation/penalty types with legal references; `demo_gov.penalty.appeal` can uphold/overturn/reduce.
5. **Menu path:** الدفاتر المساعدة → دفتر الجزاءات → الجزاءات / التظلمات / أنواع المخالفات / أنواع الجزاءات.
6. **Workflow:** `draft → recorded → approved → executed → [appealed → upheld/overturned → closed]`.
7. **Reports:** `report_penalty_decision_template.xml`, `report_penalty_register_template.xml`.
8. **Roles/access:** `group_penalty_user`/`group_penalty_manager`; a data file **force-grants `group_penalty_manager` to `base.user_admin`** with a code comment noting this works around an Odoo menu-visibility limitation.
9. **Status: PARTIALLY IMPLEMENTED** — catalogue and appeal lifecycle complete, but `action_execute()`'s financial impact is an explicit documented stub (posts a chatter message asking the finance team to create the entry manually).
10. **Demo scenario:** Record a vendor penalty, تسجيل→اعتماد→تنفيذ, trigger a "تظلم" and resolve it with "تخفيف" to a reduced amount.

## 14. `demo_gov_special_funds`
1. **Technical name:** `demo_gov_special_funds`
2. **Business module:** "الصناديق والحسابات الخاصة" (Special Funds & Ring-Fenced Accounts)
3. **Purpose:** Enforces that special-fund balances (service fees, rentals, donations, grants) must never be commingled; disbursement blocked if it would exceed that fund's own balance.
4. **Key features:** `check_disbursement_allowed(amount)` raises a `ValidationError` quoting the exact shortfall; inter-fund transfers require **two separate user approvals** before posting.
5. **Menu path:** الديوان العام → الحسابات → الصناديق والحسابات الخاصة.
6. **Workflow:** `draft → posted`; `reversed` selection value exists but **no action ever transitions into it** (unreachable from the UI).
7. **Reports:** **None** — no `reports/` directory exists for this module.
8. **Roles/access:** `account.group_account_user` (read-only) / `account.group_account_manager` (write/create, no unlink on either model).
9. **Status: PARTIALLY IMPLEMENTED — CONFIRMED BUG.** `FundTransaction.action_post()` references `rec.commitment_id`, but **no such field is defined anywhere on the model** — posting any `expense`-type transaction will raise an `AttributeError` at runtime.
10. **Demo scenario:** Create a fund, post a revenue transaction, then attempt an expense exceeding the balance to show the `ValidationError` guard. **Do not post an actual expense transaction live** — it will crash on the missing field. Stick to revenue + the balance-warning banner.

## 15. `demo_gov_dossier`
1. **Technical name:** `demo_gov_dossier`
2. **Business module:** "الاضابير - نظام الأرشفة (استمارة 101 ساير)" (Dossier Archive System)
3. **Purpose:** Enforces that every Daftar-55 disbursement has the 9 mandated supporting documents attached, and tracks shelf location.
4. **Key features:** `REQUIRED_ATTACHMENTS` = 9 hard-coded categories; `_compute_missing()`; `action_validate_attachments()` raises a `UserError` listing missing documents — but **no call site exists anywhere else in the codebase**, so it's a manual presenter action, not a gate on Daftar-55 posting. `action_open_dossier()` on Daftar-55 creates-or-opens the linked dossier.
5. **Menu path:** الديوان العام → الحسابات → الاضابير - نظام الأرشفة.
6. **Workflow:** `open → closed` field exists but **no button transitions it**.
7. **Reports:** `dossier_report.xml` / `dossier_template.xml`.
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager` — neither group can `unlink` (intentional for an archive).
9. **Status: PARTIALLY IMPLEMENTED** — completeness computation is solid, but the enforcement is informational, not a hard gate, and `state` has no transition button.
10. **Demo scenario:** From a posted Daftar-55 click "حفظ بالاضابير", attach a few of the 9 documents, show `missing_attachments` in red, attach the rest to flip `is_complete` to true — state clearly this is informational in this build, not a blocking gate.

## 16. `demo_gov_form69`
1. **Technical name:** `demo_gov_form69`
2. **Business module:** "استمارة 69 - الحسبة اليومية" (Form 69 Daily Reckoning)
3. **Purpose:** The daily reconciliation form cross-checking Daftar-224's daily totals against Daftar-55's daily payment totals, feeding Form-75 closing.
4. **Key features:** `generate_daily_reckoning(date)` pulls Daftar-224 totals and independently sums Daftar-55, computing `match_ok`; inline Gregorian→Hijri converter.
5. **Menu path:** الديوان العام → الحسابات → استمارة 69 — الحسبة اليومية.
6. **Workflow:** `draft → done` (automatic) `→ signed`.
7. **Reports:** `form69_report.xml` / `form69_template.xml`.
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager` (no unlink).
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — concrete, testable reconciliation math; Hijri conversion has a defensive bare-except fallback.
10. **Demo scenario:** Trigger daily reckoning for a date with Daftar-55 postings, show the green "تطابق" indicator, then a day with a known mismatch to show the red banner, finally "✅ اعتماد الحسبة".

## 17. `demo_gov_form75`
1. **Technical name:** `demo_gov_form75`
2. **Business module:** "استمارة 75 - الحسابات الشهرية والختامية" (Form 75 Monthly/Annual Closing — 3-Stage Sequential Approval)
3. **Purpose:** Rolls up a period's Form-69 reckonings and forces a strict sequential 3-tier sign-off (auditor → accounts manager → department head).
4. **Key features:** `build_from_form69()` aggregates the period and carries forward the prior closing balance; each stage hard-blocks if the prior stage hasn't happened; `action_reject()` routes back exactly one stage.
5. **Menu path:** الديوان العام → الحسابات → استمارة 75 — الإغلاق الشهري.
6. **Workflow:** `draft → submitted → stage1_approved → stage2_approved → approved`, with `rejected` as a one-stage-back branch.
7. **Reports:** `form75_report.xml` / `form75_template.xml` (printable only once `approved`).
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager` (no unlink). **No separate groups per stage** — nothing stops the same user clicking all three approval buttons themselves.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — solid sequential-gate logic, but note the access-control gap in point 8.
10. **Demo scenario:** Build a Form-75 from the current month's reckonings, submit, walk through all three approval stages (each button only appears once the previous is done), then show a rejection bouncing back exactly one stage.

## 18. `demo_gov_fixed_assets`
1. **Technical name:** `demo_gov_fixed_assets`
2. **Business module:** "الأصول الثابتة" (Government Fixed Assets — EAS #10)
3. **Purpose:** Full fixed-asset register compliant with Egyptian Accounting Standard #10, integrated with custody tracking and auctions.
4. **Key features:** `_generate_depreciation_schedule()` supports straight-line, declining-balance, and sum-of-years-digits; `action_post_all_pending_depreciation()`; `demo_gov.asset.disposal.action_post()` builds a real multi-line `account.move` reversing accumulated depreciation, booking gain/loss.
5. **Menu path:** الديوان العام → الحسابات → الاصول الثابتة → سجل الاصول الثابتة / جميع الاصول / قرارات التصرف / فئات الاصول (manager-only).
6. **Workflow:** Asset: `draft → active → suspended → active → disposed`. Disposal: `draft → approved → posted`.
7. **Reports:** `report_asset_register.xml`, `report_asset_card.xml`, `report_depreciation_schedule.xml`, `report_disposal.xml`.
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager`; `ir.rule` blocks deletion of active assets.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — **one of the most complete modules in the whole repo**: real multi-method depreciation math, real posted entries at every step (not stubs).
10. **Demo scenario:** Register a government vehicle, activate to show the auto-generated depreciation schedule, post year-1 depreciation, then sell it via disposal and show the posted entry with gain/loss.

## 19. `demo_gov_stock_finance_bridge`
1. **Technical name:** `demo_gov_stock_finance_bridge`
2. **Business module:** "ربط المخزون بالحسابات" (Stock-to-Finance Bridge)
3. **Purpose:** Auto-generates journal entries whenever a stock-permit document (issue/addition/transfer/return) is posted, bridging warehouse movements into the GL.
4. **Key features:** `_get_account_rule()` resolves the most specific matching rule; `create_journal_entry()` builds and immediately posts a 2-line `account.move`.
5. **Menu path:** الدفاتر المساعدة → ربط المخزون بالحسابات.
6. **Workflow:** `stock.finance.journal.entry`: `draft → posted / cancel`.
7. **Reports:** None.
8. **Roles/access:** `account.group_account_user` / `account.group_account_manager`.
9. **Status: PARTIALLY IMPLEMENTED — CONFIRMED BUG.** Two parallel, slightly inconsistent implementations exist for the **same four model names** (`bridge_engine.py` auto-posts directly; `stock_bridge.py` opens a wizard instead for three of the four, and doesn't even define the action for `issue`). Both files load via the same `__init__.py`, so the actually-active behaviour depends on Odoo's class-merge order — not demo-safe without verifying live first.
10. **Demo scenario:** Open "إعداد الحسابات" to show a pre-seeded rule, then click the journal-entry action from a posted stock permit — **verify the exact button behaviour live before recording**, given the ambiguity above.

## 20. `l10n_eg_eta_invoice`
1. **Technical name:** `l10n_eg_eta_invoice`
2. **Business module:** "الفاتورة الإلكترونية ETA" (Egyptian Tax Authority e-Invoicing — B2B/B2G)
3. **Purpose:** Builds and submits ETA-compliant e-invoice JSON documents for posted invoices, tracking submission/validation status and QR codes.
4. **Key features:** `_build_eta_document()` constructs a complete ETA-SDK-shaped document; `action_submit()` POSTs to `/api/v1/documentsubmissions`; `eta.config` handles OAuth2 tokens.
5. **Menu path:** الدفاتر المساعدة → 🧾 الفاتورة الإلكترونية ETA.
6. **Workflow:** `draft → submitted → valid / invalid`; `cancelled`.
7. **Reports:** `report_eta_invoice.xml`.
8. **Roles/access:** `eta.config` manager-only; invoices user read-only / manager read-write-create.
9. **Status: SIMULATED — by explicit design.** `EtaConfig._get_access_token()` has a hard gate: in a demo environment it raises with the message *"تكامل ETA معطّل في بيئة العرض التجريبي — لا يتم الاتصال بأي خادم حقيقي لهيئة الضرائب المصرية"*. The integration code is genuinely complete (full SDK payload, OAuth2, polling), but **no real network call to ETA can ever succeed from this build** — deliberately, not as an oversight.
10. **Demo scenario:** Post an invoice, click "إرسال لـ ETA" to show the clear, honest demo-mode block message, then walk through the built payload structure via Developer Mode to prove the integration is code-complete.

## 21. `demo_gov_coa_fix`
1. **Technical name:** `demo_gov_coa_fix`
2. **Business module:** "تصحيح شجرة الحسابات إلى الترقيم الحكومي الرسمي (8 خانات)" (Chart-of-Accounts Fix Tool)
3. **Purpose:** A one-time maintenance tool (not a user-facing app) to replace Odoo's default chart of accounts with the official 8-digit Egyptian government chart, run manually via `odoo shell`.
4. **Key features:** A 1,369-account reference CSV plus 9 standalone Python scripts meant to be piped into `odoo shell` one at a time; tags old accounts as deprecated rather than deleting them.
5. **Menu path:** None — no UI.
6. **Workflow:** None.
7. **Reports:** None.
8. **Roles/access:** None.
9. **Status: NOT INSTALLED** — `installable: False`, self-labelled *"مش موديول للتثبيت"* (not a module to install).
10. **Demo scenario:** Not a live-demo item — at most mention it as evidence of care taken setting up the official chart, run once by an administrator before the demo.

## 22. `demo_gov_acct_reports`
1. **Technical name:** `demo_gov_acct_reports`
2. **Business module:** "التقارير المحاسبية — ميزان مراجعة وكشوف حسابات" (Accounting Reports)
3. **Purpose:** A focused wizard offering two core reports: trial balance and partner ledger statement.
4. **Key features:** `demo_gov.acct.report.wizard` (transient); `read_group` aggregation on posted lines.
5. **Menu path:** الديوان العام → التقارير → التقارير المحاسبية الحكومية.
6. **Workflow:** Stateless wizard.
7. **Reports:** `report_trial_balance.xml`, `report_partner_ledger.xml`.
8. **Roles/access:** `account.group_account_user`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — a redundant subset of modules 23/24.
10. **Demo scenario:** Open the wizard, pick trial balance, set a date range, generate the PDF — note this is a subset of `demo_gov_gl_reports`/`demo_gov_reports`.

## 23. `demo_gov_gl_reports`
1. **Technical name:** `demo_gov_gl_reports`
2. **Business module:** "التقارير المحاسبية الحكومية" (adds General Ledger & Chart of Accounts)
3. **Purpose:** A superset of #22 — same trial balance + partner ledger, plus a true general-ledger-by-account report and a full chart-of-accounts dump with live balances.
4. **Key features:** `_get_general_ledger_data()`, `_get_chart_of_accounts_data()` (with deprecated-account tagging, tying to module 21).
5. **Menu path:** الدفاتر المساعدة → التقارير المحاسبية.
6. **Workflow:** Stateless wizard.
7. **Reports:** `report_trial_balance.xml`, `report_partner_ledger.xml`, `report_general_ledger.xml`, `report_chart_of_accounts.xml`.
8. **Roles/access:** `account.group_account_user`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — functionally complete, clearly a superset of module 22's logic (duplicated, not reused).
10. **Demo scenario:** Generate "شجرة الحسابات المصرية" to show the full 8-digit chart with live balances, then "دفتر الأستاذ العام" filtered to one journal.

## 24. `demo_gov_reports`
1. **Technical name:** `demo_gov_reports`
2. **Business module:** "التقارير الحكومية" (Government Reports Suite)
3. **Purpose:** The master, all-in-one report wizard spanning accounting, budget, cash/bank, aging, auction, and stock-valuation reports.
4. **Key features:** 24 report types in one radio selector, each with its own `_get_*_data()` method reading directly from the relevant model. `action_print_report()` falls back to constructing a raw `ir.actions.report` dict if no matching action record is found — defensive but fragile.
5. **Menu path:** الديوان العام → التقارير → 📋 التقارير الحكومية.
6. **Workflow:** Stateless wizard.
7. **Reports:** 20 individual templates plus a shared layout and a chart-of-accounts template.
8. **Roles/access:** `base.group_user` — any logged-in user can run every report (broadest access of any report module).
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — impressively broad, but duplicates virtually all of modules 22/23's logic independently (copy-pasted, not reused); **pre-test each of the 24 report types before recording**.
10. **Demo scenario:** The best single screen to close the Finance section on — generate "ملخص دفتر 55", "كشف حالة الارتباطات", "ميزان المراجعة الحكومي" and "سجل خطابات الضمان" in quick succession.

### End-to-end Finance flow (verified by cross-module hooks, not just shared menus)
`demo_gov_budget_planning` → `demo_gov_commitment` → `demo_gov_daftar55` (real stamp/tax math, Arabic amount-in-words) → `demo_gov_daftar224` (**automatically** created on Daftar-55 posting — the one genuinely-wired cross-module automation in this whole group) → `demo_gov_dossier` → `demo_gov_cheques`/`demo_gov_cash_books` → `demo_gov_subsidiary_books`/`general_ledger_ar` → `demo_gov_reports`. For a capital-purchase variant, splice in `demo_gov_fixed_assets` and `l10n_eg_eta_invoice`'s honest "disabled in demo" message. **Avoid `demo_gov_special_funds` expense postings and the `demo_gov_stock_finance_bridge` issue-permit button in an unrehearsed live demo** — both have confirmed code defects above.

---

# PART 2 — المشتريات — Purchases / Procurement (9 modules)

## 1. `procurement_committee`
1. **Technical name:** `procurement_committee`
2. **Business module:** "تشكيل اللجان - Committee Formation (Egypt Gov.)"
3. **Purpose:** Implements the Law 182/2018 requirement that every procurement/tender/auction action be run by a formally-constituted committee — reusable mixin so RFQs/POs/contracting/auctions can require an active committee (FR-P7 sovereign entities exempt).
4. **Key features:** `procurement.committee` (type, auto-sequenced ref, formation date, authority ref); `committee.member` lines (chairman/member/secretary/expert, exactly-one-chairman constraint); `_compute_chairman`; `hr.employee` stat buttons ("عدد اللجان"/"رئيس لجنة").
5. **Menu path:** الخدمات الحكومية التجريبية → المشتريات → **اللجان**.
6. **Workflow:** `draft → active (requires members) → closed`.
7. **Reports:** 5 government-form templates (مذكرة تشكيل اللجنة POGV_GFM_P01_F_11, محضر اجتماع لجنة البت الفني POGV_GFM_P01_F_17, محضر فض المظاريف POGV_GFM_P01_F_14, مذكرة عرض للمحافظ، مذكرة الحماية المدنية). Several forms have placeholder blank rows for data not wired up.
8. **Roles/access:** `group_contract_user` / `group_contract_manager` / `group_contract_director` (the last defined but not actually gated on any code path).
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — full CRUD, state machine, constraints, 5 reports, 3-tier security all present.
10. **Demo scenario:** Create a committee "لجنة البت الفني لتوريد أجهزة كمبيوتر", add 3 members (one chairman), activate, print "مذكرة تشكيل اللجنة".

## 2. `procurement_adjudication`
1. **Technical name:** `procurement_adjudication`
2. **Business module:** "البت الفني والمالي - Dual-Envelope Adjudication"
3. **Purpose:** Implements the two-envelope (technical then financial) tender-evaluation process: open technical envelopes, score, open financial envelopes only for suppliers who passed, auto-select lowest valid bid, notify winner, generate the Purchase Order.
4. **Key features:** Links to an RFQ and to 3 real `procurement.committee` records (genuine cross-module dependency); `adjudication.supplier.line` with technical/financial results; `action_adjudicate()` **really** picks the lowest financial bid among technically-passed suppliers (`min(eligible, key=lambda l: l.financial_bid)`); `action_create_po()` really creates a `purchase.order`.
5. **Menu path:** الخدمات الحكومية التجريبية → المشتريات → **البت الفني والمالي**.
6. **Workflow:** `draft → technical_open → financial_open → adjudicated → awarded (access-gated: `group_adjudication_director` only, else `AccessError`) → po_created` (+ `cancelled`).
7. **Reports:** 8 distinct report templates (tender ad, vendor list, technical/financial minutes, award notification, commitment form, social insurance doc, labor office doc), each state-gated correctly.
8. **Roles/access:** `group_adjudication_member` / `group_adjudication_chairman` / `group_adjudication_director` (only group that can award and create the PO).
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — **the most complete module reviewed in this whole project**: full guarded state machine, real bid-comparison logic, role-gated approval, 8 reports correctly wired.
10. **Demo scenario:** Link the RFQ, pick the 3 committees formed earlier, add 3 supplier lines, "فتح المظاريف الفنية", mark 2 "pass", "فتح المظاريف المالية", enter bids, "مقارنة العروض والترسية" (watch the auto-pick), log in as a director to "إخطار الترسية" then "إنشاء أمر التوريد".

## 3. `demo_gov_scm_requisition`
1. **Technical name:** `demo_gov_scm_requisition`
2. **Business module:** "طلب الاحتياج — التدبير والمشتريات" (code C-SCM-01)
3. **Purpose:** Captures a department's internal need with estimated cost lines; on approval automatically creates a budget commitment — the entry point of the SCM→Finance chain.
4. **Key features:** `action_approve()` **raises a real validation error** if the total exceeds `available_balance` (looked up live from `demo_gov.commitment`), then creates and auto-approves a commitment record — genuine cross-module integration.
5. **Menu path:** الخدمات الحكومية التجريبية → المشتريات → **طلبات الاحتياج**.
6. **Workflow:** `draft → submitted → approved → po_created` (+ `cancelled`).
7. **Reports:** `requisition_report.xml`/`requisition_template.xml` — full Arabic RTL template with 3 signature blocks.
8. **Roles/access:** `purchase.group_purchase_user` / `purchase.group_purchase_manager` — no module-specific groups.
9. **Status: PARTIALLY IMPLEMENTED — CONFIRMED GAP.** The `po_created` state is modeled and shown on the statusbar, but **no method anywhere ever writes it** — `action_create_po()` only opens a wizard pre-filling a new PO; the requisition itself stays "approved" forever. `action_cancel()` is also declared nowhere despite `cancelled` being a valid state value.
10. **Demo scenario:** Fill "الإدارة الطالبة", "بند الميزانية", add lines, "تقديم" then "✅ موافقة + إنشاء ارتباط" (show the auto-commitment chatter message), click "إنشاء أمر توريد" to hand off into Purchases.

## 4. `demo_gov_scm_purchase_bridge`
1. **Technical name:** `demo_gov_scm_purchase_bridge`
2. **Business module:** "أمر التوريد — الجسر مع استمارة 50" (code C-SCM-02)
3. **Purpose:** Blocks PO confirmation unless the linked budget commitment is approved, and automatically spawns a draft "استمارة 50" finance document on confirmation.
4. **Key features:** Overrides `button_confirm()`: raises `ValidationError` if the commitment isn't approved/reserved/cleared, auto-reserves it, then calls `_create_form50_draft()` exactly once (idempotency-guarded). Also tracks a bank-guarantee-letter block on the PO.
5. **Menu path:** No standalone menu — extends the standard Purchases → Orders form.
6. **Workflow:** Participates in `purchase.order`'s native state machine via `button_confirm()` override. The guarantee-letter sub-flow (`not_required → pending → issued → expired/released`) has **no action/button anywhere** — data-entry only.
7. **Reports:** None (relies on `demo_gov_daftar55`'s own report).
8. **Roles/access:** `ir.model.access.csv` is **empty (header only)** — relies entirely on core `purchase` access.
9. **Status: PARTIALLY IMPLEMENTED** — the requisition-approval gate and automatic Form-50 generation are real and working; the guarantee-letter fields are a placeholder with no workflow.
10. **Demo scenario:** Open the PO from the requisition demo, show "تكامل الديوان العام" section, try Confirm on an unapproved commitment (blocked with an Arabic error), then confirm once approved and click the new "استمارات 50" stat button.

## 5. `l10n_eg_auction`
1. **Technical name:** `l10n_eg_auction`
2. **Business module:** "المزايدات - Auctions / Muzāyada"
3. **Purpose:** The reverse of procurement — government disposal/lease of surplus assets via auction: session → bids → award → either a confirmed Sale Order (Path A) or a multi-year lease contract (Path B).
4. **Key features:** `action_accept()` auto-rejects any other accepted bid (one-accepted-bid invariant); `action_award()` dispatches to real `sale.order` creation or `auction.lease.contract` creation; `action_generate_schedule()` builds installments with a real compounding formula `(1 + annual_increase_pct/100) ** (year_number-1)`.
5. **Menu path:** الخدمات الحكومية التجريبية → المشتريات → **المزايدات** → المزادات / عقود الإيجار.
6. **Workflow:** Request: `draft → confirmed → session_open → bidding → awarded → done` (+ `cancelled`). Lease: `draft → active → expired`.
7. **Reports:** `report_auction_award.xml`, `report_lease_contract.xml`.
8. **Roles/access:** `group_auction_user` / `group_auction_manager`.
9. **Status: PARTIALLY IMPLEMENTED — CONFIRMED BUG.** `data/auction_cron.xml` schedules a daily cron calling `_cron_apply_annual_increase()` on lease contracts — **this method does not exist anywhere in the module** (only `action_generate_schedule()`, a different one-time method). The cron will raise `AttributeError` every time it fires.
10. **Demo scenario:** Create a sale-type auction request, تأكيد → فتح الجلسة → بدء تسجيل العروض, add bids, قبول the highest, الترسية (show the Sale Order link), print إخطار الترسية. Separately create a lease request to show the payment-schedule generation. **Do not let the daily cron fire live** — disable or skip it.

## 6. `c1_purchase_approval_matrix`
1. **Technical name:** `c1_purchase_approval_matrix`
2. **Business module:** "PO Approval Matrix" (English-only, generic)
3. **Purpose:** Generic multi-tier monetary-threshold approval workflow for Purchase Orders.
4. **Key features:** `purchase.approval.threshold` tiers with approvers; full audit log; `button_confirm()` override routes to approval if a threshold applies; two polished bilingual e-mail templates exist but **are never actually sent by any code path** (dead data).
5. **Menu path:** **No standalone menu** — reachable only via Settings → Technical → Actions (Developer Mode); the only visible surface is injected Approve/Reject/Reset buttons on the PO form.
6. **Workflow:** `approval_state`: `draft → pending_t1 → pending_t2 → pending_t3 → approved` (or `rejected` at any tier, `reset_to_draft` from rejected).
7. **Reports:** None.
8. **Roles/access:** No module-specific `res.groups`; authorization enforced only in code (`if user not in current_approver_ids: raise UserError`), not via security groups.
9. **Status: PARTIALLY IMPLEMENTED** — the state machine and threshold routing are real; no menu without dev mode, and the e-mail notification feature is half-built (templates exist, never triggered).
10. **Demo scenario:** Set up Tier 1/2 thresholds via Developer Mode, confirm a PO in Tier 2's range — show it switches to "Pending T2" instead of confirming, approve as the Tier-2 user, show it actually confirms with the log tab populated.

## 7. `c6_cost_centre`
1. **Technical name:** `c6_cost_centre`
2. **Business module:** "Cost Centre on Requisitions" (English-only)
3. **Purpose:** Adds a department/cost-centre dimension to Purchase Orders, drawing on `c5_financial_dimensions`.
4. **Key features:** A single field `x_cost_centre_id` on `purchase.order`, no logic.
5. **Menu path:** None — field on the standard PO form.
6. **Workflow:** None.
7. **Reports:** None.
8. **Roles/access:** No security file — relies on `purchase.order`'s own ACLs.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — too simple to be "partial".
10. **Demo scenario:** Point at the field on a PO, select a department-type dimension, mention it's the basis for future cost-centre spend reporting (no such report exists in this module).

## 8. `c7_credit_bureau`
1. **Technical name:** `c7_credit_bureau`
2. **Business module:** "Credit Bureau API" (a Sales module, not Purchasing — extends `sale.order`)
3. **Purpose:** Adds a customer credit check (Green/Amber/Red) before a Sale Order can be confirmed, intended to call an external Credit Bureau API.
4. **Key features:** `_call_credit_api()` **explicitly short-circuits in demo mode**: it never calls a real external API — it deterministically derives a synthetic score from a SHA-256 hash of the partner ID and posts a chatter message stating *"DEMO MODE — Credit Bureau check simulated (no external API call made)"*. RED blocks confirmation unless an override reason is entered — that gate logic is real.
5. **Menu path:** No standalone menu for config (dev-mode only); the check button and colored alert banner are injected into the Sales Order form.
6. **Workflow:** `credit_check_state`: `not_checked → green/amber/red/api_error`.
7. **Reports:** None.
8. **Roles/access:** Config restricted to `sales_team.group_sale_manager`; a latent access-rights bug noted (a salesperson triggering the check may hit an access error on the config record).
9. **Status: SIMULATED — the textbook case.** The module itself openly discloses the simulation in the chatter.
10. **Demo scenario:** Click "Credit Check" on a draft Sales Order, show the explicit "DEMO MODE — simulated" chatter message, then the colored banner, and a blocked Confirm until an override reason is entered.

## 9. `c8_contract_pricing`
1. **Technical name:** `c8_contract_pricing`
2. **Business module:** "Contract Pricing Override" (a Sales module, not Purchasing)
3. **Purpose:** Pre-negotiated, date-bounded contract price per customer+product that auto-overrides the standard price on a Sale Order line.
4. **Key features:** `_check_no_overlap()` constraint prevents overlapping date ranges for the same partner+product; `_onchange_product_contract_price()` auto-applies the price the moment a matching product is selected.
5. **Menu path:** No standalone menu (dev-mode only); a "Contract" toggle column on Sale Order lines.
6. **Workflow:** No state — onchange-triggered price override.
7. **Reports:** None.
8. **Roles/access:** `sales_team.group_sale_manager` full CRUD; `base.group_user` read-only.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — overlap/date validation and auto-apply logic are real and self-consistent.
10. **Demo scenario:** Create a contract price for a customer+product via Developer Mode, add that product to a new Sale Order line for that customer, show `price_unit` auto-populate with the "Contract" toggle lighting up.

### End-to-end Procurement flow (the strongest single demo flow in the whole repo)
`demo_gov_scm_requisition` (raises a need, auto-creates a commitment) → `procurement_committee` (forms technical/financial/opening committees) → `procurement_adjudication` (attaches those committees, opens envelopes, compares bids, awards, creates the PO) → `demo_gov_scm_purchase_bridge` (blocks PO confirm on an unapproved commitment, auto-spawns Form 50) → optionally `c1_purchase_approval_matrix` and `c6_cost_centre`. `l10n_eg_auction` is the correct mirror-image (disposal/lease) and should be demoed as its own self-contained scenario. `c7_credit_bureau`/`c8_contract_pricing` are Sales-side, not Procurement — keep them in their own short aside and explicitly flag `c7_credit_bureau` as simulated.

---

# PART 3 — المخازن والمستودعات — Warehouses / Stores (6 modules)

## 1. `demo_gov_scm_issue`
1. **Technical name:** `demo_gov_scm_issue`
2. **Business module:** "أذونات الصرف والارتجاع والتحويل" (Issue / Return / Transfer Permits)
3. **Purpose:** Manages the three classic Egyptian warehouse paper-forms: Form 2 (إذن الصرف), Form 8 (إذن الارتجاع) and inter-warehouse transfer permits, each requiring an approved Form 50 reference before posting.
4. **Key features:** Per-line `qty_available` computed live from `stock.quant`; on posting, auto-creates an **immutable, unlink-protected** `stock.issue.register.line` audit record with its own legal sequence; return permits support a committee concept with condition grading.
5. **Menu path:** الخدمات الحكومية التجريبية → المخازن والمستودعات → **أذونات الصرف والارتجاع** → أذونات الصرف / أذونات الارتجاع / أذونات التحويل / سجل حركات الصرف.
6. **Workflow:** Issue: `draft → submitted → approved (stock-availability check) → posted (creates register line) → cancelled`. Return: `draft → submitted → committee → approved → posted → cancelled` — **the `committee` state is unreachable**; no button ever transitions into it. Transfer: `draft → submitted → approved → posted → received → cancelled`. `action_create_journal_entry()` on Issue explicitly `raise UserError('وحدة ربط المخزون بالحسابات غير مثبتة')`; on Return/Transfer it's a no-op stub.
7. **Reports:** **None** — no `reports/` directory exists.
8. **Roles/access:** Core `stock.group_stock_user` / `stock.group_stock_manager` only — no custom groups.
9. **Status: PARTIALLY IMPLEMENTED** — core CRUD and Issue's state machine are solid with a real protected audit register, but no PDF reports at all, the accounting bridge is explicitly disabled, and the Return-permit committee stage is dead code.
10. **Demo scenario:** New Issue permit, fill warehouse/location/line, enter "رقم استمارة 50", تقديم → اعتماد → ترحيل — تنفيذ الصرف; show the auto-created, undeletable "سجل الصرف" register entry.

## 2. `demo_gov_scm_warehouse`
1. **Technical name:** `demo_gov_scm_warehouse`
2. **Business module:** "لجنة الفحص والمخازن" (Inspection Committee & Warehouses — code C-SCM-03)
3. **Purpose:** The goods-receipt inspection step before accepting a purchase delivery: an inspection committee (3 signatories + storekeeper) records accepted/rejected quantities (Form 12), then a simple addition permit (Form 1) registers accepted items into stock.
4. **Key features:** `quantity_rejected` auto-computed; `action_finalize_and_attach_to_dossier()` creates a real attachment and files it into `demo_gov.dossier` — genuine cross-module integration.
5. **Menu path:** الخدمات الحكومية التجريبية → المخازن والمستودعات → **المستودعات والمخازن** → أذونات الإضافة (نموذج 1).
6. **Workflow:** Inspection: `draft → signed (requires storekeeper signature) → finalized (attaches to dossier)`. Addition: `draft → confirmed → moved`. **`action_move_to_stock()`'s docstring claims it registers items via `stock.picking`, but the body only writes `state='moved'` and a chatter message — no real stock movement occurs.** Also, no dedicated form/tree view exists for the Addition Permit model — it falls back to Odoo's auto-generated default view.
7. **Reports:** One real PDF (`action_report_inspection`, "محضر لجنة الفحص — نموذج 12 مخازن").
8. **Roles/access:** Core `stock.group_stock_user` / `stock.group_stock_manager` only.
9. **Status: PARTIALLY IMPLEMENTED** — the inspection-committee flow is complete and consistent with a working PDF and dossier integration; the warehouse-addition flow is a shell with no real stock effect.
10. **Demo scenario:** New inspection committee record, link a PO, fill ordered/received/accepted quantities, tick storekeeper signature, اعتماد المحضر, طباعة المحضر, إرفاق بالاضبارة.

## 3. `l10n_eg_custody`
1. **Technical name:** `l10n_eg_custody`
2. **Business module:** "إدارة العهد - Custody Management" (GAFI-compliant durable-asset tracking, Form 193)
3. **Purpose:** Tracks durable (non-consumable) items personally issued to employees as legal custody (عهدة), with mandatory National-ID capture for Central Auditing Organization audits, transfers between employees, and return-to-store.
4. **Key features:** National ID validated to exactly 14 digits; `stock.move` extended — on `_action_done()` for an outgoing durable-item picking with an employee set, it **auto-creates and auto-confirms** a custody record — real, not simulated, cross-model automation. `hr.employee` extended with custody smart-stat buttons. 4-step guided wizard. Record rules: regular storekeepers see only their own records.
5. **Menu path:** الخدمات الحكومية التجريبية → المخازن والمستودعات → **إدارة العهد** → جميع العهد / سجلات العهد / ➕ عهدة جديدة / تحويل عهدة / العهدة حسب الإدارة / ⚠ العهد المتأخرة / تقرير GAFI.
6. **Workflow:** `draft → active → transferred → returned`; `cancelled` (blocked once returned) `→ draft`.
7. **Reports:** 3 real QWeb-PDF reports — استمارة 193 (per-assignment signature form), كشف العهدة - نموذج 1 (single-employee list), كشف العهد المسجلة (fleet-wide register with totals).
8. **Roles/access:** `group_custody_user` ("أمين المخزن") / `group_custody_manager` ("مدير العهد"), with `ir.rule` scoping non-managers to their own records.
9. **Status: IMPLEMENTED BUT NOT VERIFIED — the most complete module in this group.** Full CRUD, consistent state machine, 3 working reports, custom groups + record rules, and genuine automatic integration from `stock.move`.
10. **Demo scenario:** Run the 4-step wizard entering a 14-digit national ID, pick a durable product and officials, submit (auto-confirms), print استمارة 193, then "تحويل عهدة" to a second employee and show "الحائز الحالي" and the state flip to "محولة".

## 4. `stock_addition_permit`
1. **Technical name:** `stock_addition_permit`
2. **Business module:** "إذن الإضافة - Addition Permit" (code FR-I1)
3. **Purpose:** Two-step government goods-receipt: an Inspection Report validating a delivered batch, auto-creating an إذن إضافة (Form 1) that formally adds the accepted quantity.
4. **Key features:** `action_validate()` result "pass"/"partial" **auto-creates** an addition permit; "fail" sets `rejected` instead — real conditional automation. Smart buttons on `stock.picking`/`purchase.order`/`hr.employee`.
5. **Menu path:** الخدمات الحكومية التجريبية → المخازن والمستودعات → محاضر الفحص / أذونات الإضافة (siblings, not nested).
6. **Workflow:** Inspection: `draft → done (auto-creates addition permit) / rejected`. Addition: `draft → posted / cancel`. **`action_post()`'s docstring claims it creates a stock journal entry; the body only validates `product_id` and writes `state='posted'` — no `stock.move`/`account.move` is ever created despite a reserved `stock_move_id` field.**
7. **Reports:** 3 real QWeb-PDF reports — إذن إضافة نموذج 1 (4-signature block), استمارة 50 (replica of the original form), inspection report.
8. **Roles/access:** `group_storekeeper` / `group_inspector` / `group_warehouse_manager` (3-tier, implied chain).
9. **Status: PARTIALLY IMPLEMENTED** — the inspection→addition linkage, state machine, security groups and 2 detailed government-form PDFs genuinely work; the actual stock-ledger effect of "posting" is not implemented.
10. **Demo scenario:** Create a `stock.picking` from a PO, محاضر الفحص ▸ New (reference auto-fills from the PO), set test group + qty, result "مطابق للمواصفات", "✓ تحقق من الصحة" — show the linked إذن إضافة auto-appear, "✓ ترحيل إذن الإضافة", print both PDFs.

## 5. `stock_stocktaking_eg`
1. **Technical name:** `stock_stocktaking_eg`
2. **Business module:** "الجرد الحكومي - Government Stocktaking" (Form 6)
3. **Purpose:** Runs a formal physical-stock-count session comparing book quantities (live `stock.quant`) against physically counted quantities, computing surplus/deficit for GAFI audit and the full suite of related government stock forms.
4. **Key features:** `action_load_stock()` pulls real `stock.quant` balances; per-line `difference_qty`/`difference_value` computed live; session totals (surplus/deficit items & value) computed live; HR extension replaces plain-text committee members with a proper Many2many.
5. **Menu path:** الخدمات الحكومية التجريبية → المخازن والمستودعات → **الجرد الحكومي**.
6. **Workflow:** `draft → counting (loads live quants) → done → validated` (requires `group_stocktaking_chairman`).
7. **Reports:** 7 real report actions — Form 6, كشف الزيادة والعجز, بيان مخزون راكد, دفتر الشطب نموذج 4, نموذج 5 يومية المخزن, نموذج 8 ارتجاع, نموذج 9 تالف/مفقود, كشف حصر الأصناف — all confirmed wired to buttons.
8. **Roles/access:** `group_stocktaking_user` / `group_stocktaking_chairman`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — a genuinely working counting/variance engine with a full, consistent report suite; functionally the most complete reporting module in this group.
10. **Demo scenario:** New session, pick a warehouse, "📦 تحميل المخزون الحالي", manually edit a couple of physical counts to create surplus/deficit, "✓ ترحيل الجرد" then "🔒 اعتماد الجرد" (as chairman), print "نموذج 6" and "كشف الزيادة والعجز".

## 6. `c10_inventory_revaluation`
1. **Technical name:** `c10_inventory_revaluation`
2. **Business module:** "Inventory Revaluation Report" (English-led, no Arabic-first name)
3. **Purpose:** On-demand valuation report: as of a chosen date, lists every product's on-hand qty × standard cost, with an advertised "prior month variance" column.
4. **Key features:** `_get_revaluation_data()` aggregates real `stock.quant` by product. **The module's headline feature — the prior-month variance column — is hard-coded to `0.0` and never actually computed**, despite being printed on the PDF.
5. **Menu path:** Not under the government menu tree at all — hangs off core Odoo's own `stock.menu_stock_root`.
6. **Workflow:** None — a stateless wizard.
7. **Reports:** One report with current value + prior-month value + variance columns (the last two always zero).
8. **Roles/access:** `stock.group_stock_manager` only.
9. **Status: SIMULATED for its headline "prior month variance" feature; IMPLEMENTED BUT NOT VERIFIED for current-value valuation.**
10. **Demo scenario:** As Stock Manager, generate the current stock-on-hand valuation table — **avoid implying the "prior month"/"variance" columns mean anything**, since they're always zero.

### End-to-end Warehouse flow
`demo_gov_scm_warehouse` / `stock_addition_permit` (goods arrive, inspected, accepted into stock) → `demo_gov_scm_issue` (issued out to a department/employee under formal permits) → `l10n_eg_custody` (if durable, auto-tracked as personal custody, transferable) → `stock_stocktaking_eg` (periodic reconciliation, surplus/deficit, write-off). `c10_inventory_revaluation` sits outside this narrative (different menu root, unimplemented headline feature) — show it separately as a quick valuation aside.

---

# PART 4 — الموارد البشرية والرواتب — HR / Payroll (18 modules)

## 1. `demo_gov_hr_employee`
1. **Technical name:** `demo_gov_hr_employee`
2. **Business module:** ملف الموظف الحكومي — بيانات ومستندات
3. **Purpose:** Extends `hr.employee` with the government identity/classification fields every other HR module depends on.
4. **Key features:** `national_id` (14 chars, unique), `permanent_employee_number` (auto sequence, immutable once set), `gov_employment_type`, `gov_entity`, `civil_service_grade`, appointment decision fields; a required-document checklist model with a computed "missing documents" warning banner.
5. **Menu path:** No standalone menu — adds a "بيانات حكومية" tab to the standard Employee form.
6. **Workflow:** No `state` — a data-extension module.
7. **Reports:** None.
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED.**
10. **Demo scenario:** Open an employee → "بيانات حكومية" → fill National ID + employment type → show the auto-generated Permanent Employee Number and the missing-documents banner.

## 2. `demo_gov_hr_leave`
1. **Technical name:** `demo_gov_hr_leave`
2. **Business module:** إدارة الإجازات الحكومية — قانون 81/2016
3. **Purpose:** Adapts standard Odoo Time Off to the 9 statutory civil-service leave types and adds a mandatory "Leave Department" confirmation step, plus work-injury leave fields.
4. **Key features:** 9 seeded leave types; work-injury fields; computed `annual_leave_entitlement_days` — **the code's own comment calls this "reference only, needs HR confirmation of the latest executive regulation."**
5. **Menu path:** No standalone menu — adds a confirm button to the standard Time Off form.
6. **Workflow:** Reuses Odoo's native leave state, plus one extra gate: `action_confirm_by_leave_dept()`.
7. **Reports:** None directly (the certificate ships from `demo_gov_hr_reports`).
8. **Roles/access:** No dedicated access file.
9. **Status: PARTIALLY IMPLEMENTED** — entitlement formula explicitly self-flagged as unconfirmed.
10. **Demo scenario:** Request "إجازة سنوية", manager approves, HR clicks "تأكيد قسم الإجازات", show the tracked confirmation in chatter.

## 3. `demo_gov_hr_org_development`
1. **Technical name:** `demo_gov_hr_org_development`
2. **Business module:** التطوير المؤسسي — بطاقات الوظائف والموازنة
3. **Purpose:** Job description/grading governance plus the annual position-budget form (Form 5 / SSRS-04) tracking budgeted vs filled vs vacant posts.
4. **Key features:** `demo_gov.hr.job.evaluation.action_approve()` writes the evaluated grade back onto `hr.job`; `demo_gov.hr.position.budget` computes filled/vacant/movements from employee appointment/termination dates.
5. **Menu path:** الموارد البشرية → التطوير المؤسسي → تقييمات الوظائف / موازنة الوظائف (استمارة 5).
6. **Workflow:** Evaluation: `draft → approved`.
7. **Reports:** Form 5 — real, data-bound.
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED.**
10. **Demo scenario:** Evaluate "محاسب حكومي" to "الدرجة الثانية", approve, show the grade propagate onto the Job form, print Form 5.

## 4. `demo_gov_hr_payroll_insurance_eg`
1. **Technical name:** `demo_gov_hr_payroll_insurance_eg`
2. **Business module:** الرواتب الحكومية — التأمينات الاجتماعية
3. **Purpose:** Models the insurable-wage ceiling/floor and employee/employer contribution split per Social Insurance Law, by year.
4. **Key features:** `compute_contributions(gross_wage)` correctly clamps wage to [min,max] then applies both percentages — real formula.
5. **Menu path:** الرواتب الحكومية → التأمينات الاجتماعية.
6. **Workflow:** None — static reference table.
7. **Reports:** None (consumed by Form 132).
8. **Roles/access:** `hr.group_hr_user`/`hr.group_hr_manager`.
9. **Status: PARTIALLY IMPLEMENTED — placeholder data, self-disclosed.** The seed file's own comment states the figures (1,000–15,000 EGP ceiling, 11%/18.75% split) are *"illustrative demo values only... Finance must review and update with the officially approved figures."* The calculation engine is real; the numbers are not current/official.
10. **Demo scenario:** Show the bracket, trace it into a payslip's insurance deduction line — state clearly these are placeholder rates.

## 5. `demo_gov_hr_payroll_run`
1. **Technical name:** `demo_gov_hr_payroll_run`
2. **Business module:** الرواتب الحكومية — دورة الصرف الشهرية
3. **Purpose:** The actual monthly payroll engine — salary files, monthly batch computation, rewards, external/non-employee payments, annual tax settlement, and the disbursement register (دفتر 129 سايرة).
4. **Key features:** `action_compute_payslips()` genuinely computes each payslip: gross = job wage + earnings; pulls executed payroll transactions; calls the insurance bracket; computes tax via the progressive-bracket engine; computes stamp duty; `net_salary = gross − insurance − tax − stamp − manual deductions + adjustments`. **This is real, working arithmetic, not a stub.** `action_post()` on the run creates real disbursement lines **and** a `demo_gov.daftar55` entry for the net total — a genuine SCM/HR→Finance bridge.
5. **Menu path:** الرواتب الحكومية (root) → ملفات مرتبات الموظفين / دورات الرواتب الشهرية / مكافآت الموظفين / دفتر 129 سايرة.
6. **Workflow (run):** `draft → computed → under_review → approved (blocks if any payslip isn't completed) → posted`. Payslip: `draft → completed / rejected`.
7. **Reports:** Form 132 (per-employee payslip, confirmed real and data-bound) + Form 132 bulk (whole-run totals page with 3 signature blocks).
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager` across 8 sub-models.
9. **Status: IMPLEMENTED BUT NOT VERIFIED — the most functionally complete module in the entire repository.** Real end-to-end computation chain: salary → transactions → insurance → tax → stamp duty → net → disbursement ledger → Form 132. Correctness depends on the placeholder tax/insurance seed data from modules 4/7.
10. **Demo scenario:** Create a salary file, run the monthly payroll, "حساب كشوف المرتبات", mark completed, submit → approve → ترحيل, open "دفتر 129 سايرة" to show the disbursement line, print Form 132 (single + bulk).

## 6. `demo_gov_hr_payroll_structure`
1. **Technical name:** `demo_gov_hr_payroll_structure`
2. **Business module:** الرواتب الحكومية — بنود الراتب والحركات الاستثنائية
3. **Purpose:** Defines the salary component chart and the "exceptional effects" transaction log (penalties, special leave, part-time, chronic illness, etc.) that monthly payroll consumes.
4. **Key features:** 9 real salary components (BASIC, HOUS, TRANS, WNAT, PINC, INCA, PROM, PEN, INST); 14 defined transaction reason codes; `action_execute()` marks a transaction executed, which is what payroll's computation later searches for.
5. **Menu path:** Creates the root "الرواتب الحكومية" menu → إعدادات بنود الراتب / حركات التأثيرات الاستثنائية.
6. **Workflow:** Transaction: `draft → executed`.
7. **Reports:** None directly.
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED.**
10. **Demo scenario:** Create a "جزاء" (penalty) transaction, execute it, show it picked up automatically in that month's payroll run.

## 7. `demo_gov_hr_payroll_tax_eg`
1. **Technical name:** `demo_gov_hr_payroll_tax_eg`
2. **Business module:** الرواتب الحكومية — الشرائح الضريبية المصرية
3. **Purpose:** Progressive income-tax category/bracket engine, proportional stamp duty, flat tax on non-employee rewards.
4. **Key features:** `compute_tax()` correctly applies progressive brackets slice-by-slice — real algorithm, verified by reading the code.
5. **Menu path:** الرواتب الحكومية → الشرائح الضريبية.
6. **Workflow:** None — static configuration.
7. **Reports:** None (consumed by Form 132).
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: PARTIALLY IMPLEMENTED — placeholder data, self-disclosed, NOT real Egyptian tax brackets.** The seed file's comment is explicit: *"illustrative only... literally copied from a user-manual example... this is NOT the complete 6-category official bracket table."* Only 1 of 6 claimed categories is actually seeded.
10. **Demo scenario:** Open the one example bracket, trace how it feeds a payslip's monthly tax line — **explicitly caveat to the audience** that production tax tables must be loaded by Finance before real use.

## 8. `demo_gov_hr_pension`
1. **Technical name:** `demo_gov_hr_pension`
2. **Business module:** المعاشات والتأمينات
3. **Purpose:** Pension/health benefit plan catalog, enrollment, and retirement settlement calculation at age 60, producing the statutory Form 15.
4. **Key features:** `action_compute()` computes `pension_amount = final_salary * min(years/40, 1) * 0.8` — **explicitly commented as an illustrative number needing Finance/Legal sign-off**, not verified official law text.
5. **Menu path:** الموارد البشرية → المعاشات والتأمينات.
6. **Workflow:** `draft → computed → approved → form15_issued`.
7. **Reports:** Form 15 — real, confirmed data-bound (and a near-duplicate SSRS-05 version ships separately from `demo_gov_hr_reports`, so two print buttons will appear once both modules are installed).
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED for the workflow/report; the pension formula itself is a self-flagged placeholder.**
10. **Demo scenario:** Set termination type "بلوغ سن المعاش" with 35 years of service, compute a settlement (shows ~70% replacement), approve, mark Form 15 issued, print it.

## 9. `demo_gov_hr_performance`
1. **Technical name:** `demo_gov_hr_performance`
2. **Business module:** تقييم الأداء الحكومي — كفاءة وتظلمات
3. **Purpose:** Annual government-style performance rating (5-point scale) tied to an incentive allowance, plus a grievance escalation path (employee → committee → union).
4. **Key features:** Rating auto-fills an incentive % from a hard-coded table — **explicitly commented as reference-only, needs HR approval.**
5. **Menu path:** الموارد البشرية → تقييم الأداء.
6. **Workflow:** Appraisal: `draft → submitted → reviewed → finalized`. Grievance: `submitted → committee_review → union_review → resolved`.
7. **Reports:** SSRS-03 ships separately from `demo_gov_hr_reports`.
8. **Roles/access:** Appraisal readable by all employees; grievance full CRUD-minus-delete for employees.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — incentive-% table is a self-flagged placeholder.
10. **Demo scenario:** Create an appraisal rated "ممتاز" (auto-fills 10%), submit → review → finalize; file a grievance and walk it through committee → union → resolved.

## 10. `demo_gov_hr_public_service`
1. **Technical name:** `demo_gov_hr_public_service`
2. **Business module:** الخدمة العامة — خريجات بدون راتب
3. **Purpose:** Models the one-year unpaid "Public Service" assignment for female graduates, with automatic end-of-term flagging.
4. **Key features:** Daily cron schedules a to-do activity and flips `public_service_ended=True` once past the computed end date.
5. **Menu path:** الموارد البشرية → الخدمة العامة.
6. **Workflow:** No explicit `state` — a single boolean flipped by the cron.
7. **Reports:** Report files present (referenced, not read in full).
8. **Roles/access:** No dedicated access file.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — small but complete, no placeholder caveats in code.
10. **Demo scenario:** Set an employee's start date ~360 days ago, trigger the cron, show an expiry-warning activity appear.

## 11. `demo_gov_hr_recruitment`
1. **Technical name:** `demo_gov_hr_recruitment`
2. **Business module:** التوظيف والتأهيل الحكومي
3. **Purpose:** Wraps standard Odoo Recruitment with a "recruitment project" concept, links applicants to it, and adds government-specific termination types.
4. **Key features:** `demo_gov.hr.recruitment.project` with planned positions and applicant count; `hr.employee` extension adds `gov_termination_type` (retirement/resignation/death/dismissal/absence).
5. **Menu path:** الموارد البشرية → التوظيف والتأهيل → مشاريع التعيين.
6. **Workflow:** `draft → published → screening → interviewing → closed`.
7. **Reports:** None directly.
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED.**
10. **Demo scenario:** Create a recruitment project, publish, link applicants, move through screening → interviewing → closed; separately show a termination type feed Org Development's "movements out" count.

## 12. `demo_gov_hr_reports`
1. **Technical name:** `demo_gov_hr_reports`
2. **Business module:** التقارير الحكومية الثمانية — SSRS Wave 3
3. **Purpose:** A pure reporting bundle — 7 of the 8 official "SSRS" government HR forms, bound onto models from other modules.
4. **Key features:** SSRS-01 (work-injury committee form, on `hr.leave`), SSRS-02 (leave-balance certificate, on `hr.employee`), SSRS-03 (performance report, on appraisal), SSRS-05 (Form 15, on pension settlement — duplicate of module 8's own), SSRS-06 (secondments report, on transfer), SSRS-07 (training-needs survey), SSRS-08 (financial-disclosure color-coded status report) — all 7 confirmed real, data-bound templates.
5. **Menu path:** No menus of its own — print actions attached to the target models' own forms.
6. **Workflow:** N/A — reports only.
7. **Reports:** As listed above.
8. **Roles/access:** No security file — rides on the underlying models' access.
9. **Status: IMPLEMENTED BUT NOT VERIFIED.**
10. **Demo scenario:** Print SSRS-08 from a disclosure record list to show the color-coded compliance table across several employees — a strong "at a glance" moment.

## 13. `demo_gov_hr_takaful`
1. **Technical name:** `demo_gov_hr_takaful`
2. **Business module:** صندوق التكافل (Solidarity Fund)
3. **Purpose:** Employee mutual-aid fund — membership, monthly contributions, payout requests for marriage/birth/death/retirement.
4. **Key features:** `fund_balance` computed from contributions minus payouts; `action_compute_amount()` applies fixed amounts or a tenure-based multiplier for retirement.
5. **Menu path:** الموارد البشرية → صندوق التكافل → أعضاء الصندوق / الاشتراكات / طلبات الصرف / إعدادات الصندوق.
6. **Workflow:** Contribution: `draft → posted`. Payout: `draft → approved → paid`.
7. **Reports:** None.
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: SIMULATED for the accounting/posting side — self-disclosed in code.** `action_post()`'s own comment confirms totals are updated in-model but **no real `account.move` is ever created**.
10. **Demo scenario:** Enroll a member, post 3 months of contributions (show the running balance grow), request and approve a marriage payout — caveat clearly that no real journal entry is posted.

## 14. `demo_gov_hr_training`
1. **Technical name:** `demo_gov_hr_training`
2. **Business module:** التدريب الحكومي — احتياجات وخطة ودورات
3. **Purpose:** Training-needs assessment feeding an annual plan, course catalog/registration, before/after impact measurement. **Also creates the shared root "الموارد البشرية" menu that almost every other HR module hangs off.**
4. **Key features:** Needs workflow feeding the plan; course catalog with seat tracking; registration with a 5-point before/after competency scale.
5. **Menu path:** Creates `menu_gov_hr` → التدريب → الاحتياجات التدريبية / الدورات التدريبية / تسجيلات الدورات / المدربون.
6. **Workflow:** Need: `draft → submitted → approved/rejected → planned`. Registration: `draft → requested → manager_approved → confirmed → completed` (or `cancelled` any time).
7. **Reports:** SSRS-07 ships from `demo_gov_hr_reports`.
8. **Roles/access:** Courses read-only to all employees; instructor restricted.
9. **Status: IMPLEMENTED BUT NOT VERIFIED.**
10. **Demo scenario:** Raise a training need, approve, add to plan, create a course, register employees, walk through the full registration lifecycle filling in before/after competency scores.

## 15. `demo_gov_hr_transfer`
1. **Technical name:** `demo_gov_hr_transfer`
2. **Business module:** النقل والندب والإعارة والترقيات
3. **Purpose:** Tracks secondments/loans/transfers (with 30-day expiry alerting and renewal) and promotion-committee workflow.
4. **Key features:** "Settlement" transfers require **dual approval** (central agency AND finance ministry) before `action_approve()` succeeds; daily cron alerts any active transfer ending within 30 days.
5. **Menu path:** الموارد البشرية → النقل والندب والترقيات.
6. **Workflow:** Transfer: `draft → approved (dual-approval gated for settlements) → active → ended / cancelled`; `action_renew()` resets the alert. Promotion: `proposed → committee_review → approved (writes new grade) / rejected`.
7. **Reports:** SSRS-06 ships from `demo_gov_hr_reports`.
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED.**
10. **Demo scenario:** Second an employee for 45 days, approve, activate, trigger the 30-day-expiry cron to show the alert, renew it; run a promotion through proposed → committee → approved and show the grade update.

## 16. `demo_gov_hr_disclosure`
1. **Technical name:** `demo_gov_hr_disclosure`
2. **Business module:** إقرار الذمة المالية
3. **Purpose:** Anti-corruption financial-disclosure filing, required at first appointment and auto-renewed every 6 years.
4. **Key features:** Computed `net_worth`; `action_approve()` **auto-creates the next 6-year renewal cycle record**; daily cron alerts within 30 days of due date and flags overdue.
5. **Menu path:** الموارد البشرية → الإفصاح المالي.
6. **Workflow:** `draft → notified → submitted → approved (spawns next cycle) → overdue` (cron-driven), with `action_reject_correction()` sending it back to draft.
7. **Reports:** SSRS-08 ships from `demo_gov_hr_reports`.
8. **Roles/access:** `hr.group_hr_user` / `hr.group_hr_manager`.
9. **Status: IMPLEMENTED BUT NOT VERIFIED** — the 6-year chaining logic is fully coded, not a stub.
10. **Demo scenario:** File a first-appointment disclosure, fill assets/liabilities, submit → approve, point out the auto-created next renewal record, print SSRS-08.

## 17. `demo_gov_hr_uat_data` — INTERNAL TOOL, EXCLUDE FROM CUSTOMER DEMO
1. **Technical name:** `demo_gov_hr_uat_data`
2. **Business module:** أدوات الاختبار — الموارد البشرية والرواتب
3. **Purpose:** A QA/demo-data generator (extension of `demo_gov_uat_tools`'s wizard) that auto-creates realistic records across 10 HR categories for testing.
4. **Key features:** `generate_all()` chains 10 generator methods, each DB-savepoint-wrapped; `_generate_hr_payroll()` actually drives a full payroll run through its state machine as a smoke test.
5. **Menu path:** No end-user menu — only extra checkboxes on the existing UAT wizard.
6. **Workflow:** N/A — transient wizard.
7. **Reports:** None.
8. **Roles/access:** Inherits the base UAT wizard's technical-user access.
9. **Status: IMPLEMENTED BUT NOT VERIFIED as a tool — irrelevant classification since this is a QA utility, not a customer-facing feature.**
10. **Not a customer demo scenario** — running it live would look like "cheating" rather than demonstrating a real workflow. Use it only off-camera to seed demo data beforehand.

## 18. `demo_gov_egypt_national_id`
1. **Technical name:** `demo_gov_egypt_national_id`
2. **Business module:** التحقق من صحة تركيب الرقم القومي المصري
3. **Purpose:** A shared, non-destructive validator applied to every model storing a 14-digit Egyptian national ID, so an invalid ID is rejected at save time everywhere.
4. **Key features (confirmed algorithm):** Validates century digit, reconstructs and checks the birthdate as a real calendar date not in the future, validates the governorate code against an official ~28-entry table, and extracts/cross-checks the gender-parity digit. **Digit 14 (checksum) is explicitly NOT verified** — the code's own docstring states no official checksum formula is publicly documented, so only its presence as a single digit is confirmed. Applied via `_inherit` (no original files modified) across `hr.employee`, custody records, the custody wizard, sureties, payroll non-employee/external-salary records, and cash transfers — deliberately excluding `demo_gov_daftar55`'s dual-purpose field (with a documented rationale).
5. **Menu path:** No UI of its own — a backend constraint firing on existing forms.
6. **Workflow:** N/A.
7. **Reports:** None.
8. **Roles/access:** N/A.
9. **Status: IMPLEMENTED BUT NOT VERIFIED (and knowingly partial by design)** — genuine structural validation on 4 of 5 logical checks; the checksum digit is deliberately not validated.
10. **Demo scenario:** Enter an employee national ID with an invalid governorate code → show the precise Arabic rejection naming the problem; enter a valid one (century "2", real birthdate, governorate "01") → show it save; optionally show the gender cross-check reject a mismatched ID.

### End-to-end HR/Payroll flow
`demo_gov_hr_recruitment` (hire) → `demo_gov_hr_employee` (open file, National ID validated) → `demo_gov_hr_payroll_structure` (assign components) → `demo_gov_hr_payroll_tax_eg` + `demo_gov_hr_payroll_insurance_eg` (parameters) → `demo_gov_hr_payroll_run` (monthly run → Form 132 → disbursement ledger). Satellite flows that also chain logically: leave (law 81/2016), performance (appraisal → grievance), transfer (secondment/promotion), disclosure (6-year renewal), pension (→ Form 15), Takaful, org development (→ Form 5), and the SSRS report layer on top of nearly everything. **State plainly on camera**: the Egyptian tax-bracket and social-insurance figures are explicitly placeholder/example data per the modules' own code comments — the calculation engine is real, the numbers are not official. The national-ID validator checks structure/governorate/birthdate but not the undocumented checksum digit. Takaful's posting step is explicitly simulated.

---

# PART 5 — الذكاء الاصطناعي — AI Agent modules (19 modules)

**Bottom line up front: none of the 19 agent modules call an LLM for their core decision logic.** All are deterministic Python — threshold checks, SQL/ORM domain queries, `statistics.stdev`/Z-score, `SequenceMatcher`/checksum fuzzy matching, keyword/regex classification, and weighted scoring formulas. One module — `demo_gov_arabic_ai_assistant` — does contain real HTTP calls to an LLM backend (Ollama), but only as a low-confidence fallback behind a rule-based parser that handles the vast majority of cases itself.

## 1. `demo_gov_ai_agents_menu`
Pure menu-organizer: `post_init_hook` groups the other 18 agent modules' top-level menus under one "مجموعة وكلاء AI" parent. No AI of any kind. **Status: IMPLEMENTED AND TESTED** (confirmed via `KNOWN_LIMITATIONS.md`'s live-install record). Demo: open the sidebar, show all 18 sub-apps nested under one entry.

## 2. `demo_gov_arabic_ai_assistant` — the one with a real LLM call
مساعد لغوي عربي داخل Odoo — اسألني بالعربي. A **local, deterministic Arabic NLU pipeline** (normalization, tokenization, hardcoded Arabic alias dictionary e.g. "الموردين"→`res.partner`, keyword rules for count/sum/top-N/date-range) handles most questions. **Only if the local plan fails or scores confidence < 30** does it call `_ollama_plan()` — a real `requests.post()` to `http://host.docker.internal:11434` (Ollama, model `llama3.2:1b`). Hardcoded safelists block sensitive models/fields regardless of which path answers. Every query is logged.
**Status: PARTIALLY IMPLEMENTED / HYBRID.** `host.docker.internal:11434` is a Docker-Desktop-only hostname, and no Ollama service/model is provisioned anywhere in this repo — **the LLM fallback will not be reachable in this or most cloud/CI environments.** The failure is handled gracefully (no crash), and the local rule engine already answers the module's own example questions, so **the demo will work and look seamless — but every visible answer will come from the local rule engine, not from AI inference**, unless an Ollama server is separately stood up and pointed at beforehand.
Demo: "ما هو عدد الموردين؟" → instant answer with a "Local" badge (`used_ollama: false`) — a safe, honest scripted scenario.

## 3. `demo_gov_budget_forecast_ai_agent` — وكيل توقع انحرافات الموازنة
Linear extrapolation (`actual_to_date / months_elapsed * 12`) + threshold bucketing (critical/warning/surplus/normal); monthly cron + manual run; QWeb PDF + Arabic HTML narrative. **Status: TESTED (rule-based, not AI/ML).**

## 4. `demo_gov_budget_reallocation_ai_agent` — وكيل توصية إعادة توزيع الاعتمادات
Matches surplus/deficit budget lines (same category, excludes wages/debt), drafts a non-binding transfer memo ("دون تنفيذ فعلي"). **Status: TESTED (rule-based matching).**

## 5. `demo_gov_commitment_ai_agent` — وكيل أتمتة الارتباطات
Event-triggered on requisition approval; risk score from amount/limit/vendor-penalty lookups; auto-approves small low-risk commitments, routes the rest to human review. **Status: TESTED (rule-based risk scoring).**

## 6. `demo_gov_conflict_interest_ai_agent` — وكيل كشف تضارب المصالح
Weekly scan for phone/email/name overlaps between suppliers and committee members, plus repeat-pattern flags. **Status: TESTED (heuristic matching).**

## 7. `demo_gov_daftar55_reconcile_ai_agent` — وكيل مطابقة دفتر 55
Daily scan cross-checking Daftar-55 entries against `account.move` for missing/duplicate/mismatched entries. **Status: TESTED (deterministic reconciliation).**

## 8. `demo_gov_dead_stock_ai_agent` — وكيل كشف المخزون الراكد
Monthly scan flagging 180/365-day no-movement items, overstock, near-duplicate product names. **Status: TESTED (threshold rules).**

## 9. `demo_gov_duplicate_claim_ai_agent` — وكيل كشف تكرار المستندات
Daily scan using attachment checksum + `difflib.SequenceMatcher` filename similarity + amount/date matching. **Status: TESTED (checksum + string-similarity, not ML).**

## 10. `demo_gov_eta_retry_ai_agent` — وكيل ETA لإعادة المحاولة الذكية
Keyword/substring error classifier with exponential-backoff retry. **Code's own docstring: "Rule-based local classifier. Can be replaced later by an on-prem LLM."** **Status: TESTED (explicitly non-LLM).**

## 11. `demo_gov_executive_briefing_ai_agent` — وكيل الملخص التنفيذي اليومي
Daily (8am) aggregation across 7 other agents' alerts into one weighted-score Arabic brief with an emailed action list — every sentence is a `%`-format Python template, no generative text. **Status: TESTED (aggregation, not generative AI).**

## 12. `demo_gov_payment_anomaly_ai_agent` — وكيل كشف شذوذ المدفوعات والشيكات
**Genuine Z-score statistics** (`statistics.mean`/`stdev` over 200 recent same-partner transactions) — the one agent using real descriptive statistics — plus weekend-payment/new-vendor/year-end-clustering rules. Event-triggered. **Status: TESTED (classical statistics, not ML).**

## 13. `demo_gov_payment_cycle_delay_ai_agent` — وكيل مراقبة التأخيرات الإدارية
Per-stage configurable SLA tracking across the dossier→Daftar55→payment-order→cheque→posting pipeline. **Status: TESTED (SLA threshold logic).**

## 14. `demo_gov_procurement_legal_compliance_ai_agent` — وكيل مراجعة الالتزام القانوني
Keyword/substring matching against attachment filenames/descriptions (never reads document content) to check required-document completeness; can hard-block PO confirmation. **Status: TESTED (keyword classification, not OCR/NLP).**

## 15. `demo_gov_procurement_splitting_ai_agent` — وكيل مراقبة تجزئة المشتريات
Detects possible PO "salami-slicing" — multiple near-threshold orders to one vendor in a rolling window. **Status: TESTED (threshold/windowing logic).**

## 16. `demo_gov_vendor_data_quality_ai_agent` — وكيل جودة بيانات الموردين
Scores vendor master-data completeness (0-100), can block PO confirmation below a minimum. **Status: TESTED (deterministic scoring).**

## 17. `demo_gov_vendor_penalty_ai_agent` — وكيل كشف جزاءات الموردين تلقائياً
Auto-creates a financial penalty when an inspection committee records rejection/partial conformity, with escalating rate (5/10/15%) and a templated Arabic notification letter. **Status: TESTED (rule engine + templated letter generation, not generative AI).**

## 18. `demo_gov_vendor_performance_ai_agent` — وكيل تقييم كفاءة الموردين
Monthly weighted score (40% quality + 25% timeliness + 20% penalties + 15% volume). **Status: TESTED (weighted formula).**

## 19. `procurement_adjudication_ai_agent` — وكيل تحليل العروض في البت الفني والمالي
PDF text extraction (`pdfminer`) + keyword-overlap scoring between supplier offers and the spec document — the code's own comment labels this **"an on-prem rule-based analysis hook."** Drafts non-binding minutes explicitly marked "استرشادي... لا تُعد قراراً نهائياً." **Status: TESTED (text extraction + keyword overlap, explicitly not an LLM).**

### Honesty summary for this group
**0 of 19** rely on an LLM/ML model for core decisions in day-to-day operation. **1 of 19** (`demo_gov_arabic_ai_assistant`) contains genuine, working LLM-call code, but it will not fire live in this demo environment without extra setup this repo doesn't provide. Two agents' own code comments explicitly disclose their rule-based nature. These are legitimate, well-built automation — threshold engines, a real Z-score anomaly detector, string-similarity duplicate detection — and should be marketed as exactly that: **"intelligent automation" or "business-rule agents," never as "generative AI" or "machine learning."**

---

# PART 6 — البنية التحتية والأدوات — Infra / Misc (14 modules)

## `demo_branding`
"Demo Branding & Environment Banner" — single source of truth for app/org name, environment label, support contact; the DEMO ENVIRONMENT banner; defines the shared root nav menu every government module parents under. **Status: IMPLEMENTED AND TESTED** (banner-overlap and settings-page bugs previously fixed, confirmed per `KNOWN_LIMITATIONS.md`).

## `demo_gov_seed_data`
Loads synthetic employees/vendors/customers/products so the demo isn't empty; `post_init_hook` applies a `DEMO_USERS_PASSWORD` env var to all demo accounts (avoids hardcoded passwords). **Status: IMPLEMENTED AND TESTED.**

## `demo_gov_dashboard` — re-verified, status corrected from "broken" to fixed
لوحة القيادة التنفيذية — real-time KPI dashboard across procurement/warehouse/custody/auctions/HR. Serves a static HTML/JS SPA via a controller, **not** QWeb — so the previously-documented malformed-XML issue in `dashboard_template.xml` (now confirmed fixed, and in any case dead code never referenced by any action) is moot. Git history shows a real fix: the menu's broken parent reference and a broken exception-fallback were both corrected. **Status: IMPLEMENTED AND TESTED** — do not repeat the old "excluded from install" claim in the script.

## `demo_gov_menu` — re-verified, confirmed still broken
الديوان العام... تنظيم القوائم — was meant to unify menu structure across 15 modules. **No code exists**: only `__manifest__.py`, referencing 8 view files that don't exist anywhere in the repo. **Status: BROKEN — cannot install. Exclude entirely.**

## `demo_gov_form50_print`
طبقة الطباعة الرسمية لاستمارة 50 — custom `_render_qweb_pdf` override forcing pixel-perfect letterhead alignment via a 75-entry coordinate table; readiness gate before final (non-watermarked) printing. Recently fully ported from a production backup (security, views, wizard, verified background image). **Status: IMPLEMENTED BUT NOT VERIFIED (live)** — the repo's own notes mark it "not yet live-tested."

## `demo_gov_custom_programs_menu`
Groups every `c1`–`c13` module's menu under one "مجموعة البرامج المخصصة" sidebar entry, same pattern as the AI-agents aggregator. **Status: IMPLEMENTED AND TESTED.**

## `demo_gov_uat_tools`
Internal QA tool — generates ~150 synthetic records across every government module under a shared batch tag, plus a companion cleanup wizard. A real safety guard (`_check_demo_environment()`, checks DB name starts with `demo_` AND `APP_ENV=demo`) is confirmed present on both the generate and cleanup wizards. **Status: IMPLEMENTED BUT NOT VERIFIED (live) — EXCLUDE from the customer-facing demo**, only run off-camera to seed data, and only ever on a `demo_` database.

## `c2_batch_posting`
Nightly auto-posts all draft journal entries; simple per-move try/except loop. **Status: IMPLEMENTED AND TESTED.**

## `c3_aging_report`
Standard AR/AP aging report with configurable buckets. **Status: IMPLEMENTED AND TESTED.**

## `c4_payment_matching`
Early-payment discount auto-posts the discount journal entry on payment confirmation. **Status: IMPLEMENTED AND TESTED.**

## `c5_financial_dimensions`
Department/Project/Region analytical dimensions added to journal entry lines. **Status: IMPLEMENTED AND TESTED.**

## `c11_budget_alert`
Nightly project-budget-vs-spend check, posts a chatter alert past a configurable % threshold, with sensible reset on credit notes. **Status: IMPLEMENTED AND TESTED.**

## `c12_intercompany_recharge`
Creates matched, balanced journal-entry pairs to move costs between related companies. **Status: IMPLEMENTED AND TESTED.**

## `c13_tax_xml_export`
Generates a structured tax-filing XML export (schema v3.2). **Status: SIMULATED for the "signed" claim.** The manifest advertises "signed" XML; `_sign_xml()` only appends a plain-text comment (`<!-- PKCS7-Signed by ... -->`) — **no real cryptographic signature is ever performed**, despite a `cryptography` import that's never actually used for signing. The XML generation itself is real and correct. **Never describe the output as "cryptographically signed" or submit-ready** — it's a draft export file.

---

**End of inventory. 90 modules, all read in full. See `Feature_Coverage_Matrix.md` for the one-page summary and `Demo_Scenarios.md` for the consolidated end-to-end flows used to build the two video scripts.**
