# Port Said Governorate — Odoo 17 Supply Chain Custom Modules
## الديوان العام لمحافظة بورسعيد — وحدات سلسلة التوريد المخصصة

**Vendor:** Paradise AI Solutions  
**Client:** Port Said Governorate General Diwan  
**System:** Odoo 17 (Community or Enterprise)  
**Regulatory Basis:** Law 182/2018, Min. Finance Decree 692/2019, Government Warehouse Regulations, GAFI

---

## Module Index

| # | Module Technical Name | Arabic Name | FR Coverage | Priority |
|---|---|---|---|---|
| 1 | `l10n_eg_custody` | إدارة العهد | FR-I4, FR-I7 | CRITICAL (GAFI-audited) |
| 2 | `l10n_eg_auction` | المزايدات | FR-P9 | CRITICAL (full custom) |
| 3 | `procurement_committee` | تشكيل اللجان | FR-P2–P8 | HIGH (mixin for all tender types) |
| 4 | `stock_addition_permit` | إذن الإضافة | FR-I1 | HIGH |
| 5 | `stock_stocktaking_eg` | الجرد الحكومي | FR-I5, FR-I6 | HIGH |
| 6 | `procurement_adjudication` | البت الفني والمالي | FR-P2, P3, P8 | HIGH |

---

## Installation Order (MANDATORY — respect dependencies)

```
Step 1:  procurement_committee      (no custom deps — install first)
Step 2:  l10n_eg_custody            (depends: stock, hr, mail)
Step 3:  stock_addition_permit      (depends: stock, purchase)
Step 4:  stock_stocktaking_eg       (depends: stock, hr)
Step 5:  procurement_adjudication   (depends: purchase, procurement_committee)
Step 6:  l10n_eg_auction            (depends: purchase, sale, stock, account)
```

---

## Server Installation

### 1. Copy modules to addons path
```bash
# Copy all 6 module directories to your Odoo addons path
cp -r portsaid_sc_modules/* /opt/odoo/addons/

# Or if using a custom addons path:
cp -r portsaid_sc_modules/* /opt/odoo/custom_addons/
```

### 2. Update addons path in odoo.conf
```ini
[options]
addons_path = /opt/odoo/addons,/opt/odoo/custom_addons
```

### 3. Restart Odoo and update module list
```bash
sudo systemctl restart odoo
# Then in Odoo UI: Settings → Technical → Update Module List
```

### 4. Install in order (via UI or CLI)
```bash
# Via CLI (recommended for production):
cd /opt/odoo
python odoo-bin -c /etc/odoo/odoo.conf \
  -d YOUR_DATABASE \
  -i procurement_committee \
  --stop-after-init

python odoo-bin -c /etc/odoo/odoo.conf \
  -d YOUR_DATABASE \
  -i l10n_eg_custody \
  --stop-after-init

python odoo-bin -c /etc/odoo/odoo.conf \
  -d YOUR_DATABASE \
  -i stock_addition_permit,stock_stocktaking_eg \
  --stop-after-init

python odoo-bin -c /etc/odoo/odoo.conf \
  -d YOUR_DATABASE \
  -i procurement_adjudication \
  --stop-after-init

python odoo-bin -c /etc/odoo/odoo.conf \
  -d YOUR_DATABASE \
  -i l10n_eg_auction \
  --stop-after-init
```

---

## Module Details

### 1. `l10n_eg_custody` — إدارة العهد (FR-I4)

**Purpose:** Track government durable items (مستديم) assigned to employees via Form 193 (ع.ح). GAFI-audited annually.

**Key models:**
- `custody.assignment` — main custody record with full GAFI-required fields
- `custody.transfer` — transfer between employees with audit trail
- `stock.move` (extended) — auto-creates custody on دurable item issue

**GAFI Compliance:**
- `national_id` field on Form 193 is **mandatory** — system blocks confirmation without it
- All state changes logged via `mail.thread` chatter
- Form 193 Arabic RTL QWeb print with all required government fields

**Sequences:**
- Custody: `EHD/YYYY/00001`
- Transfer: `TEHD/YYYY/00001`

**After install — configure:**
1. Assign `إدارة العهد / أمين المخزن` group to warehouse staff
2. Assign `إدارة العهد / مدير العهد` group to warehouse managers

---

### 2. `l10n_eg_auction` — المزايدات (FR-P9)

**Purpose:** Full government auction management — two paths: Sale (auto sales order + stock) and Lease/Usufruct (contract with annual % increase + payment schedule).

**Key models:**
- `auction.request` — auction with state machine: draft→confirmed→session_open→bidding→awarded→done
- `auction.bid` — bidder records with accept/reject
- `auction.lease.contract` — lease contract with `annual_increase_pct`, payment schedule, grace period
- `payment.schedule.line` — individual installments with collection tracking

**Automatic behaviours:**
- On award (Sale path): auto-creates confirmed `sale.order`
- On award (Lease path): auto-creates `auction.lease.contract`
- `ir.cron` runs daily: marks overdue payments + applies annual increase on contract anniversary

**Sequences:**
- Auction: `MZD/YYYY/00001`
- Lease contract: `EQD/YYYY/00001`

---

### 3. `procurement_committee` — تشكيل اللجان (FR-P2–P8)

**Purpose:** Reusable committee formation module. Used by RFQ, PO, Contracting, and Auction.

**Key models:**
- `procurement.committee` — committee with type, members, formation decision reference
- `committee.member` — member with role: رئيس لجنة / عضو / أمين سر / خبير
- `procurement.committee.mixin` — AbstractModel mixin applied via `_inherit`

**Usage in your custom modules:**
```python
class YourTenderModel(models.Model):
    _name = 'your.tender'
    _inherit = ['your.tender', 'procurement.committee.mixin']
```
Then call `self._validate_committee()` before state transitions.

**Note:** FR-P7 (Sovereign entities) — set `has_committee = False` to bypass committee requirement.

**Sequence:** `LGN/YYYY/00001`

---

### 4. `stock_addition_permit` — إذن الإضافة (FR-I1)

**Purpose:** Mandatory two-step goods receipt per Government Warehouse Regulations.

**Flow:**
```
Supply Order received
    → Step 1: Preliminary Receipt (إيصال استلام مبدئي)
    → Inspection Report (محضر الفحص): reference_batch, test_group, qty, result
    → Step 2: إذن إضافة journal entry (auto-created on inspection approval)
    → Print Form 1 (نموذج 1 مخازن حكومية) — Arabic RTL
```

**Smart buttons** added to `stock.picking` form for quick navigation.

**Sequences:**
- Inspection: `FCH/YYYY/00001`
- Addition Permit: `IZN-IDA/YYYY/00001`

---

### 5. `stock_stocktaking_eg` — الجرد الحكومي (FR-I5, FR-I6)

**Purpose:** Government annual stocktaking with Form 6, surplus/deficit reporting, and slow-moving stock sale authorization.

**Key models:**
- `stock.stocktaking.session` — stocktaking session with committee, load from Odoo quants
- `stock.stocktaking.line` — per-item: system_qty, physical_qty, difference, value

**Reports (Arabic RTL):**
1. **نموذج 6 مخازن** — `action_print_form6` — full government stocktaking minutes
2. **كشف الزيادة والعجز** — `action_print_surplus_deficit` — colour-coded surplus/deficit summary
3. **بيان مخزون راكد** — slow-moving stock with تصريح بالبيع (sale authorization block)

**Workflow:** Load Stock → Count Items → Post → Validate (chairman sign-off) → Print Form 6

**Sequence:** `JRD/YYYY/00001`

---

### 6. `procurement_adjudication` — البت الفني والمالي (FR-P2, P3, P8)

**Purpose:** Dual-envelope adjudication per Law 182/2018. Technical envelope first, financial envelope second.

**State Machine:**
```
draft → technical_open → financial_open → adjudicated → awarded → po_created
```

**Key behaviours:**
- Technical evaluation per supplier (pass/fail/conditional)
- Financial comparison auto-selects lowest valid bid as winner
- `bid_vs_estimate` computed field shows % of bid vs estimated value
- On `action_create_po`: auto-creates `purchase.order` for the winning supplier

**Reports (Arabic RTL):**
1. **محضر البت الفني** — technical adjudication minutes A & B
2. **محضر البت المالي** — financial comparison + adjudication decision
3. **إخطار الترسية** — award notification letter

**Sequence:** `BT/YYYY/00001`

---

## Arabic Font for Reports

For best Arabic RTL rendering in QWeb PDF reports, install the Cairo or Amiri font:

```bash
sudo apt-get install fonts-arabeyes fonts-hosny-amiri
# Or for Cairo font:
pip install fonttools
```

In your Odoo paper format / report CSS, fonts are already referenced as:
```css
font-family: 'Cairo', 'Amiri', Arial, sans-serif;
```

---

## Security Groups Summary

| Module | Group | Access Level |
|---|---|---|
| l10n_eg_custody | أمين المخزن (group_custody_user) | Create/Edit custody records |
| l10n_eg_custody | مدير العهد (group_custody_manager) | Full access including delete |
| All purchase modules | purchase.group_purchase_user | Standard purchase user |
| All purchase modules | purchase.group_purchase_manager | Full purchase access |
| All stock modules | stock.group_stock_user | Standard stock user |
| All stock modules | stock.group_stock_manager | Full stock access |

---

## Tested With
- Odoo 17.0 Community
- Python 3.11
- PostgreSQL 15
- Ubuntu 22.04 LTS

---

## Support
Paradise AI Solutions  
133 El Showaifat (Al Amal) St., New Cairo, Cairo  
info@paradise-solutions.com
