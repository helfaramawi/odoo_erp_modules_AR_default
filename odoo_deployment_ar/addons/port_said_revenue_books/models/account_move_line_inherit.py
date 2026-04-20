# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_revenue_folio_ids = fields.Many2many(
        'port_said.revenue.folio',
        compute='_compute_revenue_folios',
        string='يظهر في فوليوهات إيرادات/مصروفات')

    def _compute_revenue_folios(self):
        Folio = self.env['port_said.revenue.folio']
        for line in self:
            line.x_revenue_folio_ids = Folio.search([
                ('date_from', '<=', line.date),
                ('date_to', '>=', line.date),
                ('company_id', '=', line.company_id.id),
            ])

    def action_open_revenue_folios(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('فوليوهات إيرادات/مصروفات'),
            'res_model': 'port_said.revenue.folio',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.x_revenue_folio_ids.ids)],
        }
