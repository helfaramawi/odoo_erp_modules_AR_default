from . import models

def post_init_hook(env):
    env['demo_gov.custom.menu.organizer'].sudo().action_organize_c_menus()
