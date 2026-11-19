from . import models


def post_init_hook(env):
    """Fill the sample requests with captions so the app opens with real examples."""
    samples = env['social.caption.request'].search([('state', '=', 'draft')])
    samples.with_context(social_caption_force_offline=True).action_generate()
