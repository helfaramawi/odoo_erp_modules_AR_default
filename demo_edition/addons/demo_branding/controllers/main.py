import json

from odoo import http
from odoo.http import request


class DemoHealthController(http.Controller):

    @http.route('/api/health', type='http', auth='public', csrf=False, methods=['GET'])
    def health(self):
        """Minimal health check for container orchestration.

        Deliberately returns no internal infrastructure details (host,
        database name, versions) — only status and environment label.
        """
        try:
            environment = request.env['demo.branding'].sudo().get_value('environment')
            status = 'healthy'
        except Exception:
            environment = 'unknown'
            status = 'degraded'
        body = json.dumps({'status': status, 'environment': environment})
        return request.make_response(
            body,
            headers=[('Content-Type', 'application/json')],
        )

    @http.route('/demo_branding/info', type='http', auth='public', csrf=False, methods=['GET'])
    def info(self):
        """Branding info for the JS-rendered banner (see demo_banner.js).

        Deliberately a plain JSON endpoint + client-side DOM insertion
        instead of QWeb-inheriting into Odoo core's login/webclient page
        templates: two attempts at that broke on internal markup that
        doesn't match this Odoo build (see KNOWN_LIMITATIONS.md). This
        has no dependency on Odoo's internal page structure at all.
        """
        try:
            data = request.env['demo.branding'].sudo().get_all()
        except Exception:
            data = {'environment': 'unknown', 'application_name': ''}
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')],
        )
