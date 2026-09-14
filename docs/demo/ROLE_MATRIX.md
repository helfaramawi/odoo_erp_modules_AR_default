# Role Matrix — Demo Accounts

Seven demo accounts ship with the Demo Edition (see `DEMO_DATA.md` for
the full list with logins). Their Odoo security groups are taken as-is
from the production module design (`l10n_eg_custody/data/demo_users.xml`)
— only the account identity was anonymized, not the permission model.

| Role (login) | Custody | Procurement Committee | Adjudication | Auction | Purchase | Stock | System Admin |
|---|---|---|---|---|---|---|---|
| `demo.admin` (Director General) | Manager | Director | Director | Manager | Manager | Manager | Yes |
| `demo.contracts_manager` | — | Manager | Director | Manager | Manager | User | No |
| `demo.contracts_officer` | — | User | Member | User | User | User | No |
| `demo.adjudication_chairman` | — | User | Chairman | — | User | User | No |
| `demo.warehouse_manager` | Manager | — | — | — | User | Manager | No |
| `demo.storekeeper` | User | — | — | — | — | User | No |
| `demo.inspector` | — | — | — | — | — | User | No |

Legend: "Manager"/"Director"/"Chairman"/"User"/"Member" are the actual
Odoo security group labels each module defines (e.g.
`l10n_eg_custody.group_custody_manager`,
`procurement_adjudication.group_adjudication_chairman`). "—" means the
account holds no group in that module and cannot access its menus.

## What this demonstrates

- **Segregation of duties** in adjudication: `demo.adjudication_chairman`
  can chair the adjudication committee but is only a plain `purchase`
  user otherwise — cannot unilaterally create/approve purchase orders
  outside that role.
- **Warehouse chain of custody**: `demo.storekeeper` (custody user) and
  `demo.inspector` (no custody access at all) are deliberately narrower
  than `demo.warehouse_manager`, so a demo can show a permission denial
  by logging in as the storekeeper and attempting a manager-only action.
- **`demo.admin`** is intentionally over-privileged (mirrors the
  production "Director General" account) — use it only to show
  administration screens, not as the default demo login for a workflow
  walkthrough (use the role-specific account instead, so the audience
  sees real access control, not an admin bypassing it).

## Not independently re-verified

This matrix reflects what each module's `security/*.xml` and the seed
data's `groups_id` assignments declare — it was read from source, not
exercised by actually logging in as each account (no live instance
available). Before a real demo, log in once as each account and confirm
the menus shown match this table — see `DEMO_SCRIPT.md`.
