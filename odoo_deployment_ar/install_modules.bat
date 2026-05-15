@echo off
echo ============================================
echo  Installing all custom Odoo modules
echo ============================================

echo.
echo [1/3] Stopping Odoo app...
docker stop odoo17_app

echo.
echo [2/3] Installing all modules (this may take 10-20 minutes)...
docker start odoo17_app
timeout /t 10 /nobreak > nul

docker exec odoo17_app odoo -c /etc/odoo/odoo.conf -d odoo17_db ^
  -i port_said_menu,^
c1_purchase_approval_matrix,^
c2_batch_posting,^
c3_aging_report,^
c4_payment_matching,^
c5_financial_dimensions,^
c6_cost_centre,^
c7_credit_bureau,^
c8_contract_pricing,^
c10_inventory_revaluation,^
c11_budget_alert,^
c12_intercompany_recharge,^
c13_tax_xml_export,^
general_ledger_ar,^
l10n_eg_auction,^
l10n_eg_custody,^
l10n_eg_eta_invoice,^
portsaid_dashboard,^
port_said_acct_reports,^
port_said_advances,^
port_said_budget_planning,^
port_said_cash_books,^
port_said_cash_transfers,^
port_said_cheques,^
port_said_commitment,^
port_said_daftar224,^
port_said_daftar55,^
port_said_dossier,^
port_said_fixed_assets,^
port_said_form50_print,^
port_said_form69,^
port_said_form75,^
port_said_gl_reports,^
port_said_insurance_subsidiary,^
port_said_penalties,^
port_said_reports,^
port_said_revenue_books,^
port_said_scm_issue,^
port_said_scm_purchase_bridge,^
port_said_scm_requisition,^
port_said_scm_warehouse,^
port_said_special_funds,^
port_said_stock_finance_bridge,^
port_said_subsidiary_books,^
procurement_adjudication,^
procurement_committee,^
stock_addition_permit,^
stock_stocktaking_eg ^
  --stop-after-init

echo.
echo [3/3] Restarting Odoo...
docker compose restart odoo

echo.
echo ============================================
echo  Done! Open http://localhost:8069
echo ============================================
pause