from . import models
from . import wizard


def post_init_hook(env):
    """Set company report layout to prevent the 'configure layout' wizard."""
    companies = env['res.company'].sudo().search([])
    for company in companies:
        if not company.external_report_layout_id:
            layout = env['ir.ui.view'].sudo().search([
                ('key', '=', 'web.external_layout_standard'),
            ], limit=1)
            if not layout:
                layout = env['ir.ui.view'].sudo().search([
                    ('key', 'like', 'web.external_layout'),
                    ('type', '=', 'qweb'),
                ], limit=1)
            if layout:
                company.sudo().write({'external_report_layout_id': layout.id})
