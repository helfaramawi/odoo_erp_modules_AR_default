# Demo Edition — Enterprise Digital Operations Platform

A safe-to-share demonstration build of the government financial/ERP
module suite in this repository, with every client-identifying detail
replaced by neutral demo branding and synthetic data. See
[`docs/demo/`](../docs/demo/) at the repository root for the full
discovery, architecture, branding, security, and role documentation
this build is based on.

**This is not the production system.** It is a separate, isolated copy
(`demo_edition/`) built from it — the original `odoo_deployment_ar/`
tree is untouched. Nothing here can reach production databases, APIs,
or credentials; see [`docs/demo/SECURITY_REVIEW.md`](../docs/demo/SECURITY_REVIEW.md)
and [`docs/demo/INTEGRATIONS.md`](../docs/demo/INTEGRATIONS.md).

## What this is

- **Architecture**: Odoo 17 (Community) + PostgreSQL, ~50 custom addon
  modules (accounting/general ledger, budget, fixed assets, procurement
  & tenders, custody, auctions, cheques, cash/revenue books, inventory,
  government report forms). Same code as production, anonymized.
- **Prerequisites**: Docker + Docker Compose (recommended), or a local
  Odoo 17 + PostgreSQL 13+ install if you prefer running it bare.

## Quick start — Docker (recommended)

```bash
cd demo_edition
cp .env.example .env
# edit .env: set DEMO_DB_PASSWORD and DEMO_USERS_PASSWORD to your own values

# --env-file is explicit on purpose: with -f pointing into docker/, Compose
# can otherwise resolve its project directory there and miss ./.env
docker compose --env-file .env -f docker/docker-compose.demo.yml up -d --build

# first run only: create the demo database and install the modules.
# Note: /entrypoint.sh (not plain `odoo`) so HOST/PORT/USER/PASSWORD get
# translated into a real DB connection; --no-http because the main odoo
# process (started by `up` above) already holds port 8069 in this container.
docker compose --env-file .env -f docker/docker-compose.demo.yml exec odoo \
  /entrypoint.sh odoo -d "$DEMO_DB_NAME" \
  -i demo_branding,demo_gov_seed_data,l10n_eg_custody,l10n_eg_auction,procurement_committee,procurement_adjudication,stock_addition_permit,stock_stocktaking_eg \
  --stop-after-init --no-http

docker compose --env-file .env -f docker/docker-compose.demo.yml restart odoo
```

Then open `http://localhost:8069` (or your configured `DEMO_HTTP_PORT`).

Health check: `curl http://localhost:8069/api/health` → `{"status":"healthy","environment":"demo"}`.

## Quick start — local install (no Docker)

```bash
# 1. Get Odoo 17 core (not included in this repo)
git clone --branch 17.0 --depth 1 https://github.com/odoo/odoo.git /opt/odoo

# 2. Point Odoo at this repo's demo addons in addition to core addons
export ADDONS_PATH="/opt/odoo/addons,$(pwd)/addons"

# 3. Create a demo Postgres role/database and install
createdb demo_gov_erp
APP_ENV=demo DEMO_USERS_PASSWORD='choose-a-strong-demo-password' \
  python3 /opt/odoo/odoo-bin -d demo_gov_erp --addons-path="$ADDONS_PATH" \
  -i demo_branding,demo_gov_seed_data,l10n_eg_custody,l10n_eg_auction,procurement_committee,procurement_adjudication,stock_addition_permit,stock_stocktaking_eg \
  --stop-after-init

python3 /opt/odoo/odoo-bin -d demo_gov_erp --addons-path="$ADDONS_PATH"
```

## Demo roles

Seven role-based accounts are seeded automatically (login / password from
`DEMO_USERS_PASSWORD`, default `Demo@2024` if unset):
`demo.admin`, `demo.contracts_manager`, `demo.contracts_officer`,
`demo.adjudication_chairman`, `demo.warehouse_manager`,
`demo.storekeeper`, `demo.inspector`. Full permission matrix:
[`docs/demo/ROLE_MATRIX.md`](../docs/demo/ROLE_MATRIX.md).

## Resetting the demo

```bash
cd scripts/demo-seed
APP_ENV=demo ./demo-reset.sh
```

Refuses to run unless `APP_ENV=demo` and the target database name starts
with `demo_` — see [`scripts/demo-seed/README.md`](scripts/demo-seed/README.md).

## Testing

No automated test suite was added as part of this conversion (out of
scope for this pass — see
[`docs/demo/KNOWN_LIMITATIONS.md`](../docs/demo/KNOWN_LIMITATIONS.md)).
Before demonstrating, walk the sequence in
[`docs/demo/DEMO_SCRIPT.md`](../docs/demo/DEMO_SCRIPT.md) once end to end.

## Troubleshooting

- **Module fails to install / "depends on unknown module"**: install
  order matters — install `demo_branding` first, then
  `demo_gov_seed_data`, then the application modules (see the command
  above).
- **Don't add `demo_gov_menu` to the install list**: it's an incomplete
  module (manifest references view files that don't exist anywhere in
  the repo, pre-existing in production too) and installing modules that
  depend on it transitively hits `Recursion error in modules
  dependencies!` through `general_ledger_ar`. See
  [`docs/demo/KNOWN_LIMITATIONS.md`](../docs/demo/KNOWN_LIMITATIONS.md).
  Each module shows under Odoo's normal Apps menu without it.
- **`docker compose exec odoo odoo ...` fails with a Postgres socket
  error**: `exec` bypasses the official image's entrypoint script, which
  is what translates `HOST`/`PORT`/`USER`/`PASSWORD` into a real DB
  connection. Call `/entrypoint.sh odoo ...` instead of `odoo ...`.
- **That same command then fails with `Address already in use`**: the
  main Odoo process from `docker compose up -d` is already listening on
  8069 inside the container; add `--no-http` to the one-off install
  command (it doesn't need to serve HTTP, only install and exit).
- **`docker compose up` errors that a required `.env` variable is
  missing even though it's set in the file**: pass `--env-file .env`
  explicitly — with `-f docker/docker-compose.demo.yml`, Compose can
  otherwise resolve its project directory to `docker/` and look for
  `.env` there instead of in `demo_edition/`.
- **Arabic PDF reports show boxes instead of text**: the `Amiri`/`Noto`
  fonts are installed in the provided Dockerfile; on a bare install,
  install `fonts-hosny-amiri` (or equivalent) on the Odoo host.
- **Health check failing**: `demo_branding` must be installed — it
  provides `/api/health`.
