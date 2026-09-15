# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        engine = self.env['port_said.vendor.data.quality.engine'].sudo()
        block_purchase = engine._get_block_purchase()
        min_score = engine._get_min_score()

        for po in self:
            partner = po.partner_id
            if not partner:
                continue

            if partner.supplier_rank > 0:
                partner.sudo().action_recalculate_vendor_quality()
                quality = partner.vendor_quality_id[:1]

                if block_purchase and quality and quality.score < min_score:
                    raise UserError(_(
                        'لا يمكن اعتماد أمر الشراء لأن جودة بيانات المورد أقل من الحد المسموح.\n\n'
                        'المورد: %s\n'
                        'درجة الجودة: %s / 100\n'
                        'الحد الأدنى: %s\n\n'
                        'النواقص:\n%s'
                    ) % (
                        partner.display_name,
                        quality.score,
                        min_score,
                        quality.issue_summary or ''
                    ))

        return super().button_confirm()
