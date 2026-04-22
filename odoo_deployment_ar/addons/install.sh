#!/bin/bash
# ============================================================
# Port Said Governorate — Odoo 17 SC Modules Install Script
# Usage: ./install.sh <database_name> [odoo_conf_path]
# ============================================================

DB=${1:-"portsaid_sc"}
CONF=${2:-"/etc/odoo/odoo.conf"}
ODOO_BIN=${ODOO_BIN:-"python3 /opt/odoo/odoo-bin"}
ADDONS_DEST=${ADDONS_DEST:-"/opt/odoo/custom_addons"}

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[$(date +%H:%M:%S)] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARN] $1${NC}"; }
err()  { echo -e "${RED}[ERROR] $1${NC}"; exit 1; }

log "=== Port Said SC Modules — Deployment ==="
log "Database: $DB"
log "Config:   $CONF"
log "Addons:   $ADDONS_DEST"
echo ""

# 1. Copy modules
log "Copying modules to $ADDONS_DEST ..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
for mod in procurement_committee l10n_eg_custody stock_addition_permit \
           stock_stocktaking_eg procurement_adjudication l10n_eg_auction; do
    src="$SCRIPT_DIR/$mod"
    if [ -d "$src" ]; then
        cp -r "$src" "$ADDONS_DEST/"
        log "  Copied: $mod"
    else
        err "Module directory not found: $src"
    fi
done

# 2. Restart Odoo to pick up new addons path
log "Restarting Odoo service ..."
if systemctl is-active --quiet odoo 2>/dev/null; then
    sudo systemctl restart odoo
    sleep 4
    log "  Odoo restarted"
else
    warn "  Odoo service not found via systemctl — restart manually if needed"
fi

# 3. Install in dependency order
MODULES=(
    "procurement_committee"
    "l10n_eg_custody"
    "stock_addition_permit"
    "stock_stocktaking_eg"
    "procurement_adjudication"
    "l10n_eg_auction"
)

for mod in "${MODULES[@]}"; do
    log "Installing: $mod ..."
    $ODOO_BIN -c "$CONF" -d "$DB" -i "$mod" --stop-after-init 2>&1 | \
        grep -E "(INFO|WARNING|ERROR|installed|updated)" | tail -5
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "  ✓ $mod installed"
    else
        err "  ✗ Failed to install $mod — check Odoo logs"
    fi
done

echo ""
log "============================================"
log "ALL 6 MODULES INSTALLED SUCCESSFULLY"
log "============================================"
echo ""
log "Post-install checklist:"
echo "  [ ] Assign 'أمين المخزن' group to warehouse staff"
echo "  [ ] Assign 'مدير العهد' group to warehouse managers"
echo "  [ ] Configure warehouse locations in Inventory → Configuration"
echo "  [ ] Verify Arabic font (Cairo/Amiri) is installed for PDF reports"
echo "  [ ] Test Form 193 print from l10n_eg_custody"
echo "  [ ] Test Form 6 print from stock_stocktaking_eg"
echo "  [ ] Run one test auction (sale path) to verify sales order creation"
echo "  [ ] Run one test auction (lease path) to verify payment schedule"
