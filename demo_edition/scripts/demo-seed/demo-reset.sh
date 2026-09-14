#!/bin/bash
# ============================================================
# Demo Edition — safe database reset
#
# Drops and recreates the DEMO database only, then reinstalls the
# Demo Edition modules with fresh seed data. Refuses to run unless
# APP_ENV=demo is explicitly set, and refuses to run against any
# database name that doesn't start with "demo_" — this is the
# explicit safeguard required so this script can never be pointed
# at a production database by accident.
#
# Usage: APP_ENV=demo ./demo-reset.sh [db_name] [odoo_conf_path]
# ============================================================
set -euo pipefail

DB=${1:-"demo_gov_erp"}
CONF=${2:-"/etc/odoo/odoo-demo.conf"}
ODOO_BIN=${ODOO_BIN:-"python3 /opt/odoo/odoo-bin"}
ADDONS_PATH=${ADDONS_PATH:-"/opt/odoo/demo_addons"}

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date +%H:%M:%S)] $1${NC}"; }
err()  { echo -e "${RED}[ERROR] $1${NC}"; exit 1; }

# ---- Safeguards: this must never be able to touch production ----
if [ "${APP_ENV:-}" != "demo" ]; then
    err "Refusing to run: APP_ENV must be set to 'demo' (got '${APP_ENV:-<unset>}')."
fi
case "$DB" in
    demo_*) ;;
    *) err "Refusing to run: database name '$DB' does not start with 'demo_'." ;;
esac

log "=== Demo Edition — Database Reset ==="
log "Database: $DB"
log "Config:   $CONF"
echo ""

log "Dropping existing demo database (if present) ..."
dropdb --if-exists "$DB"

log "Creating fresh demo database ..."
createdb "$DB"

MODULES="demo_branding,demo_gov_seed_data,l10n_eg_custody,l10n_eg_auction,procurement_committee,procurement_adjudication,stock_addition_permit,stock_stocktaking_eg"

log "Installing Demo Edition modules: $MODULES ..."
$ODOO_BIN -c "$CONF" -d "$DB" --addons-path="$ADDONS_PATH" -i "$MODULES" --stop-after-init

log "============================================"
log "Demo database '$DB' reset and seeded."
log "============================================"
log "Login with any demo.* account (see docs/demo/DEMO_GUIDE.md)."
log "Set DEMO_USERS_PASSWORD before running this script to control the shared demo password."
