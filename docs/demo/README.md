# Demo Edition Documentation

This folder documents the conversion of the production Odoo 17 government
financial/ERP module suite (`odoo_deployment_ar/`) into a safe-to-share
**Demo Edition** (`demo_edition/` at the repository root). The production
tree was not modified — the Demo Edition is an anonymized, isolated copy.

Read in this order:

1. [`DEMO_CONVERSION_PLAN.md`](DEMO_CONVERSION_PLAN.md) — scope, phases, what was and wasn't done, and why.
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) — technology stack and module dependency structure.
3. [`FEATURE_INVENTORY.md`](FEATURE_INVENTORY.md) — every module, what it does, and its demo status.
4. [`BRANDING.md`](BRANDING.md) — exactly what identifying information was found and how it was replaced.
5. [`DEMO_DATA.md`](DEMO_DATA.md) — the synthetic dataset shipped with the Demo Edition.
6. [`INTEGRATIONS.md`](INTEGRATIONS.md) — every external dependency and how it's handled in demo.
7. [`SECURITY_REVIEW.md`](SECURITY_REVIEW.md) — findings and fixes.
8. [`ROLE_MATRIX.md`](ROLE_MATRIX.md) — demo accounts and permissions.
9. [`DEPLOYMENT.md`](DEPLOYMENT.md) — how to run it (Docker and bare-metal).
10. [`DEMO_GUIDE.md`](DEMO_GUIDE.md) / [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) — how to present it.
11. [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) — what's not done, and pre-existing defects found along the way.

The application itself lives in [`demo_edition/`](../../demo_edition/),
with its own [README](../../demo_edition/README.md) for day-to-day use
(install, reset, troubleshooting).
