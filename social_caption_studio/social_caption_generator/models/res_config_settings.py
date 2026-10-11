from odoo import fields, models

from .caption_engine import DEFAULT_MODEL


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    social_caption_api_key = fields.Char(
        string='Anthropic API key',
        config_parameter='social_caption_generator.api_key',
        help='Leave empty to use the built-in generator, or to read ANTHROPIC_API_KEY from the server environment.')
    social_caption_model = fields.Char(
        string='Claude model',
        config_parameter='social_caption_generator.model',
        default=DEFAULT_MODEL)
