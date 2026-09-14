# Demo Script

For a live presentation, once the "golden" demo database exists (see
`DEMO_GUIDE.md` step 1-2). Run through in order; each step assumes the
previous ones' records still exist in the database.

---

### Step 1 — Login & environment identity
- **Screen**: Login page
- **Action**: Show the "DEMO ENVIRONMENT" banner and log in as `demo.admin`
- **Feature demonstrated**: Centralized demo branding (`demo_branding`)
- **Expected result**: Banner reads the configured application name; standard Odoo home screen loads
- **Business value**: Confidence the audience is looking at a safe demo, not production
- **Demo account**: `demo.admin`
- **Required demo data**: none

### Step 2 — Organization & roles
- **Screen**: Settings > Users & Companies > Users
- **Action**: Open two or three of the seven demo accounts, show their assigned groups
- **Feature demonstrated**: Role-based access control (`ROLE_MATRIX.md`)
- **Expected result**: Each account's groups match the documented matrix
- **Business value**: Segregation of duties is enforced by the system, not by policy alone
- **Demo account**: `demo.admin`
- **Required demo data**: seeded users

### Step 3 — Purchase requisition & committee
- **Screen**: Purchase > Requisitions (menu under the unified Diwan menu)
- **Action**: Create a requisition for "Office Laptop" against "Supplier One", form a procurement committee
- **Feature demonstrated**: `demo_gov_scm_requisition`, `procurement_committee`, automatic budget commitment
- **Expected result**: Requisition auto-creates a budget commitment record; committee is formed with chairman/member/secretary roles
- **Business value**: Budget control is enforced before spend commitment, per Law 182/2018 workflow
- **Demo account**: `demo.contracts_officer` → `demo.contracts_manager`
- **Required demo data**: `product_office_laptop`, `partner_vendor_1`

### Step 4 — Adjudication & award
- **Screen**: Procurement > Adjudication
- **Action**: Open technical envelope, adjudicate, open financial envelope, adjudicate, award
- **Feature demonstrated**: `procurement_adjudication` dual-envelope state machine
- **Expected result**: State progresses draft → technical_open → financial_open → adjudicated → awarded → po_created; a Purchase Order is auto-created
- **Business value**: Auditable, tamper-evident procurement decision trail
- **Demo account**: `demo.adjudication_chairman`
- **Required demo data**: requisition from Step 3

### Step 5 — Goods receipt & custody
- **Screen**: Inventory > Addition Permits, then Custody
- **Action**: Receive the PO (inspection report + Form 1), then assign custody of the laptop to a demo employee
- **Feature demonstrated**: `stock_addition_permit`, `l10n_eg_custody` (Form 193)
- **Expected result**: Two-step receipt produces a signed-off Form 1; custody record links the asset to an employee with full chatter audit trail
- **Business value**: GAFI-auditable chain of custody for durable government assets
- **Demo account**: `demo.warehouse_manager`
- **Required demo data**: awarded PO from Step 4

### Step 6 — Auction
- **Screen**: Auctions
- **Action**: Create an auction request for a surplus item, record bids, award (sale path)
- **Feature demonstrated**: `l10n_eg_auction`
- **Expected result**: Winning bid auto-creates a `sale.order`; award notification prints as Arabic RTL PDF with the demo seal
- **Business value**: Transparent, documented disposal of surplus government assets
- **Demo account**: `demo.contracts_manager`
- **Required demo data**: any seeded item

### Step 7 — Finance & reporting
- **Screen**: Accounting > Government Reports
- **Action**: Print a trial balance and a general ledger PDF
- **Feature demonstrated**: `demo_gov_gl_reports`, shared report layout
- **Expected result**: PDF shows correct RTL formatting, generic Demo Edition branding, real numbers from Steps 3-6
- **Business value**: Statutory-format reporting, ready for audit, safe to show externally
- **Demo account**: `demo.admin`
- **Required demo data**: transactions from prior steps

### Step 8 — Executive dashboard
- **Screen**: Dashboard
- **Action**: Open the executive KPI dashboard
- **Feature demonstrated**: `demo_gov_dashboard`
- **Expected result**: KPIs (active requisitions, pending approvals, custody items, auction value) reflect Steps 3-6, not zeros
- **Business value**: Real-time visibility for leadership
- **Demo account**: `demo.admin`
- **Required demo data**: transactions from prior steps
- **Note**: this module has one known pre-existing display defect — see `KNOWN_LIMITATIONS.md` — verify it doesn't affect the KPI cards you plan to show before presenting

### Step 9 — Permission boundary (optional, for a technical audience)
- **Screen**: any warehouse-manager-only menu
- **Action**: Log in as `demo.inspector` and attempt it
- **Feature demonstrated**: enforced `res.groups` access control
- **Expected result**: Access denied
- **Business value**: Proves RBAC is real, not cosmetic
- **Demo account**: `demo.inspector`
- **Required demo data**: none

### Step 10 — Logout
- Standard Odoo logout, end of session.
