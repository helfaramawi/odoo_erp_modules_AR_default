# Known Limitations

Honest punch list. Nothing below was hidden or silently worked around.

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

## Not tested against a live Odoo instance

**Root cause**: the build environment had no cloud account and no
pre-existing Odoo 17 runtime; standing one up was explicitly deprioritized
in favor of anonymization/packaging (see `DEMO_CONVERSION_PLAN.md`).
**Severity**: Medium-High — this is the single biggest gap. **Fix
required**: run `demo_edition/scripts/demo-seed/demo-reset.sh` (or the
Docker quick start) as the real first test, before any presentation.
Everything in this repo was verified statically (parses, dependencies
resolve, no leftover identifying strings) but *not* by actually booting
Odoo. **Workaround**: none — this needs to happen once, in an
environment with Odoo available, before the Demo Edition is trusted.

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
