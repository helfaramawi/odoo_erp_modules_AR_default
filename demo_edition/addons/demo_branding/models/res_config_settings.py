from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    demo_branding_application_name = fields.Char(
        string='Application Name',
        config_parameter='demo_branding.application_name',
    )
    demo_branding_organization_name = fields.Char(
        string='Organization Name',
        config_parameter='demo_branding.organization_name',
    )
    demo_branding_environment = fields.Selection(
        selection=[('demo', 'Demo'), ('production', 'Production')],
        string='Environment',
        config_parameter='demo_branding.environment',
    )
    demo_branding_support_email = fields.Char(
        string='Support Email',
        config_parameter='demo_branding.support_email',
    )
    demo_branding_support_phone = fields.Char(
        string='Support Phone',
        config_parameter='demo_branding.support_phone',
    )
