# Known Limitations

Honest punch list. Nothing below was hidden or silently worked around.

## DEMO ENVIRONMENT banner covered Odoo's own top menu bar — fixed

**Problem**: `demo_branding`'s banner (`static/src/js/demo_banner.js`,
`static/src/css/demo_banner.css`) is `position: fixed; top: 0` so it
doesn't interfere with Odoo's own layout calculations, but nothing
reserved space for it — it just sat on top of whatever was already at
the top of the page, which is Odoo's own menu bar (company selector,
top app tabs). **Fixed**: after inserting the banner, JS now measures
its real rendered height (`offsetHeight`, not a hard-coded value,
since the banner text wraps to two lines on narrow screens) and sets
`body.style.paddingTop` to match, re-measuring on window resize since
wrapping can change the height. The banner still overlays nothing now
— the whole page is pushed down by exactly the banner's height.

## Apps page was a flat list of ~30 separate government modules — grouped

**Problem**: every `demo_gov_*` module (plus the closely related
`l10n_eg_auction`, `l10n_eg_custody`, `l10n_eg_eta_invoice`,
`procurement_committee`, `procurement_adjudication`,
`stock_addition_permit`, `stock_stocktaking_eg`, and
`general_ledger_ar`) either had no `category` set in its manifest, or
had a generic core category (`Accounting`, `Purchase`, `Inventory`)
shared with unrelated Odoo apps. In Settings → Apps, each module with
no category (or a category unique to it) got its own row in the
category sidebar — about 30 of them, one per module, with no grouping.

**Fixed**: every module in that list now sets
`'category': 'الخدمات الحكومية التجريبية/<subcategory>'`, using Odoo's
standard `Parent/Child` category-string convention. That puts all of
them under one parent group, **الخدمات الحكومية التجريبية** (Demo
Government Services), with four subcategories matching the site's real
functional areas:

- **الحسابات** (Accounts) — general ledger, all subsidiary/cash/bank
  books, budgets, advances, fixed assets, special funds, archiving,
  e-invoicing (`general_ledger_ar`, `demo_gov_subsidiary_books`,
  `demo_gov_cash_books`, `demo_gov_cash_transfers`, `demo_gov_cheques`,
  `demo_gov_revenue_books`, `demo_gov_insurance_subsidiary`,
  `demo_gov_commitment`, `demo_gov_daftar224`, `demo_gov_daftar55`,
  `demo_gov_advances`, `demo_gov_budget_planning`, `demo_gov_penalties`,
  `demo_gov_special_funds`, `demo_gov_dossier`, `demo_gov_form69`,
  `demo_gov_form75`, `demo_gov_fixed_assets`,
  `demo_gov_stock_finance_bridge`, `l10n_eg_eta_invoice`).
- **المشتريات** (Purchases) — committees, adjudication, requisitions,
  the purchase↔Form-50 bridge, auctions (`procurement_committee`,
  `procurement_adjudication`, `demo_gov_scm_requisition`,
  `demo_gov_scm_purchase_bridge`, `l10n_eg_auction`).
- **المخازن والمستودعات** (Warehouses & Stores) — inspection/warehouse
  forms, issue/return/transfer permits, addition permits, stocktaking,
  custody (`demo_gov_scm_warehouse`, `demo_gov_scm_issue`,
  `stock_addition_permit`, `stock_stocktaking_eg`, `l10n_eg_custody`).
- **التقارير الحكومية** (Government Reports) — the report wizard,
  trial-balance/statement reports, the GL report engine
  (`demo_gov_reports`, `demo_gov_acct_reports`, `demo_gov_gl_reports`).

`demo_branding` and `demo_gov_seed_data` are infrastructure/admin
modules, not a business function a demo user would pick from this
list, so they were deliberately left under their existing `Extra
Tools` category rather than folded into one of the four groups.
`demo_gov_dashboard` and `demo_gov_menu` are excluded from install
(see their own sections below) so their category doesn't affect the
live demo either way.

### Update: the `category` fix above only changed the Settings → Apps page — the real navigation sidebar needed the menu tree itself restructured

After the `category` fix shipped, live testing showed the actual
always-visible app-switcher/navigation sidebar (the persistent list of
apps on the side of every page, not the Settings → Apps management
kanban) was completely unaffected — it still listed ~13 separate
government apps with no grouping. That sidebar is populated purely
from root `ir.ui.menu` records (any `<menuitem>` with no `parent`),
which has nothing to do with a module's manifest `category` — the two
are unrelated Odoo mechanisms that happen to both live under the word
"Apps". The `category` fix above was still correct/worth keeping (it
does clean up the Settings → Apps management page), but it wasn't
what the user was pointing at, and didn't address the actual request.

Tracing every module's menu file found exactly **13 modules** that
each registered their own standalone root `<menuitem>` (no `parent`)
— the same 13 uncovered by the earlier "13 modules pointed at a broken
parent menu" fix further below, when their `parent="demo_gov_menu.…"`
references were stripped rather than repointed at a working parent.
Eleven more modules (`demo_gov_cash_books`, `demo_gov_cash_transfers`,
`demo_gov_cheques`, `demo_gov_revenue_books`,
`demo_gov_insurance_subsidiary`, `demo_gov_penalties`,
`demo_gov_budget_planning`, `demo_gov_gl_reports`,
`general_ledger_ar`, `l10n_eg_eta_invoice`) already nested correctly
under `demo_gov_subsidiary_books`'s root menu, so re-parenting that one
root menu carried all eleven of them along for free — they needed no
changes of their own.

**Fixed**: added one new file,
`demo_branding/views/gov_menu_root.xml`, defining a single root app
menu (`menu_gov_root`, "الخدمات الحكومية التجريبية") with four child
menus matching the same four functional groups as the category fix —
`menu_gov_accounts` (الحسابات), `menu_gov_purchases` (المشتريات),
`menu_gov_warehouses` (المخازن والمستودعات), and `menu_gov_reports`
(التقارير الحكومية). `demo_branding` is the natural home for this
since it's already the one module every part of the Demo Edition
treats as central infrastructure, and it depends on nothing beyond
`base`/`web` so there's no risk of a dependency cycle.

Each of the 13 modules' own root `<menuitem>` then got a `parent="demo_branding.menu_gov_<category>"`
attribute added (previously absent, which is exactly what made it a
standalone root app), and `demo_branding` was added to that module's
manifest `depends` so install/upgrade order guarantees the parent menu
exists first:

| Module | Category |
|---|---|
| `demo_gov_subsidiary_books`, `demo_gov_fixed_assets`, `demo_gov_form69`, `demo_gov_form75`, `demo_gov_special_funds` | الحسابات |
| `demo_gov_scm_requisition`, `procurement_adjudication` | المشتريات |
| `demo_gov_scm_issue`, `demo_gov_scm_warehouse`, `l10n_eg_custody`, `stock_addition_permit`, `stock_stocktaking_eg` | المخازن والمستودعات |
| `demo_gov_reports` | التقارير الحكومية |

Verified with a repo-wide AST trace of every `<menuitem>`'s parent
chain (resolving cross-module `module.xmlid` references) confirming
these 13 are the only remaining root nodes among the government-suite
modules, and a manifest dependency-graph cycle check confirming adding
`demo_branding` to all 13 introduces no circular dependency. Since
`demo_branding` was already installed before this change, picking it
up requires an actual module **upgrade** (`-u`), not just a restart —
plain source-file changes to an already-installed module's `data`
files aren't re-read until the module is reinstalled/upgraded.

**Follow-up bug caught by the live upgrade**: `demo_gov_scm_issue`'s
root `<menuitem>` also carried `web_icon="stock,static/description/icon.png"`
(it was previously used to control that menu's own app-drawer icon).
Odoo's RelaxNG schema only allows `web_icon` on a *root* menuitem (no
`parent`) — once it gained a `parent`, the combination failed XML
schema validation on upgrade
(`RELAXNG_ERR_EXTRACONTENT: Element odoo has extra content: record`,
reported against the file's first `<record>` rather than the actual
offending `<menuitem>` further down, which is why it initially looked
unrelated). Removed `web_icon` — the menu is nested now, so it doesn't
need its own app icon. Confirmed (via a repo-wide grep) this was the
only `web_icon` usage anywhere in `demo_edition/addons`, so none of
the other 12 re-parented modules have the same issue.

### Update: five apps under الحسابات had an action but no menu at all — fixed

**Problem**: reported by the user testing Settings → Apps: several
`demo_gov_*` modules already carried `'category': 'الخدمات الحكومية
التجريبية/الحسابات'` and each defined a working `ir.actions.act_window`,
but had **zero `<menuitem>`** anywhere in the module — not even a
standalone root one. `demo_gov_daftar55` (دفتر 55 ع.ح), `demo_gov_daftar224`
(دفتر 224 ع.ح), `demo_gov_dossier` (الاضابير/الفوليوهات), and
`demo_gov_commitment` (الارتباطات) had no `menuitem` in any file at all;
`demo_gov_advances` (السلف وخطابات الضمان) shipped a `views/menu.xml`
that was a literal empty `<odoo></odoo>` stub, already wired into the
manifest's `data` list but with nothing in it. Unlike the `demo_gov_menu`
breakage documented above, these five never had a working menu to begin
with in *either* edition — confirmed byte-for-byte identical (same empty
`menu.xml`, same total absence of any menu file for the other four) in
`odoo_deployment_ar/addons/port_said_daftar55`, `port_said_daftar224`,
`port_said_dossier`, `port_said_commitment`, `port_said_advances`, so
this is pre-existing in production too, not something anonymization
introduced. All five were correctly categorized on the Settings → Apps
page and would even show up as installed successfully, but there was
literally no click-path anywhere in the UI to reach the underlying "دفتر
55", "دفتر 224", "الاضابير", "الارتباطات", or "السلف/خطابات الضمان"
records — exactly the "app doesn't exist" symptom reported.
**Fixed** (in `demo_edition/` only, matching the "13 modules" fix's
scope — the equivalent production fix needs `port_said_menu`'s own gap
resolved first, same as documented above): added a `views/menu.xml` to
each of `demo_gov_daftar55`, `demo_gov_daftar224`, `demo_gov_dossier`,
and `demo_gov_commitment` (and filled in the empty stub in
`demo_gov_advances`), each with a `<menuitem>` parented directly at
`demo_branding.menu_gov_accounts` — the same root the already-working
`demo_gov_form69`/`demo_gov_form75`/`demo_gov_special_funds`/
`demo_gov_fixed_assets` menus use — with `demo_branding` added to each
module's manifest `depends` so the parent menu is guaranteed to exist at
install/upgrade time. `demo_gov_advances` additionally got its own root
menu (`menu_advances_root`) with four children (السلف الحكومية, السلف
المتأخرة, خطابات الضمان, خطابات تنتهي قريباً) since it exposes two
separate models (`demo_gov.advance`, `demo_gov.bank.guarantee`) each
with two actions. Verified with the same repo-wide manifest
dependency-graph cycle check and cross-module XML-ID reference scan used
for the earlier fixes above: 49 modules, zero cycles, zero missing
dependencies.

### Update: same audit repeated for المشتريات / المخازن والمستودعات / التقارير الحكومية

Requested as a direct follow-up once الحسابات was fixed: same check
(action exists, no `<menuitem>` reaches it — or reaches it only
partially) run against the other three category groups. A repo-wide
scan (`ir.actions.act_window` count vs `<menuitem>` count per module,
then read every module that didn't match 1:1) found four more real
instances, all confirmed pre-existing in the `port_said_*`/
`odoo_deployment_ar` production equivalents where a menu file exists at
all:

- **`procurement_committee`** (المشتريات, `application: True`) — the
  module's own `views/committee_views.xml` had a literal `<!-- Menus -->`
  placeholder comment where the menu was clearly meant to go, followed
  by nothing. `action_procurement_committee` (اللجان) was completely
  unreachable. **Fixed**: added the menuitem at the placeholder, parented
  at `demo_branding.menu_gov_purchases` (same root
  `procurement_adjudication`/`demo_gov_scm_requisition` already use),
  plus `demo_branding` to `depends`.
- **`l10n_eg_auction`** (المشتريات, `application: True`, "CRITICAL (full
  custom)" per the root README) — zero menu files anywhere despite two
  real actions (`action_auction_request` — المزادات,
  `action_auction_lease_contract` — عقود الإيجار). **Fixed**: new
  `views/menu.xml` with a root menu and both actions as children,
  parented at `demo_branding.menu_gov_purchases`; added `demo_branding`
  to `depends` and the new file to `data` (after both view files that
  define the actions it references).
- **`demo_gov_acct_reports`** (التقارير الحكومية) — `action_acct_report_wizard`
  (ميزان المراجعة / كشوف الحسابات) had no menu, unlike its sibling
  `demo_gov_gl_reports`/`demo_gov_reports` which do. **Fixed**: added the
  menuitem directly in `views/wizard_views.xml` (same file as the
  action), parented at `demo_branding.menu_gov_reports` like
  `demo_gov_reports`'s own entry; added `demo_branding` to `depends`.
- **`stock_addition_permit`** (المخازن والمستودعات, `application: True`) —
  had 2 actions but only 1 menuitem: `action_addition_permit` (أذونات
  الإضافة) was reachable, `action_inspection_report` (محاضر الفحص) was
  not, even though the module's own `help` text on the addition-permit
  action says the addition permit "يُنشأ تلقائياً بعد اعتماد محضر
  الفحص" (auto-created once the inspection report is approved) — i.e.
  the unreachable action was step 1 of the two-step workflow, so there
  was no way to start it from the UI. **Fixed**: added a sibling
  menuitem next to the existing one, same parent
  (`demo_branding.menu_gov_warehouses`), no manifest change needed (the
  action was already defined in the same file).

One more was found by the same scan but judged not a bug and left
alone: `demo_gov_scm_purchase_bridge` has zero actions and zero menus,
but it's a pure `purchase.order` form inheritance (auto-generates a
Form 50/Daftar 55 entry from an existing PO) with no standalone model
of its own to browse — nothing to link a menu to.

**Not exhaustive by design**: a handful of modules had *more* actions
than menu items (`demo_gov_scm_issue`: 8 vs 5, `l10n_eg_custody`: 7 vs
6 before this pass). In each case the gap turned out to be dead-code
duplicate action definitions (e.g. `demo_gov_scm_issue`'s menu file
redefines its own `..._2`-suffixed copies of actions already defined,
unused, in the model's own view file) rather than a genuinely
unreachable feature — confirmed by checking each orphaned action's
`res_model` against the ones already wired into a menu. One real
instance *was* found this way and fixed: `l10n_eg_custody`'s
`action_gafi_custody_audit` ("تقرير GAFI - أرباب العهد", the GAFI
compliance audit report the root README flags as
"CRITICAL (GAFI-audited)") had no menu entry — added as a sixth child
of `menu_ps_custody_main`, no manifest change needed. Its sibling
`action_custody_assignment` (a duplicate of the already-menu'd
`action_custody_assignment_main`) and `action_open_new_custody_wizard_main`
(an `ir.actions.server` bound to the list/kanban view's own gear-menu,
not meant to have a standalone menu item) were left alone — cleaning up
dead duplicate action definitions is a separate, lower-severity
cleanup, not an unreachable-app bug.

Verified with the same repo-wide dependency-cycle scan, extended to
also confirm every `<menuitem action="...">` reference resolves to a
real `ir.actions.*` record: 49 modules, zero cycles, zero missing
manifest dependencies, zero dangling action references.

### Update: same audit run against الدفاتر المساعدة and الفوليوهات themselves

Requested as a direct follow-up: check `demo_gov_subsidiary_books`
(الدفاتر المساعدة) and every "folio" concept in the repo
(`demo_gov_subsidiary_books`'s generic folio, `demo_gov_cash_books`'s
cash/bank folio, `demo_gov_insurance_subsidiary`'s insurance folio) for
the same "action with no click-path" bug, then extended the check to
every remaining module still categorized الحسابات that hadn't been
read line-by-line yet.

This pass used a stricter script instead of eyeballing counts: for
every `ir.actions.act_window` in each module, check whether it's
referenced by a `<menuitem action=...>`, a `<button action=...>`, or
`binding_model_id` (Odoo's own List-view gear-menu binding, which needs
no menu). A first run flagged `demo_gov_cash_books`'s five actions as
"orphaned" — a false positive: that module's `views/menu.xml` uses
single-quoted `action='...'` attributes throughout, which the first
version of the regex didn't match. Once fixed to accept both quote
styles, `demo_gov_subsidiary_books` (الفوليوهات، تعريف الدفاتر،
تصنيفات الحسابات — all 3), `demo_gov_cash_books` (فوليوهات النقدية
والبنك and its other 5 actions), and `demo_gov_insurance_subsidiary`
(الفوليوهات، الإيداعات، الحركات، توليد فولية، plus its two
`binding_model_id`-bound bulk-release wizards) all came back clean —
every action in all three is genuinely reachable.

One real orphan turned up in a module that hadn't been read yet:
**`demo_gov_stock_finance_bridge`**'s `action_bridge_log` (سجل القيود
المحاسبية — the audit log of accounting entries auto-posted from stock
movements, including failed/`error`-state ones). This one was worse
than a missing menuitem: `views/bridge_log_views.xml` — the file
defining the model's list view, its action, *and* the only place
`stock.finance.bridge.log` is referenced anywhere in the module's
XML — wasn't in the manifest's `data` list at all, so neither the view
nor the action were ever loaded into the database, and
`security/ir.model.access.csv` had no access-right row for the model
either (so even a direct URL to the model would have 403'd for every
non-superuser). **Fixed**: added `views/bridge_log_views.xml` to
`data` (after `journal_entry_views.xml`, before `menu.xml`, matching
load order for its dependents), added `access_bridge_log_user`/`_mgr`
rows to the access CSV (read-only for `account.group_account_user`,
full CRUD for `account.group_account_manager` — same pattern as the
module's other three models), and added a `menu_sfb_bridge_log`
menuitem under the existing `menu_sfb_root`.

The same script's disk-vs-manifest check (every `.xml` file under each
module's directory cross-referenced against that module's own `data`
list) found three more files never loaded, all pre-existing and
already accounted for elsewhere in this document: `demo_gov_menu`'s 8
missing view files (see its own section above — the module is excluded
from install), `demo_gov_dashboard/views/dashboard_template.xml` (the
malformed-XML module also excluded from install, see below), and the
dead `demo_gov_subsidiary_books/views/menu_____.xml` stub (superseded
by `views/menu.xml`, left in place rather than deleted since it was
out of scope for this pass and isn't loaded either way). A fourth,
`c1_purchase_approval_matrix/data/mail_template.xml`, belongs to a
generic (`category: Purchase`) module outside the government-suite
category set entirely and was left alone.

Re-verified with the same repo-wide cycle/dependency/dangling-action
scan: 49 modules, zero cycles, zero missing deps, zero dangling action
references.

## `demo_branding`'s Settings-page XML inheritance was wrong — fixed

**Problem**: the first version of `demo_branding` added its config fields
by XML-inheriting into `base_setup.res_config_settings_view_form` at
`//div[hasclass('settings')]`. That element doesn't exist in this Odoo
17 build's actual settings page markup — install failed with `Element
'<xpath expr="//div[hasclass('settings')]">' cannot be located in parent
view`.
**Root cause**: this was new code written for the Demo Edition (not
pre-existing), and inheriting into Odoo core's settings page layout
without a live instance to verify against was exactly the kind of risk
flagged as untested elsewhere in this document.
**Fixed**: replaced it with a plain, standalone `demo.branding.config`
model with its own form view and its own menu item under Settings (`base.menu_administration`)
— no inheritance into any Odoo core view, so nothing about Odoo's
internal settings page structure can break it. Branding values moved
from `ir.config_parameter` keys to fields on this model;
`self.env['demo.branding'].get_all()` / `get_value()` /
`is_demo_environment()` keep the same external interface other code
already used, so nothing else needed to change.
**How it was found**: caught immediately on the first real install
attempt against a live Odoo 17 + Postgres instance — see `demo_gov_menu`
below for the same theme.

A second, identical-shaped bug followed right after: the DEMO ENVIRONMENT
banner was originally implemented by XML-inheriting into `web.login_layout`
at `//div[hasclass('o_database_list')]/..`, which also didn't match this
build's actual markup. After two guessed-XPath failures in a row, the
banner was rebuilt without any dependency on Odoo's internal page
structure at all: a plain JSON endpoint (`/demo_branding/info`) plus a
small vanilla-JS snippet (`demo_banner.js`) that inserts the banner via
`document.body.prepend(...)`, loaded through `web.assets_frontend`/
`web.assets_backend`'s own root (`position="inside"` on `.` — safe,
doesn't reference any internal class name). A third, related failure followed immediately: even the safe-looking
`position="inside"` on `.` against `web.assets_frontend`/
`web.assets_backend` failed too — `External ID not found in the system:
web.assets_frontend`. This specific Odoo 17 build doesn't have those
QWeb template IDs at all (Odoo's asset bundle mechanism has moved on).
Final fix: register the CSS/JS as `ir.asset` records instead
(`bundle` is a plain string match at render time, not an XML-ID
reference, so it can't fail this way). This is the modern,
template-independent way to add assets and should be preferred over
QWeb bundle-template inheritance generally, live-instance or not.

## `demo_gov_menu` is an incomplete module — confirmed pre-existing in production too

**Problem**: `demo_gov_menu/__manifest__.py` (and the original
`port_said_menu/__manifest__.py` in `odoo_deployment_ar/` — verified
identical) lists 8 data files (`views/menu_structure.xml`,
`views/menu_dashboard.xml`, `views/menu_accts.xml`, and five more) and a
menu ID `menu_ps_20_accts` that five other modules (`demo_gov_subsidiary_books`,
`demo_gov_fixed_assets`, `demo_gov_form69`, `demo_gov_form75`,
`demo_gov_special_funds`) parent their own menus under. None of those 8
files, nor any definition of `menu_ps_20_accts`, exist anywhere in the
repository — confirmed by a repo-wide filename search. The module
directory contains only `__manifest__.py`. This means the "unified
single-tab menu structure" feature described in the module's own summary
cannot actually install in this state, in the Demo Edition or in
production.
**Root cause**: pre-existing, not introduced by anonymization — verified
byte-for-byte identical structure in `odoo_deployment_ar/addons/port_said_menu/`.
**How it was found**: discovered by actually attempting the install
(`docker compose exec odoo ... -i demo_branding,demo_gov_seed_data,demo_gov_meno,...`)
against a live Odoo 17 + Postgres instance — this is exactly the class of
defect the "not tested against a live Odoo instance" limitation below
warned could exist.
**Severity**: High for the "unified menu" feature specifically; Low for
everything else — none of the other modules in the recommended install
set (`demo_branding`, `demo_gov_seed_data`, `l10n_eg_custody`,
`l10n_eg_auction`, `procurement_committee`, `procurement_adjudication`,
`stock_addition_permit`, `stock_stocktaking_eg`) require `demo_gov_menu`
transitively, so it can simply be **omitted from the install list** and
everything else installs and works with each module's own default Odoo
Apps-menu entry instead of the unified single-tab layout.
**Fix required**: write the 8 missing view files (menu structure design
not present anywhere in the source — this needs the application owner's
input, not something to fabricate from the anonymized code alone).
**Recommendation**: `docs/demo/DEPLOYMENT.md` and `demo_edition/README.md`'s
install commands should drop `demo_gov_menu` until this is fixed.

**Update — this went further than a missing-dependency problem.** Once
installed live, 13 modules across the repository (`demo_gov_fixed_assets`,
`demo_gov_form69`, `demo_gov_form75`, `demo_gov_reports`,
`demo_gov_scm_requisition`, `demo_gov_scm_warehouse`,
`demo_gov_special_funds`, `demo_gov_subsidiary_books` (two files),
`l10n_eg_custody`, `procurement_adjudication`, `stock_addition_permit`,
`stock_stocktaking_eg`) each define one top-level `<menuitem>` with
`parent="demo_gov_menu.menu_ps_XX_yyy"` — an XML ID that, per the finding
above, is never defined anywhere. None of these modules formally declare
`demo_gov_menu` as an Odoo dependency either, so Odoo's own dependency
graph gave no warning; the breakage only surfaces at literal install
time, one module at a time, in whatever order Odoo's topological sort
happens to process them (not the order given on the command line — this
is why the first attempts appeared to get further before failing each
time: modules with shallower dependency chains load earlier and hit
their own copy of this bug sooner). **Fixed**: removed the `parent=`
attribute from all 13 menuitems, verified each file still parses.
Each of those 13 menu entries is now a standalone top-level menu instead
of a child of the (nonexistent) unified structure — this is a strict
improvement for the Demo Edition specifically, since every feature stays
reachable from the UI once `demo_gov_menu` is dropped from the install
list, rather than being silently unreachable. Confirmed zero remaining
`demo_gov_menu.` references anywhere in `demo_edition/addons/`.

**Same theme, one more instance**: `l10n_eg_custody/data/demo_users.xml`
seeds `groups_id` with `ref()` calls into `procurement_committee`,
`procurement_adjudication`, `stock_addition_permit`,
`stock_stocktaking_eg`, and `l10n_eg_auction` — none of which
`l10n_eg_custody`'s manifest declared as dependencies (it only depended
on `purchase, sale, stock, account, mail, hr`). Install failed with
`External ID not found in the system: procurement_adjudication.group_adjudication_director`
once Odoo's topological sort happened to load `l10n_eg_custody` before
that module. **Fixed**: added the five missing dependencies to
`l10n_eg_custody/__manifest__.py` (verified no circular dependency
results). Then wrote a static scan across every module in the
recommended install set's transitive closure, checking every `ref('module.xmlid')`
call and every `ir.model.access.csv` `group_id:id` value against that
module's declared dependencies — zero further instances found in that
scope. This class of bug (a data file referencing another module's XML
ID without a matching manifest dependency) is exactly the kind of thing
Odoo's own tooling doesn't catch until literal install time in
whatever order the topological sort happens to pick.

**Update — extended to the full repository, and the full module set now
installs.** Once the 8-module set above was confirmed working live, the
same fix was extended to the rest of the repository: 7 more modules
(`demo_gov_cash_books`, `demo_gov_cash_transfers`, `demo_gov_cheques`,
`demo_gov_insurance_subsidiary`, `demo_gov_penalties`,
`demo_gov_revenue_books`, `demo_gov_subsidiary_books`) had `demo_gov_menu`
in their manifest `depends` with no remaining technical need for it
(their only reference was the menuitem `parent=` already stripped
earlier) — removed. That in turn broke the last of the
`general_ledger_ar` circular-dependency chains from the earlier finding
above (`demo_gov_budget_planning`, `demo_gov_stock_finance_bridge`,
`l10n_eg_eta_invoice`), so those three were re-pointed at
`demo_gov_subsidiary_books` directly — what their own menu XML actually
needed all along.

A repository-wide cycle check (all 49 modules) now reports zero cycles,
and the missing-dependency scan (`ref()` / `parent=` / `ir.model.access.csv`),
extended from the original 8-module scope to all 49 modules, reports
zero issues. The recommended install list is now every module **except**
`demo_gov_menu` itself (still incomplete — see above) and
`demo_gov_dashboard` (the pre-existing unrelated XML defect above) — 47
modules — pending confirmation this installs cleanly end-to-end against
a live instance the same way the original 8 did.

## Circular module dependency through `general_ledger_ar`

**Problem**: `general_ledger_ar -> demo_gov_subsidiary_books ->
demo_gov_menu -> demo_gov_fixed_assets -> general_ledger_ar` (and two more
cycles of the same shape through `demo_gov_budget_planning` and
`l10n_eg_eta_invoice`) — Odoo refuses to install any of these with
`Recursion error in modules dependencies!`.
**Root cause**: pre-existing, confirmed identical in
`odoo_deployment_ar/addons/port_said_fixed_assets/__manifest__.py` etc.
`general_ledger_ar` has no Python models and only four generic menu
items — nothing in `demo_gov_fixed_assets` actually references it (zero
grep hits), so its `depends` entry was dead weight.
**Fixed**: removed the spurious `general_ledger_ar` dependency from
`demo_gov_fixed_assets/__manifest__.py` — this one had zero technical
justification and breaks cleanly. **Not fixed**: the same spurious-looking
edge in `demo_gov_budget_planning`, `demo_gov_stock_finance_bridge`, and
`l10n_eg_eta_invoice` — these three actually do need transitive access to
`demo_gov_subsidiary_books.menu_subsidiary_root` (their own menu XML
parents on it), which they currently only reach via `general_ledger_ar`.
Fixing these properly requires resolving the `demo_gov_menu` gap above
first (since `demo_gov_subsidiary_books` itself sits under
`demo_gov_menu` in the dependency graph, simply pointing them at
`demo_gov_subsidiary_books` directly recreates the same cycle) — recorded
here rather than worked around blindly. None of these three are in the
recommended minimal install list either.

## `general_ledger_ar`'s menu shortcuts pointed at three actions Odoo no longer ships

**Problem**: `general_ledger_ar/views/menu_views.xml` — a thin, models-free
module that only adds four shortcut menu items under the "subsidiary
books" menu — referenced `account.action_account_ledger`,
`account.action_account_receivable_from_account`, and
`account.action_account_payable_from_account`. None of those three exist
in this Odoo 17 build (`account.action_move_journal_line`, the fourth
one, does). Install failed with `External ID not found in the system:
account.action_account_ledger`.
**Root cause**: this Odoo build's `account` module has moved General
Ledger / Partner Ledger reporting onto a different, newer mechanism
(no `ir.actions.act_window`/`ir.actions.client` record under `account`
matches "ledger", "receivable", or "payable" at all — confirmed by
querying `ir_model_data` directly against the live database) — those
three classic action names were presumably valid when
`general_ledger_ar` was originally written against an earlier Odoo 17
point release, and no longer are in this one.
**How it was found and fixed**: rather than guess a fourth time in a
row, queried the live database directly for the actual list of
`account`-module actions, then remapped by real functional match:
General Ledger → `account.action_move_line_select` (Journal Items — the
underlying general-ledger data); both the Customer and Vendor ledger
shortcuts → `account.action_account_moves_ledger_partner` (the modern,
unified Partner Ledger report — which is exactly why separate
receivable/payable ledger actions no longer exist as distinct actions).
Confirmed via repo-wide grep this was the only file referencing any of
the three broken action names.
**Recommendation for a real deployment**: if this module needs to run
against a different Odoo 17 patch level, re-verify these four action
names against that instance the same way (query `ir_model_data`) rather
than assuming this mapping is portable — it's specific to the exact
Odoo build this Demo Edition was tested against.

## `demo_gov_revenue_books` menu loaded before the action it needs

**Problem**: `views/menu.xml` was listed in the manifest's `data` array
*before* `wizard/print_wizard_views.xml`, but its menu item references
an action (`action_revenue_print_wizard`) defined in that later file —
install failed with `External ID not found`.
**Fixed**: reordered the `data` list so the wizard/action file loads
before the menu that references it.
**Also**: wrote a repository-wide static check for this exact bug shape
(a menuitem referencing a same-module action defined in a file that
loads later per the manifest's `data` order) — zero further instances
found anywhere in the 49-module repository.

**Update — the reorder alone wasn't the whole fix.** Once installed
live, a second error surfaced at the same module:
`wizard/print_wizard_views.xml` turned out to have its *own*, exact
duplicate `menu_revenue_print` menuitem (same id, same content) in
addition to the one already correctly defined in `views/menu.xml` — and
that copy referenced `menu_revenue_root`, which is defined in
`views/menu.xml`, i.e. the file loading *after* it. Reordering the
files to fix the first error broke this second, duplicate menuitem
instead. Root cause: the duplicate itself, not the ordering — removed
the redundant copy from `wizard/print_wizard_views.xml`, keeping the
one that was always the canonical definition in `views/menu.xml`.
Extended the load-order static check to also cover `parent=` menu
references (not just `action=`), and separately checked for any other
exact-duplicate `menuitem` id defined in more than one file within the
same module — zero further instances of either anywhere in the
repository.

## Cleaned up every warning surfaced during the live install

None of these blocked installation, but since a live install was
already underway, all warnings raised along the way were fixed rather
than left as noise for the next person:

- **3 manifests listed a data file twice** (`demo_gov_commitment`,
  `demo_gov_dossier`, `demo_gov_scm_requisition` each had their
  `reports/*_report.xml` and `reports/*_template.xml` entries
  duplicated in `data`) — deduplicated.
- **4 module `description` fields broke Odoo's RST renderer**
  (`demo_gov_seed_data` — introduced in this pass, a bullet list
  directly after a paragraph with no blank line; `demo_gov_cash_books`
  and `demo_gov_penalties` — pre-existing, same missing-blank-line
  pattern before a list, plus over-indented continuation text;
  `demo_gov_insurance_subsidiary` — pre-existing, a line of `===`
  characters under a heading-like line was parsed as a section-title
  underline). Fixed all four and then ran every module's `description`
  through `docutils` directly (not just the ones that happened to
  surface in the install log) — zero remaining RST issues anywhere in
  the repository.
- **11 Python field definitions passed view-only attributes
  (`invisible=`, `tracking=`, `password=`) as ORM field constructor
  kwargs** — these aren't valid `fields.X()` parameters and were always
  silently ignored, so removing them is a pure no-op with zero behavior
  change. For the `invisible=` and `password=` cases (which are never
  valid as Python field kwargs regardless of model setup), verified the
  correct `invisible=`/`password=` attribute already exists on the
  corresponding `<field>` tag in each module's own view XML, so the
  actual show/hide and masking behavior was already correct and unaffected.
  For the `tracking=` cases, checked whether the model inherits
  `mail.thread` first: `demo_gov.advance` and `auction.request` do (kept
  `tracking=True`, only removed the co-located invalid `invisible=`);
  `adjudication.supplier.line` and `demo_gov.form69` don't (removed
  `tracking=True`, since it was already non-functional there).
- **5 view files had a Bootstrap `alert`/`alert-*` div with no
  accessibility role** — added `role="alert"` to each (found by a
  repository-wide grep for the pattern, not just instances already hit
  during install).
- **One warning was left as-is deliberately**:
  `custody.assignment.product_description` is a `related`,
  `store=True` field pointing at a translatable source
  (`product.template.description`) — Odoo's warning here is a standard,
  well-known framework caveat about that combination, not a bug; "fixing"
  it would mean removing the stored/related design (used for search and
  reporting) rather than fixing anything broken.

### Update: two more invalid `tracking=` kwargs found after expanding the install to all 47 modules

The fixes above were driven by the log from the original 8-module
install. Once the install list was expanded to all 47 modules (to
surface every app — Accounts, subsidiary books, Assets, Purchases,
Warehouses, Reports, etc.), a fresh full install surfaced one more
instance of the same bug class, and a repository-wide AST scan (every
`ClassDef` with a `tracking=True` field kwarg, cross-checked against
that class's own `_inherit`/`_name` for `mail.thread`, with `_inherit`
targets resolved against Odoo core and against this repo's own model
definitions) found a second one that hadn't surfaced in any log yet:

- `demo_gov_scm_warehouse.WarehouseAdditionPermit.state` — the model
  doesn't inherit `mail.thread` (only its sibling model in the same
  module, `InspectionCommittee`, does). Removed `tracking=True`.
- `procurement_committee.ProcurementCommitteeMixin.committee_id` — an
  `AbstractModel` mixin that doesn't inherit `mail.thread` itself and
  isn't currently `_inherit`'d by any concrete model in the repo, so it
  never picks up `mail.thread` transitively either. Removed
  `tracking=True`.

The same scan confirmed every other `tracking=True` in the repo is on
a model that inherits `mail.thread` either directly or by extending a
core Odoo model that already does (`purchase.order`, `sale.order`,
`hr.employee`), or a model defined elsewhere in the same module that
does (`stock.stocktaking.session`, `demo_gov.daftar55`,
`auction.request`, `auction.lease.contract`) — no further instances of
this bug class remain anywhere in `demo_edition/addons`.

## Live-tested against a real Odoo 17 instance — confirmed working

**Update**: the gap described below (no live Odoo runtime in the build
environment) has since been closed. The Demo Edition was installed
end-to-end on a real Docker Desktop + Odoo 17 (`17.0-20260305`) stack,
against a freshly-dropped, empty database, with the full 47-module
custom install list (114 modules total once Odoo's own core
dependencies are included, `demo_gov_menu` and `demo_gov_dashboard`
excluded per their sections below). The install completed cleanly:
`Modules loaded.` / `Registry loaded in 56.065s`, zero errors, zero
remaining warnings after the fixes documented across this file
(Bugs 6-16 plus the two additional `tracking=` fixes above). All of
Accounts, the subsidiary books, Assets, Purchases, Warehouses/SCM, and
Reports are confirmed visible and installed.

Everything below this point in the original writeup (build environment
had no cloud account/Odoo runtime, so only static verification —
parses, dependency resolution, no leftover identifying strings — had
been done) is now superseded for the general install path. It's kept
for history since the individual bugs it led to finding are still
documented throughout this file. The one thing that remains genuinely
untested live is the seeded demo *data* and *scenarios*
(`demo_edition/scripts/demo-seed/demo-reset.sh`) rather than the
module installation itself — run that script and walk through the
demo scenarios at least once before any real presentation.

## `demo_gov_dashboard/views/dashboard_template.xml` — malformed XML

**Problem**: line 302 embeds raw HTML tags inside a JS string literal
inside (what should be) a `<script>` block, without a `CDATA` wrapper —
breaks strict XML parsing (confirmed with Python's `xml.etree`).
**Root cause**: pre-existing in the original production code
(`odoo_deployment_ar/addons/portsaid_dashboard/views/dashboard_template.xml`
has the identical defect) — not introduced by this conversion.
**Severity**: Low-Medium — may or may not affect the dashboard at
runtime depending on how Odoo's own QWeb/asset loader handles it (it may
be more lenient than a strict parser); unverified without a live
instance. **Fix required**: wrap the inline JS block in `<![CDATA[ ... ]]>`
or escape the embedded HTML string. Not fixed here — it's a
business-logic-adjacent code change, out of the anonymization/packaging
scope this pass was scoped to. **Recommendation**: fix before relying on
this dashboard in a presentation; verify Step 8 of `DEMO_SCRIPT.md`
against a real instance first regardless.

## `demo_gov_form50_print` — not installable

**Problem**: ships `models/form50_print.py` (398 lines, extends the
Daftar 55 model with a print-only layer) but no `__manifest__.py`.
**Root cause**: pre-existing — same in production
(`port_said_form50_print/`). Not referenced by any other module.
**Severity**: Informational — Odoo silently ignores a directory with no
manifest, so this doesn't break anything; the code inside is simply dead.
**Fix required**: either give it a manifest (if the print layer it
implements is wanted) or delete the directory. Left as-is because it's
unclear from source alone whether this was abandoned intentionally or is
missing a file. **Recommendation**: ask whoever owns the production
codebase before doing either.

## Report branding is static text, not dynamically config-driven

**Problem**: `demo_branding`'s centralized config (`BRANDING.md`) drives
the login banner and health check, but the ~30 printed QWeb report
templates still carry their branding as anonymized static strings rather
than reading `demo.branding` live.
**Root cause**: wiring config values into QWeb report rendering context
needs to be verified against a live Odoo instance (report context
variables differ subtly by Odoo version/report type), which was out of
scope for this pass.
**Severity**: Low — the current state is safe (no real identity leaks),
just not centrally editable without a code change.
**Fix required**: extend `gov_shared_layout.xml`'s `gov_header`/`gov_footer`
templates to call `env['demo.branding'].get_all()` and use the returned
values, then verify rendering on a live instance.

## Transactional demo data is not scripted

**Problem**: only master data (users, employees, vendors, items) is
seeded automatically; workflow records (a completed procurement cycle, an
awarded auction, a posted custody assignment) require a manual one-time
walkthrough (`DEMO_GUIDE.md`) rather than being present immediately after
install.
**Root cause**: deliberate — see `DEMO_DATA.md` for why raw XML records
past `draft` state were judged unsafe to script without live
verification.
**Severity**: Low — documented and has a clear, one-time remedy
(`DEMO_GUIDE.md` step 1-2, then snapshot the database).

## No automated test suite

**Problem**: no unit/integration/smoke tests were added.
**Root cause**: none existed in the production repository to extend, and
writing a test suite from scratch for 37 modules was outside the
"anonymize + package" scope chosen for this pass.
**Severity**: Medium for long-term maintainability; Low for the demo's
immediate usability, since the manual walkthrough in `DEMO_GUIDE.md`
serves as the smoke test until an automated one exists.
**Recommendation**: at minimum, script the `DEMO_SCRIPT.md` sequence as a
Playwright/Selenium smoke test once a live instance is available to
develop it against.

## No live cloud deployment performed

**Problem**: `DEPLOYMENT.md`'s cloud-provider guidance is untested.
**Root cause**: no cloud account was available in the build environment.
**Severity**: Medium if a cloud deployment is imminent — budget time for
first-deployment troubleshooting. **Recommendation**: deploy to a
disposable/free-tier environment first as a dry run before a real
customer-facing demo deployment.

## CI/CD not added

Documented already in `DEPLOYMENT.md`. No pipeline existed to extend; not
built from scratch in this pass.
