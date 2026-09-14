from odoo import api, models

DEFAULTS = {
    'application_name': 'Enterprise Digital Operations Platform',
    'organization_name': 'Public Services Organization',
    'environment': 'demo',
    'support_email': 'support@example.com',
    'support_phone': '+000 000 0000',
}


class DemoBranding(models.AbstractModel):
    """Single source of truth for demo branding, backed by ir.config_parameter.

    Any report, controller, or view can call:
        self.env['demo.branding'].get_all()
    instead of hard-coding the application/organization name.
    """
    _name = 'demo.branding'
    _description = 'Demo Branding Helper'

    @api.model
    def get_value(self, key):
        icp = self.env['ir.config_parameter'].sudo()
        return icp.get_param(f'demo_branding.{key}', DEFAULTS.get(key, ''))

    @api.model
    def get_all(self):
        return {key: self.get_value(key) for key in DEFAULTS}

    @api.model
    def is_demo_environment(self):
        return self.get_value('environment') == 'demo'
