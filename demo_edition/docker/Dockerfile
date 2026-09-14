# Demo Edition image — built on the official Odoo 17 image (already runs
# as the non-root "odoo" user). We only add our own addons on top.
FROM odoo:17.0

USER root

# Arabic RTL PDF reports need proper shaping/BiDi fonts.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fonts-hosny-amiri \
        fonts-noto-core \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Demo Edition addons (already anonymized — see docs/demo/BRANDING.md)
COPY --chown=odoo:odoo addons /mnt/demo-addons

# Demo-only Odoo config (points at the demo addons path, disables demo
# mail delivery — see odoo.conf.demo for the full annotated version)
COPY --chown=odoo:odoo docker/odoo.conf.demo /etc/odoo/odoo.conf

USER odoo

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -fsS http://localhost:8069/api/health || exit 1

EXPOSE 8069 8072
