# External Integrations

| Integration | Module | Original behavior | Demo Edition classification | How it's enforced |
|---|---|---|---|---|
| Egyptian Tax Authority (ETA) e-invoicing | `l10n_eg_eta_invoice` | OAuth2 client-credentials call to `https://api.invoicing.eta.gov.eg` (production) or `https://api.preprod.invoicing.eta.gov.eg` (preprod), then submit/query/cancel invoice documents | **DISABLED** (not mocked with fake success — see rationale below) | `EtaConfig._get_access_token()` raises a clear bilingual `ValidationError` before any `requests.*` call is made, whenever demo mode is active |
| Credit Bureau API | `c7_credit_bureau` | HTTP GET to an admin-configured `api_url`, bearer-token auth, returns a credit score | **MOCK** | `SaleOrder._call_credit_api()` returns a deterministic synthetic score (SHA-256 of partner id → 300-900 range) instead of calling out, whenever demo mode is active |
| Tax filing XML export | `c13_tax_xml_export` | Generates a signed XML file for manual upload to a government portal | **N/A — offline file generation, no live call to classify** | No change needed |

## Demo-mode gate (single choke point per integration)

Both integrations check the same condition, duplicated in each module
rather than centralized, because `c7_credit_bureau` and
`l10n_eg_eta_invoice` don't otherwise depend on `demo_branding`:

```python
def _is_demo_environment(self):
    if os.environ.get('APP_ENV') == 'demo':
        return True
    return self.env['ir.config_parameter'].sudo().get_param(
        'demo_branding.environment', 'production') == 'demo'
```

This reads the same `demo_branding.environment` parameter the
`demo_branding` module exposes in Settings, plus a fast env-var check, so
the gate works whether or not `demo_branding` happens to be installed.
Both modules' single outbound-call code paths were traced (every
`requests.get/post/put` call site is reached through this guard before
any network I/O — see `KNOWN_LIMITATIONS.md` for how that was confirmed
without a live interpreter) so there is no remaining path from the Demo
Edition to a real government tax server or a real credit bureau.

## Why ETA is disabled rather than mocked with a fake success

Faking a realistic "ETA accepted this invoice" response risks demo
viewers walking away with a wrong impression of tax-compliance behavior
for what is, in production, a government filing. A clear "this is
simulated / disabled in the Demo Edition" message was judged safer and
more honest than a convincing fake approval. The Credit Bureau check, by
contrast, has no compliance implication — a synthetic score number is
low-risk and makes for a better demo (the green/amber/red workflow is
visibly exercised).

## Not found in this codebase

No SMS gateway, no payment gateway, no document-storage/cloud-bucket
integration, no dedicated AI service call, and no separate identity
provider (SSO/OAuth login) were found anywhere in the 37 modules
inspected. Odoo's own built-in outbound email (`mail` module, SMTP) is
present as infrastructure but not configured with any credentials in the
source; see `.env.example`'s `MAIL_CONNECTION` (left blank = outbound
email disabled by default in the Demo Edition, per `odoo.conf.demo`'s
`email_from = False`).
