from odoo import api, fields, models


class DemoBrandingConfig(models.Model):
    """Editable, persisted branding config — single source of truth.

    Deliberately a plain model with its own dedicated screen instead of
    inheriting res.config.settings: that requires XML-inheriting into
    Odoo core's General Settings page layout, which varies across
    versions and is easy to get wrong without a live instance to verify
    against. A standalone screen has no such dependency.
    """
    _name = 'demo.branding.config'
    _description = 'Demo Branding Configuration'

    application_name = fields.Char(default='Enterprise Digital Operations Platform', required=True)
    organization_name = fields.Char(default='Public Services Organization', required=True)
    environment = fields.Selection(
        [('demo', 'Demo'), ('production', 'Production')],
        default='demo', required=True,
    )
    support_email = fields.Char(default='support@example.com')
    support_phone = fields.Char(default='+000 000 0000')

    @api.model
    def get_singleton(self):
        record = self.search([], limit=1, order='id asc')
        if not record:
            record = self.create({})
        return record
