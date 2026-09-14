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
