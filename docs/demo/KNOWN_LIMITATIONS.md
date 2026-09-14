# Known Limitations

Honest punch list. Nothing below was hidden or silently worked around.

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
