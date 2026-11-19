# Deployment

Day-to-day instructions live in
[`demo_edition/README.md`](../../demo_edition/README.md) (Docker Compose
quick start, bare-metal install, resetting the demo, troubleshooting).
This document covers the parts specific to a cloud deployment.

## What's provided

- `demo_edition/docker/Dockerfile` — official `odoo:17.0` base image
  (already runs as a non-root `odoo` user) + Arabic font packages +
  the Demo Edition addons copied in + a `HEALTHCHECK` hitting `/api/health`.
- `demo_edition/docker/docker-compose.demo.yml` — Odoo + PostgreSQL 15,
  named volumes for the database and filestore, `restart: unless-stopped`,
  both services healthchecked, an isolated bridge network.
- `demo_edition/.env.example` — every configurable value, all blank/demo
  defaults; copy to `.env` and fill in before running.

## What was not done (no cloud account available)

No actual deployment to AWS/Azure/GCP/DigitalOcean/Huawei Cloud was
performed or could be performed in the build environment — there was no
cloud account to deploy to. The stack below is provider-agnostic (plain
Docker Compose, no provider-specific service used), so it should map onto
any of the following without changes to the application itself — only
the deployment commands differ:

| Provider | Suggested approach |
|---|---|
| Any VM (DigitalOcean Droplet, Azure VM, EC2, on-prem) | Install Docker + Compose, copy `demo_edition/`, `docker compose --env-file .env -f docker/docker-compose.demo.yml up -d --build` |
| AWS | ECS/Fargate (two task definitions from the same Dockerfile + an RDS Postgres instead of the `db` service) or plain EC2 + Docker Compose |
| Azure | Container Apps or App Service for Containers + Azure Database for PostgreSQL |
| Google Cloud | Cloud Run (stateless Odoo container) + Cloud SQL for PostgreSQL — note Cloud Run's read-only filesystem means the Odoo filestore volume must move to Cloud Storage/GCS-fuse or a similar mount |
| Managed Odoo hosting (Odoo.sh, etc.) | Push `demo_edition/addons/` as the custom addons path per that platform's own workflow, ignore the Dockerfile |

None of these were tested. Treat the Docker Compose stack (which *is*
buildable/runnable, verified by YAML/Dockerfile syntax and matching the
official Odoo image's documented environment variables) as the reference
implementation, and adapt deliberately rather than assuming any specific
cloud config above works unmodified.

## HTTPS

Neither the Dockerfile nor the compose file terminates TLS — `proxy_mode = True`
is set in `odoo.conf.demo` so Odoo trusts `X-Forwarded-*` headers from a
reverse proxy, but you must put one in front of it (nginx, Caddy, Traefik,
or your cloud provider's load balancer) with a real certificate before
exposing the demo publicly. Do not expose port 8069 directly to the
internet.

## Health check

```
GET /api/health
200 {"status": "healthy", "environment": "demo"}
```

Provided by `demo_branding` — no internal infrastructure details (host,
database name, versions) are exposed in the response, by design.

## Database

Demo Edition databases must be named `demo_*` — enforced by
`scripts/demo-seed/demo-reset.sh`'s guard rail, not just a convention.
For a cloud deployment, point `HOST`/`PORT`/`USER`/`PASSWORD` (standard
Odoo environment variables, already wired in `docker-compose.demo.yml`)
at your managed Postgres instance instead of the bundled `db` service.

## CI/CD

No CI/CD pipeline exists in this repository (production or demo). Adding
one (lint → unit tests → build → security scan → container build →
deploy → migrate → seed → health check → smoke test, per common practice)
is a reasonable next step but was not built here — there is no existing
CI system in the repo to extend, and building one from scratch was
outside the "anonymize + package" scope chosen for this pass (see
`DEMO_CONVERSION_PLAN.md`).
