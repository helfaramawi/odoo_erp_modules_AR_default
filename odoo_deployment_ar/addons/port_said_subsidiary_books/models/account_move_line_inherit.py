# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_subsidiary_folio_ids = fields.Many2many(
        'port_said.subsidiary.folio',
        compute='_compute_subsidiary_folios',
        string='يظهر في فوليوهات',
        help='الفوليوهات القانونية التي يظهر فيها هذا السطر.')

    def _compute_subsidiary_folios(self):
        Folio = self.env['port_said.subsidiary.folio']
        for line in self:
            if not line.account_id.x_subsidiary_classification_id:
                line.x_subsidiary_folio_ids = False
                continue
            line.x_subsidiary_folio_ids = Folio.search([
                ('date_from', '<=', line.date),
                ('date_to', '>=', line.date),
                ('book_id.account_classification_ids', 'in',
                 line.account_id.x_subsidiary_classification_id.id),
                '|',
                ('partner_id', '=', line.partner_id.id),
                ('account_id', '=', line.account_id.id),
            ])

    def action_open_subsidiary_folios(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('فوليوهات هذا السطر'),
            'res_model': 'port_said.subsidiary.folio',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.x_subsidiary_folio_ids.ids)],
        }
