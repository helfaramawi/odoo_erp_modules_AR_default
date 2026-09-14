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
doesn't reference any internal class name). This is the more robust
pattern going forward for anything that needs to touch Odoo's own pages;
prefer it over inheriting into core view internals when there isn't a
live instance available to verify the exact markup against.

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
