# REQUEST FOR PROPOSAL (RFP)
## Enterprise Resource Planning (ERP) System
### Finance & Supply Chain — Egyptian Government Entity

---

| | |
|---|---|
| **Issuing Authority** | General Diwan — ............ Governorate |
| **Document Reference** | RFP-ERP-2026-001 |
| **Issue Date** | May 2026 |
| **Submission Deadline** | ............/............/2026 |
| **Contact** | IT Department — ............ Governorate |

---

## Confidentiality Notice

This document is confidential and intended solely for pre-qualified vendors. Reproduction or distribution without prior written consent from the issuing authority is strictly prohibited.

---

# SECTION 1 — INTRODUCTION

## 1.1 Background

The General Diwan of ............ Governorate is the executive body responsible for managing financial affairs, administrative operations, government procurement, supply chain, and treasury functions in compliance with Egyptian financial regulations, Ministry of Finance directives, and Central Auditing Organization (CAO) standards.

The organization currently operates with manual and semi-automated workflows that limit transparency, efficiency, and real-time financial visibility. The Diwan seeks to implement a fully integrated, Arabic-first ERP system to modernize operations and enforce compliance.

## 1.2 Purpose of this RFP

This RFP invites qualified vendors to submit **technical and financial proposals** for the supply, installation, customization, training, and support of a fully integrated ERP system based on **Odoo 17** (Community or Enterprise Edition), covering:

- Government Financial Management
- Supply Chain & Procurement
- Warehouse & Inventory Management
- Executive Reporting & Dashboard

## 1.3 Project Scale

| Parameter | Value |
|-----------|-------|
| Number of Named Users | **40 Users** |
| Concurrent Users (estimated) | 20–25 |
| Number of Entities / Branches | 1 (central) |
| Deployment Model | On-Premise (preferred) / Private Cloud |
| Primary Language | Arabic (RTL) |
| Go-Live Target | Within 5 months from contract signing |

---

# SECTION 2 — SCOPE OF WORK

## 2.1 In-Scope Modules

The following functional modules are **mandatory** unless marked *(Optional)*:

### 2.1.1 Financial Management

| Module | Description |
|--------|-------------|
| **General Ledger** | Multi-level chart of accounts, Arabic journal entries, fiscal year July–June |
| **Daftar 55 (دفتر 55 ع.ح)** | Government daily accounting register — Ministry of Finance format |
| **Daily Journal 224 (يومية 224)** | Government payment journal — Ministry of Finance format |
| **Subsidiary Books Engine** | 29 government subsidiary books: Forms 29/39/71/78 (debit/credit, current/statutory accounts, treasury, assets, penalties, auctions) with legal sequential numbering and monthly carry-forward |
| **Budget Planning & Control** | Budget by Chapter/Section/Line-item; real-time commitment tracking; over-budget alerts |
| **Commitments** | Pre-expenditure commitment registration linked to budget |
| **Treasury & Cash Books** | Multi-fund cash management; government cash book formats |
| **Cash Transfers** | Inter-fund transfers with full audit trail |
| **Cheque Management** | Issue, receive, collect, bounce tracking |
| **Staff & Vendor Advances** | Multiple advance types, settlement tracking |
| **Insurance & Deposits** | Deposit receipt/release/forfeiture linked to vendor contracts |
| **Penalties & Violations** | Administrative violation register, appeals workflow |
| **Special Funds** | Petty cash and restricted fund management |
| **GL Reports** | General ledger report, trial balance, aging reports |
| **Payment Matching** | Match payments to invoices automatically |

### 2.1.2 Payment Order — Form 50 (استمارة 50 ع.ح)

| Feature | Requirement |
|---------|-------------|
| Electronic payment order creation | Mandatory |
| Print Form 50 on pre-printed official background | Mandatory |
| Pixel-accurate field positioning on physical form | Mandatory |
| Multi-invoice table per payment order | Mandatory |
| Auto-calculation of deductions (tax, stamps, additional) | Mandatory |
| Net amount + Arabic text amount (تفقيط) | Mandatory |
| Budget classification (Chapter/Section/Line) | Mandatory |
| Multi-level approval workflow | Mandatory |
| Form 69 (Leave Request) printing | Optional |
| Form 75 (Disbursement Schedule) printing | Optional |

### 2.1.3 Government Procurement

| Module | Description |
|--------|-------------|
| **Purchase Requisitions** | Multi-level requisition with approval matrix |
| **Procurement Committee** | Committee formation, meeting minutes, decisions |
| **Bidding & Tendering** | Tender sessions, bid evaluation |
| **Adjudication** | Award decisions, vendor notifications |
| **Purchase Orders** | PO linked to budget; receiving workflow |
| **ETA Electronic Invoice** | Full B2B/B2G integration with Egyptian Tax Authority |

### 2.1.4 Warehouse & Inventory

| Module | Description |
|--------|-------------|
| **Multi-Warehouse Management** | Multiple stores/locations |
| **Addition Permits** | Goods receipt with official permits |
| **Issue / Return / Transfer Permits** | Controlled stock movements |
| **Annual Stocktaking** | Periodic physical count with variance reporting |
| **Inventory Revaluation** | FIFO/Average costing revaluation |
| **Stock-Finance Bridge** | Automatic journal entries for stock movements |

### 2.1.5 Fixed Assets

| Module | Description |
|--------|-------------|
| Asset Register | Full asset record with categories |
| Depreciation | Automatic (Straight-Line / Declining Balance) |
| Asset Disposal | Write-off / sale workflows |
| Budget Integration | Depreciation entries linked to budget |

### 2.1.6 Reporting & Executive Dashboard

| Report | Description |
|--------|-------------|
| **Executive Dashboard** | Real-time KPIs — finance, procurement, inventory |
| **Budget Execution Report** | Planned vs. actual by classification |
| **General Ledger Report (Arabic)** | Full ledger per account |
| **Aging Report** | Receivables & payables aging |
| **Tax XML Export** | Export for Egyptian Tax Authority |
| **Auctions & Government Property** | *(Optional)* |
| **Custody Management** | Government custody tracking |

---

# SECTION 3 — TECHNICAL REQUIREMENTS

## 3.1 Server Infrastructure (On-Premise)

### Production Server

| Specification | Minimum Requirement |
|--------------|-------------------|
| CPU | Intel Xeon / AMD EPYC — 16 Cores / 32 Threads |
| RAM | 64 GB DDR4 ECC |
| OS Storage | 2 × 480 GB SSD (RAID 1) |
| Data Storage | 4 × 2 TB NVMe SSD (RAID 10) |
| Network | 2 × 10 Gbps Ethernet (Bonding/LACP) |
| Power Supply | Redundant PSU (2 × 800W) |
| Operating System | Ubuntu Server 22.04 LTS |

### Backup / DR Server

| Specification | Minimum Requirement |
|--------------|-------------------|
| CPU | 8 Cores |
| RAM | 32 GB |
| Storage | 8 TB NAS (RAID 6) |
| Network | 1 Gbps |
| Location | Physically separate from production |

### Staging / Test Server

| Specification | Minimum Requirement |
|--------------|-------------------|
| CPU | 8 Cores |
| RAM | 32 GB |
| Storage | 1 TB SSD |

## 3.2 Network & Security Infrastructure

| Component | Requirement |
|-----------|------------|
| Firewall | Enterprise-grade (Fortinet / Palo Alto / pfSense) |
| Load Balancer | HAProxy or Nginx |
| SSL Certificate | Valid SSL/TLS (Let's Encrypt or CA-signed) |
| VPN | Remote admin access (WireGuard / OpenVPN) |
| Redundant ISP | Secondary 4G/Fiber failover link |
| IDS/IPS | Intrusion detection system |
| WAF | Web Application Firewall |

## 3.3 Software Stack

| Component | Required Version |
|-----------|----------------|
| Odoo | 17.0 (Community or Enterprise) |
| PostgreSQL | 15 or later |
| Python | 3.10+ |
| Nginx | Latest stable |
| Docker / Compose | Latest (if containerized) |
| wkhtmltopdf | 0.12.6 (PDF printing) |
| Redis | 7.x (session / cache) |

## 3.4 Client Workstations (Provided by Client — Minimum Spec)

| Specification | Minimum |
|--------------|---------|
| CPU | Intel Core i5 (8th Gen+) |
| RAM | 8 GB |
| Storage | 256 GB SSD |
| Display | 21" Full HD |
| Browser | Chrome 120+ / Firefox 120+ / Edge 120+ |
| Printer | Laser A4 (for government forms) |

## 3.5 UPS & Power

| Component | Requirement |
|-----------|------------|
| Server UPS | APC / Eaton — 10 KVA minimum |
| Runtime | 30 minutes minimum under full load |
| Generator | Required for large facilities (Bidder to confirm) |

---

# SECTION 4 — NON-FUNCTIONAL REQUIREMENTS

## 4.1 Performance

| Metric | Requirement |
|--------|------------|
| Page response time | < 3 seconds (90th percentile) |
| System availability (Uptime) | ≥ 99.5% |
| Simultaneous users | 40 named / 25 concurrent |
| Recovery Time Objective (RTO) | < 4 hours |
| Recovery Point Objective (RPO) | < 24 hours |

## 4.2 Security & Access Control

| Requirement | Detail |
|------------|--------|
| Authentication | Username + Password + optional 2FA |
| Authorization | Role-Based Access Control (RBAC) |
| Audit Trail | Full action log for every transaction |
| Data Encryption | AES-256 at rest; TLS 1.3 in transit |
| Password Policy | Complexity rules + expiry |
| Session Management | Auto-timeout after inactivity |

## 4.3 Backup Policy

| Parameter | Requirement |
|-----------|------------|
| Daily backup | Full DB + filestore + custom addons |
| Weekly / Monthly | Full backup with offsite copy |
| Retention | 90 days (daily) / 12 months (monthly) |
| Restore testing | Quarterly documented restore test |
| Backup format | pg_dump -Fc (restorable via pg_restore) |

## 4.4 Arabic & Localization Requirements

| Requirement | Detail |
|------------|--------|
| Text direction | Full RTL (Right-to-Left) |
| Arabic fonts | Amiri / Cairo (embedded in PDF reports) |
| Numeral support | Arabic-Indic (٠١٢٣٤٥٦٧٨٩) where required |
| Government forms | Pixel-accurate match to MoF official forms |
| Fiscal calendar | July 1 – June 30 (Egyptian government year) |
| Date formats | DD-MM-YYYY and Hijri where applicable |

---

# SECTION 5 — IMPLEMENTATION REQUIREMENTS

## 5.1 Proposed Project Phases

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1 — Infrastructure & Base Install | Weeks 1–4 | Servers configured, Odoo installed, environments ready |
| Phase 2 — Customization & Development | Weeks 5–10 | All modules coded, tested in staging |
| Phase 3 — Data Migration & UAT | Weeks 11–14 | Data imported, user acceptance testing completed |
| Phase 4 — Training | Weeks 15–16 | All 40 users trained |
| Phase 5 — Pilot Go-Live | Week 17 | Parallel run with existing system |
| Phase 6 — Full Go-Live | Week 18 | Production cutover |

## 5.2 Data Migration Requirements

| Data Type | Source | Requirement |
|-----------|--------|------------|
| Chart of Accounts | Existing system / Excel | Full import |
| Opening Balances | As of go-live date | All accounts |
| Vendor / Supplier Master | Existing records | Complete |
| Fixed Assets Register | Existing records | With accumulated depreciation |
| Inventory Opening Stock | Physical count | Quantities + values |

## 5.3 Training Requirements

| Group | Required Hours | Format |
|-------|--------------|--------|
| End Users (Finance) | 16 hrs/module | Classroom + recorded video |
| End Users (Procurement) | 16 hrs/module | Classroom + recorded video |
| System Supervisors | 40 hours | Classroom |
| IT Administrators | 24 hours | Classroom + hands-on |
| Senior Management | 4 hours (executive summary) | Presentation |

---

# SECTION 6 — SUPPORT & MAINTENANCE

## 6.1 Service Level Agreement (SLA)

| Priority | Definition | Response Time | Resolution Time |
|----------|-----------|--------------|----------------|
| **P1 — Critical** | System completely down | 1 hour | 4 hours |
| **P2 — High** | Core function unavailable | 4 hours | 24 hours |
| **P3 — Medium** | Partial functionality issue | 8 hours | 72 hours |
| **P4 — Low** | Minor issue / enhancement request | 24 hours | 1 week |

## 6.2 Maintenance Services (3-Year Contract)

- Monthly security patches and updates
- Minor version upgrades within Odoo 17.x
- Performance monitoring and capacity reporting
- Supervised automated backup with quarterly restore testing
- Monthly system health reports
- Phone + email support during official working hours
- On-site visits: minimum 2 per year (or as needed for P1/P2)

---

# SECTION 7 — PROPOSAL REQUIREMENTS

## 7.1 Required Documents

Vendors must submit all of the following:

| # | Document | Format |
|---|---------|--------|
| 1 | Technical Proposal | PDF |
| 2 | Project Plan with Gantt Chart | PDF / MS Project |
| 3 | Team CVs and Certifications | PDF |
| 4 | References: minimum 3 government ERP projects | PDF |
| 5 | **Financial Proposal** (sealed envelope) | PDF |
| 6 | Company registration and tax card | PDF |
| 7 | Odoo Partnership certificate (if applicable) | PDF |
| 8 | Bank guarantee / bid bond | Original |

## 7.2 Pre-Qualification Criteria

| Criterion | Minimum |
|-----------|---------|
| Years of Odoo experience | 3 years |
| Completed government ERP projects | 3 projects |
| Technical staff | 10 FTEs minimum |
| Odoo Partner status | Preferred |
| Valid commercial registration | Mandatory |
| Valid tax registration | Mandatory |

## 7.3 Evaluation Criteria

| Criterion | Weight |
|-----------|--------|
| Technical solution adequacy & completeness | 35% |
| Team experience & project references | 25% |
| Implementation plan & training quality | 15% |
| Support plan & SLA commitment | 15% |
| Total cost of ownership (5 years) | 10% |

---

# SECTION 8 — FINANCIAL PROPOSAL STRUCTURE

Vendors must provide a detailed cost breakdown covering:

| Item | Required |
|------|---------|
| Odoo license (if Enterprise) | Per-user annual cost |
| Implementation & customization | Fixed price per module |
| Infrastructure (servers, network, UPS) | Itemized |
| Data migration | Fixed price |
| Training | Per session / total |
| Year 1 support & maintenance | Annual |
| Year 2 support & maintenance | Annual |
| Year 3 support & maintenance | Annual |
| **Total 3-Year Cost of Ownership** | **Summary line** |

*Note: All prices must be quoted in Egyptian Pounds (EGP), inclusive of all applicable taxes.*

---

# SECTION 9 — GENERAL TERMS & CONDITIONS

## 9.1 IP & Data Ownership

- All data remains the exclusive property of the Governorate Diwan
- Full source code of all customizations must be delivered upon project completion
- Vendor may not retain access to production systems after contract expiry without written consent

## 9.2 Penalties

| Event | Penalty |
|-------|---------|
| Delivery delay | 1% of contract value per week (max 10%) |
| SLA breach | Pro-rata deduction from monthly maintenance fee |
| Data breach due to vendor negligence | As per Egyptian Cybercrime Law |

## 9.3 Warranty

- Minimum 12-month warranty from official go-live date
- All software defects corrected at no additional cost during warranty period
- Warranty does not cover issues resulting from unauthorized client modifications

## 9.4 Governing Law

This contract is governed by the laws of the Arab Republic of Egypt, including regulations of the Central Auditing Organization (CAO) and Ministry of Finance procurement rules.

---

# SECTION 10 — SUBMISSION & CONTACT

## 10.1 Submission Instructions

- Technical and financial proposals must be submitted in **separate sealed envelopes**
- Both envelopes to be placed in a single outer envelope clearly marked:
  `"ERP System RFP — RFP-ERP-2026-001 — DO NOT OPEN"`
- Electronic copy (USB or email) acceptable in addition to hard copy

## 10.2 Contact Information

```
Department       : Information Technology Department
Organization     : General Diwan — ............ Governorate
Address          : ............................................
Phone            : ............................................
Email            : ............................................
Working Hours    : Sunday–Thursday, 09:00–15:00
```

---

## Appendix A — Module Summary Checklist

| Module | Mandatory | Optional |
|--------|-----------|---------|
| General Ledger (Daftar 55 / Journal 224) | ✓ | |
| Subsidiary Books (29 government books) | ✓ | |
| Budget Planning & Commitments | ✓ | |
| Payment Order — Form 50 | ✓ | |
| Treasury & Cash Books | ✓ | |
| Cheque Management | ✓ | |
| Advances & Deposits | ✓ | |
| Penalties | ✓ | |
| Procurement (Requisition → PO) | ✓ | |
| Procurement Committee & Tendering | ✓ | |
| ETA Electronic Invoice | ✓ | |
| Warehouse & Inventory | ✓ | |
| Fixed Assets | ✓ | |
| Executive Dashboard | ✓ | |
| GL & Financial Reports | ✓ | |
| Form 69 / Form 75 printing | | ✓ |
| Auctions & Government Property | | ✓ |
| Intercompany Recharge | | ✓ |

---

*Document Version: 1.0 — May 2026*
*Prepared by: General Diwan — ............ Governorate*
*Based on implemented Odoo 17 system requirements*
