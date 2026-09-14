# Security Review

Scope: static review of `demo_edition/addons/` (source code, config,
data files). No dynamic/runtime testing was performed (no live Odoo
instance was available — see `DEMO_CONVERSION_PLAN.md`), so this is not
a substitute for a real penetration test or an authenticated code
security scan before a public-internet deployment.

## Findings and fixes

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | Real government tax-authority (ETA) API reachable from the codebase, hardcoded production and preprod URLs | High (data exposure / accidental real filing if credentials were ever entered) | **Fixed** — demo-mode gate blocks every outbound call (`INTEGRATIONS.md`) |
| 2 | Credit Bureau external API reachable, admin-configurable URL | Medium (uncontrolled outbound call target) | **Fixed** — demo-mode gate returns a synthetic score instead |
| 3 | Real government seal image embedded as base64 inside 34 report templates (55 occurrences), not just as static files | Medium (identity/branding leak inside generated PDFs, missed by a naive "replace image files" pass) | **Fixed** — replaced at the byte level, MD5-verified |
| 4 | Real-looking employee names + real government email domain (`@<client>.gov.eg`) in demo seed data | Medium (personal-data-shaped info in a public demo) | **Fixed** — rewritten to role-based accounts, `@demo-gov.example` domain |
| 5 | Hard-coded demo password (`Diwan@2024`) shared by all 7 seed accounts | Low-Medium in a demo context; would be High if reused in a real deployment | **Mitigated** — default changed, and a `DEMO_USERS_PASSWORD` env var + post-install hook lets every deployment set its own password without editing code |
| 6 | No secret values found hardcoded anywhere (`client_secret`, `api_key` fields all ship empty, entered by the admin at runtime) | — | No action needed; confirmed by grep across `.py`/`.xml`/`.csv`/`.conf` for `password=`, `secret=`, `api_key`, `token=` |
| 7 | No `.env`/credential files tracked in git | — | Confirmed clean; `.env.example` added with all values blank |
| 8 | One pre-existing malformed XML file (`demo_gov_dashboard/views/dashboard_template.xml`) — unescaped HTML inside inline JS breaks strict XML parsing | Low (functional bug, not a security issue per se — but any part of a page an XML parser can't validate is worth flagging) | **Not fixed** — pre-existing in production too, out of the anonymization scope for this pass; documented in `KNOWN_LIMITATIONS.md` |
| 9 | `demo_gov_form50_print` module has no `__manifest__.py` — dead code, not installable, but still present on disk | Informational | **Not fixed** — pre-existing, harmless (Odoo won't load a directory without a manifest); documented in `KNOWN_LIMITATIONS.md` |

## Checks performed (with the commands used)

```bash
# Hardcoded secrets
grep -rIE "password\s*=|secret\s*=|api_key|apikey|token\s*=" \
  --include="*.py" --include="*.xml" --include="*.conf" .

# Emails / IPs / phone-like strings
grep -rIEo "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" .
grep -rIEo "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" .

# Any remaining client/vendor identity strings (see BRANDING.md)
grep -rIcE "port_said|portsaid|Port Said|Paradise|بورسعيد" . | grep -v ':0'

# Embedded images clustered by content hash (catches base64, not just files)
# — custom script, see BRANDING.md's "Verification method"
```

All returned clean (zero hits) in `demo_edition/` after the fixes above,
except the intentional demo config values in `.env.example` (blank
placeholders) and the demo domain `@demo-gov.example` / `example.com`
(IANA-reserved, non-resolving documentation domains, used deliberately).

## Not checked (out of scope for this pass — no live instance)

- SQL injection / XSS / CSRF / IDOR / broken auth in the actual running
  application — Odoo's ORM parameterizes queries by default and these
  modules were not seen to build raw SQL from user input during review,
  but this was a read-through, not a dynamic scan.
- CORS configuration, security headers, cookie flags — these are set by
  Odoo core / the reverse proxy in front of it, not by these addons;
  configure them at the proxy layer for any real deployment (see
  `DEPLOYMENT.md`).
- Dependency vulnerability scanning (no `requirements.txt` exists in this
  repo to scan — it depends on whatever Odoo 17 core version is deployed
  alongside it).

## Recommendations before any public-internet demo deployment

1. Set a strong, unique `DEMO_USERS_PASSWORD` (never keep the shipped default).
2. Terminate TLS at a reverse proxy in front of the Odoo container (see `DEPLOYMENT.md`); do not expose port 8069 directly.
3. Set `list_db = False` (already default in `odoo.conf.demo`) so the database-manager screen isn't publicly browsable.
4. Periodically run `scripts/demo-seed/demo-reset.sh` to wipe any data a demo visitor may have entered.
