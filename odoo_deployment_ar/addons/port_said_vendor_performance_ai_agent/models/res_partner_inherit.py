# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_performance_score_ids = fields.One2many(
        'port_said.vendor.performance.score',
        'partner_id',
        string='تقييمات كفاءة المورد'
    )

    vendor_latest_performance_score = fields.Float(
        string='آخر تقييم كفاءة',
        compute='_compute_vendor_latest_performance',
        store=False
    )

    vendor_latest_performance_rating = fields.Selection([
        ('excellent', 'ممتاز'),
        ('good', 'جيد'),
        ('average', 'متوسط'),
        ('risky', 'عالي المخاطر'),
    ], string='آخر تصنيف كفاءة', compute='_compute_vendor_latest_performance', store=False)

    def _compute_vendor_latest_performance(self):
        Score = self.env['port_said.vendor.performance.score'].sudo()
        for rec in self:
            latest = Score.search([('partner_id', '=', rec.id)], order='period_date desc', limit=1)
            rec.vendor_latest_performance_score = latest.final_score if latest else 0.0
            rec.vendor_latest_performance_rating = latest.rating if latest else False

    def action_recompute_vendor_performance(self):
        period = fields.Date.today()
        for rec in self:
            if rec.supplier_rank > 0:
                self.env['port_said.vendor.performance.engine'].sudo().compute_vendor_score(rec, period)
        return True
