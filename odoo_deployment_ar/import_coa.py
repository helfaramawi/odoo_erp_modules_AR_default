#!/usr/bin/env python3
"""Import Egyptian Government Chart of Accounts into Odoo 17."""
import csv, sys

env = env  # noqa: F821 — provided by odoo shell

company = env['res.company'].browse(1)
currency_egp = env['res.currency'].search([('name', '=', 'EGP')], limit=1)

print(f"Company: {company.name}")
print(f"Currency: {currency_egp.name if currency_egp else 'NOT FOUND'}")

# Valid Odoo 17 account types
VALID_TYPES = {
    'asset_receivable', 'asset_cash', 'asset_current', 'asset_non_current',
    'asset_prepayments', 'asset_fixed', 'liability_payable',
    'liability_credit_card', 'liability_current', 'liability_non_current',
    'equity', 'equity_unaffected', 'income', 'income_other',
    'expense', 'expense_depreciation', 'expense_direct_cost', 'off_balance',
}

created = 0
updated = 0
errors = 0

with open('/tmp/gov_coa.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        code = row['code'].strip()
        name = row['name'].strip()
        atype = row['account_type'].strip()
        reconcile = row['reconcile'].strip().lower() == 'true'

        if atype not in VALID_TYPES:
            print(f"  SKIP unknown type: {atype} for {code}")
            errors += 1
            continue

        existing = env['account.account'].search([
            ('code', '=', code), ('company_id', '=', 1)
        ], limit=1)

        vals = {
            'code': code,
            'name': name,
            'account_type': atype,
            'reconcile': reconcile,
            'company_id': 1,
        }

        if existing:
            existing.write(vals)
            updated += 1
        else:
            env['account.account'].create(vals)
            created += 1

        if (created + updated) % 100 == 0:
            print(f"  Progress: {created} created, {updated} updated, {errors} skipped")
            env.cr.commit()

env.cr.commit()
print(f"\nDone! Created: {created}, Updated: {updated}, Skipped: {errors}")
