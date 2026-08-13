from . import models

def post_init_hook(env):
    env['port_said.custom.menu.organizer'].sudo().action_organize_c_menus()
