# Port Said Budget AI Monitoring Agent

This add-on implements a daily and weekly budget monitoring agent for the Port Said Odoo environment.

## Why it is a separate add-on
It inherits the existing `port_said.budget.plan` model instead of editing the core budget planning module directly. This makes deployment safer and easier to rollback.

## Dependencies
- `mail`
- `port_said_budget_planning`
- `port_said_commitment`

## Main model added
- `port_said.budget.alert`

## Existing models used
- `port_said.budget.plan`
- `port_said.budget.line`
- `port_said.commitment`
- `port_said.daftar55`

## Main methods
- `_cron_budget_monitor()` daily monitor
- `_cron_budget_weekly_report()` weekly Arabic report
- `_calculate_budget_line_metrics()` financial metrics
- `_calc_daily_burn_from_daftar55()` spending velocity
- `_get_budget_risk_level()` deterministic risk scoring

## Financial logic
The agent computes:
- Actual execution rate = actual spending / approved amount
- Commitment rate = committed amount / approved amount
- Exposure rate = (actual spending + commitments) / approved amount
- Daily burn rate from Daftar 55
- Expected exhaustion date

## Important customization points
1. If your active budget state is not `active` or `approved`, update `_cron_budget_monitor()`.
2. If Daftar 55 uses a different date field, adjust `_calc_daily_burn_from_daftar55()`.
3. If the budget menu should appear under an existing menu, replace the menu parent in `views/budget_alert_views.xml`.
4. If you want LLM integration, keep Odoo as the source of truth for numbers and use the LLM only to polish the Arabic wording.

## Installation
Copy the folder into your Odoo custom addons path, then run:

```bash
odoo -u port_said_budget_ai_agent -d YOUR_DATABASE
```

Or from Docker:

```bash
docker exec -it odoo17 odoo -u port_said_budget_ai_agent -d odoo17_db --stop-after-init
```

Then restart Odoo and install/upgrade the module from Apps.


## التشغيل اليدوي

تمت إضافة قائمة داخل Odoo باسم:

- وكيل مراقبة الموازنة
  - تشغيل فحص الموازنة الآن
  - فتح تنبيهات الموازنة
  - تنبيهات الموازنة

استخدم "تشغيل فحص الموازنة الآن" لاختبار الـ Agent مباشرة بدون انتظار الـ Cron اليومي.
