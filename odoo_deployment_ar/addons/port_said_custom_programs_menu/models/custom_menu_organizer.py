# -*- coding: utf-8 -*-
from odoo import models, _


class PortSaidCustomMenuOrganizer(models.TransientModel):
    _name = 'port_said.custom.menu.organizer'
    _description = 'منظم قوائم البرامج المخصصة'

    def _get_or_create_root_menu(self):
        Menu = self.env['ir.ui.menu'].sudo()
        IMD = self.env['ir.model.data'].sudo()

        xmlid = IMD.search([
            ('module', '=', 'port_said_custom_programs_menu'),
            ('name', '=', 'menu_custom_programs_root'),
            ('model', '=', 'ir.ui.menu'),
        ], limit=1)

        if xmlid and xmlid.res_id:
            menu = Menu.browse(xmlid.res_id)
            if menu.exists():
                return menu

        menu = Menu.search([
            ('name', '=', 'مجموعة البرامج المخصصة'),
            ('parent_id', '=', False),
        ], limit=1)

        if not menu:
            menu = Menu.create({
                'name': 'مجموعة البرامج المخصصة',
                'sequence': 65,
                'parent_id': False,
            })

        if not xmlid:
            IMD.create({
                'module': 'port_said_custom_programs_menu',
                'name': 'menu_custom_programs_root',
                'model': 'ir.ui.menu',
                'res_id': menu.id,
                'noupdate': False,
            })
        else:
            xmlid.write({'res_id': menu.id})

        return menu

    def action_organize_c_menus(self):
        Menu = self.env['ir.ui.menu'].sudo()
        IMD = self.env['ir.model.data'].sudo()
        Module = self.env['ir.module.module'].sudo()

        root = self._get_or_create_root_menu()

        c_modules = Module.search([
            ('name', '=like', 'c%'),
            ('state', '=', 'installed'),
        ]).filtered(lambda m: m.name and len(m.name) > 1 and m.name[1].isdigit())

        moved = 0
        skipped = 0

        for mod in c_modules:
            menu_xmlids = IMD.search([
                ('module', '=', mod.name),
                ('model', '=', 'ir.ui.menu'),
            ])

            menus = Menu.browse(menu_xmlids.mapped('res_id')).exists()

            top_menus = menus.filtered(lambda menu: not menu.parent_id)

            if not top_menus and menus:
                owned_ids = set(menus.ids)
                top_menus = menus.filtered(lambda menu: not menu.parent_id or menu.parent_id.id not in owned_ids)

            for menu in top_menus:
                if menu.id == root.id:
                    skipped += 1
                    continue

                if menu.name in ('Settings', 'الإعدادات', 'Apps', 'التطبيقات'):
                    skipped += 1
                    continue

                menu.write({
                    'parent_id': root.id,
                    'sequence': menu.sequence or 10,
                })
                moved += 1

        message = _('تم تجميع %s قائمة من برامج c* تحت مجموعة البرامج المخصصة. تم تخطي %s قائمة.') % (moved, skipped)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تنظيم القوائم'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
