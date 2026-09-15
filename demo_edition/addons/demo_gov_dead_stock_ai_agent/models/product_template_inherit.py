# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    dead_stock_alert_ids = fields.One2many(
        'demo_gov.dead.stock.alert',
        'product_tmpl_id',
        string='تنبيهات المخزون الراكد'
    )

    dead_stock_alert_count = fields.Integer(
        string='عدد تنبيهات المخزون الراكد',
        compute='_compute_dead_stock_alert_count'
    )

    def _compute_dead_stock_alert_count(self):
        Alert = self.env['demo_gov.dead.stock.alert'].sudo()
        for rec in self:
            rec.dead_stock_alert_count = Alert.search_count([('product_tmpl_id', '=', rec.id)])

    def action_open_dead_stock_alerts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'تنبيهات المخزون الراكد',
            'res_model': 'demo_gov.dead.stock.alert',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'target': 'current',
        }
