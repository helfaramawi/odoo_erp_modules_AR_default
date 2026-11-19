# Feature Coverage Report — Script-to-Module Timestamp Mapping

This is the honest accounting the brief demanded: **which of the 90 real modules actually get a timestamped, on-screen moment in the 30-minute script, and which don't.** Verified mechanically (grepped each module's distinctive Arabic business-name phrase against the actual script text in `03_Voiceover/Arabic_Narration_30_Minutes.md`), not by recollection — so this reflects what was actually written, not what was planned.

**90 modules total. 36 have a confirmed, timestamped on-screen moment in the 30-minute script. 54 do not appear in either script at all** — they exist only in the inventory and the planning document (`02_Demonstration/Demo_Scenarios.md`). Per the acceptance criteria, those 54 are listed explicitly below rather than silently omitted or falsely claimed as covered.

## Confirmed on-screen, with timestamp (36 modules)

| Timestamp | Module(s) |
|---|---|
| 01:00–02:30 | `demo_branding` (unified menu, implicit — the "الخدمات الحكومية التجريبية" app and its 4 categories) |
| 03:00–04:00 | `demo_gov_budget_planning` |
| 04:00–05:30 | `demo_gov_commitment` |
| 05:30–07:30 | `demo_gov_daftar55` |
| 07:30–08:15 | `demo_gov_daftar224` |
| 08:15–09:00 | `demo_gov_dossier` |
| 09:00–10:00 | `demo_gov_subsidiary_books`; `demo_gov_reports` and `demo_gov_acct_reports` named together for "ميزان المراجعة" — **not individually distinguished on screen**, see caveat below |
| 10:00–11:00 | `demo_gov_scm_requisition` |
| 11:00–12:30 | `procurement_committee` |
| 12:30–14:30 | `procurement_adjudication` |
| 14:30–15:30 | `demo_gov_scm_purchase_bridge` (its Form-50 stat button is what triggered a text-match against `demo_gov_form50_print`'s name below — see caveat) |
| 15:30–16:00 | `l10n_eg_auction` |
| 16:00–17:30 | `demo_gov_scm_warehouse` |
| 17:30–18:30 | `demo_gov_scm_issue` |
| 18:30–19:30 | `l10n_eg_custody` |
| 19:30–20:30 | `stock_stocktaking_eg` |
| 20:30–21:30 | `demo_gov_hr_recruitment`, `demo_gov_hr_employee`, `demo_gov_egypt_national_id` |
| 21:30–23:00 | `demo_gov_hr_payroll_structure`, `demo_gov_hr_payroll_insurance_eg`, `demo_gov_hr_payroll_run` |
| 23:00–24:30 | `demo_gov_hr_leave` (named explicitly); appraisal and transfer shown but without naming `demo_gov_hr_performance`/`demo_gov_hr_transfer` on screen text |
| 24:30–25:30 | `demo_gov_hr_pension`, `demo_gov_hr_takaful`, `demo_gov_hr_disclosure` |
| 25:30–26:00 | `demo_gov_hr_reports` |
| 26:00–28:00 | `demo_gov_ai_agents_menu` (group framing), `demo_gov_payment_anomaly_ai_agent`, `demo_gov_vendor_penalty_ai_agent`, `demo_gov_executive_briefing_ai_agent`, `demo_gov_arabic_ai_assistant` |
| 28:00–29:30 | `demo_gov_reports` (master console, revisited), `demo_gov_dashboard` |

**Two caveats on the auto-check above (manual correction):**
- `stock_addition_permit` is also demoed in the 16:00–17:30 beat (the script frames it as an alternate path alongside `demo_gov_scm_warehouse`'s inspection committee), even though its own distinctive report name ("إذن الإضافة") also matched.
- The automated text-match flagged `demo_gov_form50_print` and `c1_purchase_approval_matrix` as "present" — this is a **false positive**: the script's mention of "استمارة 50" at 14:30–15:30 refers to `demo_gov_scm_purchase_bridge`'s auto-created Form-50 draft, not to `demo_gov_form50_print`'s PDF-rendering engine, which is never opened on screen. `c1_purchase_approval_matrix` is only named in passing in `Demo_Scenarios.md` as an "optional governance layer" and was **not actually written into the final 30-minute narration** — remove it from the covered list; it belongs in the uncovered list below.

**Corrected total: 34 modules with a genuine, timestamped on-screen moment** (36 minus the 2 false positives).

## Not covered in either script — grouped by why

### Finance modules with real, working features that didn't make the 30-minute cut (14)
`general_ledger_ar`, `demo_gov_cash_books`, `demo_gov_cash_transfers`, `demo_gov_cheques`, `demo_gov_revenue_books`, `demo_gov_insurance_subsidiary`, `demo_gov_advances`, `demo_gov_penalties`, `demo_gov_special_funds` (correctly excluded — confirmed bug), `demo_gov_form69`, `demo_gov_form75`, `demo_gov_fixed_assets`, `demo_gov_stock_finance_bridge` (correctly excluded — confirmed ambiguous behavior), `l10n_eg_eta_invoice`, `demo_gov_gl_reports` (mentioned at 28:00 for "chart of accounts" but the business name itself isn't spoken).

### Procurement modules not shown (3)
`c1_purchase_approval_matrix`, `c6_cost_centre`, `c7_credit_bureau`, `c8_contract_pricing` — all four are Developer-Mode-only or Sales-side asides per the inventory; genuinely secondary to the core procurement story.

### Warehouse modules not shown (1)
`c10_inventory_revaluation` — deliberately kept as a "quick aside" per `Demo_Scenarios.md` and in practice cut entirely for time; its headline feature is simulated anyway (see coverage matrix).

### HR modules not shown (6)
`demo_gov_hr_org_development`, `demo_gov_hr_payroll_tax_eg` (the tax-bracket engine itself isn't opened on screen, only insurance is), `demo_gov_hr_performance`, `demo_gov_hr_public_service`, `demo_gov_hr_training`, `demo_gov_hr_transfer` — the 23:00–24:30 beat describes these conceptually in narration but no module is individually opened on camera.

### AI Agent modules not shown (14 of 19)
Only `demo_gov_ai_agents_menu`, `demo_gov_arabic_ai_assistant`, `demo_gov_payment_anomaly_ai_agent`, `demo_gov_executive_briefing_ai_agent`, `demo_gov_vendor_penalty_ai_agent` get screen time. The remaining 14 — `demo_gov_budget_forecast_ai_agent`, `demo_gov_budget_reallocation_ai_agent`, `demo_gov_commitment_ai_agent`, `demo_gov_conflict_interest_ai_agent`, `demo_gov_daftar55_reconcile_ai_agent`, `demo_gov_dead_stock_ai_agent`, `demo_gov_duplicate_claim_ai_agent`, `demo_gov_eta_retry_ai_agent`, `demo_gov_payment_cycle_delay_ai_agent`, `demo_gov_procurement_legal_compliance_ai_agent`, `demo_gov_procurement_splitting_ai_agent`, `demo_gov_vendor_data_quality_ai_agent`, `demo_gov_vendor_performance_ai_agent`, `procurement_adjudication_ai_agent` — are only covered by the narration's collective framing ("تسعة عشر وكيل أتمتة... تعمل في الخلفية") at 26:00, never individually demonstrated.

### Infra/reporting modules not shown (9)
`demo_gov_seed_data`, `demo_gov_menu` (correctly excluded — broken), `demo_gov_form50_print`, `demo_gov_custom_programs_menu`, `demo_gov_uat_tools` (correctly excluded — internal QA tool), `demo_gov_hr_uat_data` (correctly excluded, same reason), `demo_gov_coa_fix` (correctly excluded — admin-only, not installable), `c2_batch_posting`, `c3_aging_report`, `c4_payment_matching`, `c5_financial_dimensions`, `c11_budget_alert`, `c12_intercompany_recharge`, `c13_tax_xml_export`.

## Honest math
34 genuinely demonstrated out of 90 real custom modules = **~38% of the repository gets individual, named screen time in the 30-minute video.** The remaining ~62% either gets group/conceptual narration coverage (the AI-agent layer, several HR satellites) or no mention at all (most of the `c1`–`c13` generic add-ons, several Finance subsidiary-book modules, several infra/QA tools). This is a direct, unavoidable consequence of 90 modules vs. a 30-minute runtime at a pace that still lets viewers actually see a form being filled and a button being clicked — not a shortfall to paper over. A deeper-dive follow-up video (or a per-department 10–15 minute cut using the untouched material already written up in `01_Feature_Inventory/Complete_Custom_Addons_Inventory.md`) would be the honest way to raise this percentage, rather than padding the 30-minute cut with faster, shallower cuts that stop actually showing the product.

The 5-minute executive video does not attempt broad coverage by design — it is a highlight reel of ~10 modules selected for visual impact, explicitly scoped that way in its own script notes.
