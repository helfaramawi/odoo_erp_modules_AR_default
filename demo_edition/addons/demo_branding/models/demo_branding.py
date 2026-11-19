from odoo import api, models


class DemoBranding(models.AbstractModel):
    """Read-only helper other modules/reports/controllers call instead of
    hard-coding branding strings:
        self.env['demo.branding'].get_all()
        self.env['demo.branding'].get_value('environment')
        self.env['demo.branding'].is_demo_environment()
    """
    _name = 'demo.branding'
    _description = 'Demo Branding Helper'

    @api.model
    def get_all(self):
        record = self.env['demo.branding.config'].sudo().get_singleton()
        return {
            'application_name': record.application_name,
            'organization_name': record.organization_name,
            'environment': record.environment,
            'support_email': record.support_email,
            'support_phone': record.support_phone,
        }

    @api.model
    def get_value(self, key):
        return self.get_all().get(key, '')

    @api.model
    def is_demo_environment(self):
        return self.get_value('environment') == 'demo'
