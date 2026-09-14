# Demo Seed Data

This directory provides the safe, repeatable way to (re)populate the
Demo Edition with synthetic data. It never touches a production database
(see the guard rails in `demo-reset.sh`).

## What gets seeded automatically (module install)

Installing `demo_gov_seed_data` (which depends on `demo_branding` and the
core application modules) loads, via ordinary Odoo data files:

- **7 demo user accounts** (`demo.admin`, `demo.contracts_manager`,
  `demo.contracts_officer`, `demo.adjudication_chairman`,
  `demo.warehouse_manager`, `demo.storekeeper`, `demo.inspector`) —
  see `addons/l10n_eg_custody/data/demo_users.xml`.
- **7 matching HR employee records**, one per demo user.
- **4 demo vendors** and **3 demo customers/beneficiaries**.
- **6 demo inventory items** (laptop, printer, chair, paper, switch, cabinet).

All of it is synthetic. No record in this directory represents a real
person, company, or government entity.

## Setting the demo password

The XML data ships with a default demo-only password
(`Demo@2024`) so the modules install cleanly out of the box. To use a
different password (recommended for any shared/cloud demo), set
`DEMO_USERS_PASSWORD` in the environment before installing or resetting —
the `demo_gov_seed_data` post-install hook applies it to every `demo.*`
account automatically:

```bash
export DEMO_USERS_PASSWORD='choose-a-strong-demo-password'
APP_ENV=demo ./demo-reset.sh
```

## Resetting the demo database

```bash
APP_ENV=demo ./demo-reset.sh [db_name] [odoo_conf_path]
```

- Refuses to run unless `APP_ENV=demo` is set.
- Refuses to run against any database whose name doesn't start with `demo_`.
- Drops and recreates that database, then installs the Demo Edition module set.

## Layering end-to-end demo scenarios

The seed data above is master data only (who, and what's for sale/in
stock) — deliberately not scripted transactional records (purchase
requisitions, auctions, custody assignments, GL postings), because those
custom modules carry their own state-machine validations
(draft -> committee -> adjudicated -> awarded, etc.) that are only safe to
satisfy by going through the actual business logic, not by inserting raw
XML rows. On top of the seed data, walk each scenario once through the UI
using the demo accounts above — see `docs/demo/DEMO_GUIDE.md` for the
recommended sequence per module (procurement, custody, auction, GL). Doing
this once against a fresh `demo-reset.sh` database and leaving the records
in place is what gives the dashboards and reports non-empty numbers for a
live demo.
