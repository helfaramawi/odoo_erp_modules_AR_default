# -*- coding: utf-8 -*-
from datetime import date, timedelta
from calendar import monthrange
from odoo import api, fields, models, _


class PortSaidVendorPerformanceEngine(models.TransientModel):
    _name = 'port_said.vendor.performance.engine'
    _description = 'محرك تقييم كفاءة الموردين'

    @api.model
    def _month_start(self, any_date=None):
        d = any_date or fields.Date.today()
        if isinstance(d, str):
            d = fields.Date.to_date(d)
        return date(d.year, d.month, 1)

    @api.model
    def _month_end(self, any_date=None):
        d = any_date or fields.Date.today()
        if isinstance(d, str):
            d = fields.Date.to_date(d)
        last = monthrange(d.year, d.month)[1]
        return date(d.year, d.month, last)

    @api.model
    def _get_min_warning_score(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_vendor_performance.min_warning_score',
            '60'
        )
        try:
            return float(value)
        except Exception:
            return 60.0

    @api.model
    def _get_max_volume_reference(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_vendor_performance.max_volume_reference',
            '500000'
        )
        try:
            return float(value)
        except Exception:
            return 500000.0

    def action_run_monthly_scan(self):
        count = self.sudo().cron_monthly_vendor_performance_scan()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تشغيل تقييم كفاءة الموردين'),
                'message': _('تم حساب/تحديث %s تقييم مورد.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_monthly_vendor_performance_scan(self):
        partners = self.env['res.partner'].sudo().search([
            ('supplier_rank', '>', 0),
            ('active', '=', True),
        ])
        count = 0
        period = self._month_start(fields.Date.today())
        for partner in partners:
            self.compute_vendor_score(partner, period)
            count += 1
        return count

    @api.model
    def compute_vendor_score(self, partner, period_date=None):
        if not partner:
            return False

        period_start = self._month_start(period_date)
        period_end = self._month_end(period_start)

        po_domain = [
            ('partner_id', '=', partner.id),
            ('state', 'in', ['purchase', 'done']),
        ]

        # include orders either created/confirmed in the period or with receipts in the period
        orders = self.env['purchase.order'].sudo().search(po_domain)
        period_orders = self.env['purchase.order'].sudo()

        for po in orders:
            po_date = fields.Date.to_date(po.date_order) if po.date_order else False
            has_period_receipt = any(
                p.date_done and period_start <= fields.Date.to_date(p.date_done) <= period_end
                for p in po.picking_ids
            )
            if (po_date and period_start <= po_date <= period_end) or has_period_receipt:
                period_orders |= po

        received_qty = 0.0
        accepted_qty = 0.0
        rejected_qty = 0.0
        delivery_count = 0
        delayed_delivery_count = 0
        delay_days_total = 0.0
        total_purchase_value = sum(period_orders.mapped('amount_total'))
        successful_purchase_value = 0.0
        picking_ids = self.env['stock.picking'].sudo()

        for po in period_orders:
            order_qty = sum(po.order_line.mapped('product_qty'))
            done_pickings = po.picking_ids.filtered(
                lambda p: p.state == 'done' and p.picking_type_code == 'incoming'
            )
            period_pickings = done_pickings.filtered(
                lambda p: p.date_done and period_start <= fields.Date.to_date(p.date_done) <= period_end
            )
            if not period_pickings and done_pickings:
                period_pickings = done_pickings

            picking_ids |= period_pickings

            po_received_qty = 0.0
            for picking in period_pickings:
                delivery_count += 1
                for move in picking.move_ids_without_package:
                    if move.state == 'done':
                        qty = move.quantity or move.product_uom_qty or 0.0
                        received_qty += qty
                        po_received_qty += qty

                delay_days = self._get_delay_days(po, picking)
                if delay_days > 0:
                    delayed_delivery_count += 1
                    delay_days_total += delay_days

            accepted_qty += po_received_qty
            if order_qty and po_received_qty < order_qty:
                rejected_qty += max(0.0, order_qty - po_received_qty)

            if po_received_qty > 0:
                successful_purchase_value += po.amount_total

        if received_qty > 0:
            quality_score = max(0.0, min(100.0, (accepted_qty / received_qty) * 100.0))
        elif period_orders:
            quality_score = 50.0
        else:
            quality_score = 100.0

        if delivery_count > 0:
            avg_delay = delay_days_total / delivery_count
        else:
            avg_delay = 0.0

        delay_score = max(0.0, 100.0 - avg_delay * 5.0)

        penalty_count, open_penalty_count = self._get_penalty_counts(partner, period_start, period_end)
        penalty_score = max(0.0, 100.0 - penalty_count * 20.0 - open_penalty_count * 10.0)

        max_volume = self._get_max_volume_reference()
        volume_score = min(100.0, (successful_purchase_value / max_volume) * 100.0) if max_volume else 0.0

        final_score = (
            quality_score * 0.40 +
            delay_score * 0.25 +
            penalty_score * 0.20 +
            volume_score * 0.15
        )
        final_score = max(0.0, min(100.0, final_score))

        recommendation = self._recommendation(final_score, quality_score, delay_score, penalty_score)

        details = (
            'معادلة التقييم:\n'
            '40%% جودة التوريد + 25%% الالتزام بالوقت + 20%% سجل الجزاءات + 15%% حجم التعامل الناجح\n\n'
            'جودة التوريد: %.2f\n'
            'الالتزام بالوقت: %.2f\n'
            'سجل الجزاءات: %.2f\n'
            'حجم التعامل الناجح: %.2f\n'
            'التقييم النهائي: %.2f\n'
        ) % (quality_score, delay_score, penalty_score, volume_score, final_score)

        Score = self.env['port_said.vendor.performance.score'].sudo()
        score_rec = Score.search([
            ('partner_id', '=', partner.id),
            ('period_date', '=', period_start),
        ], limit=1)

        vals = {
            'partner_id': partner.id,
            'period_date': period_start,
            'quality_score': quality_score,
            'delay_score': delay_score,
            'penalty_score': penalty_score,
            'volume_score': volume_score,
            'final_score': final_score,
            'accepted_qty': accepted_qty,
            'received_qty': received_qty,
            'rejected_qty': rejected_qty,
            'purchase_order_count': len(period_orders),
            'successful_purchase_value': successful_purchase_value,
            'total_purchase_value': total_purchase_value,
            'delivery_count': delivery_count,
            'delayed_delivery_count': delayed_delivery_count,
            'average_delay_days': avg_delay,
            'penalty_count': penalty_count,
            'open_penalty_count': open_penalty_count,
            'recommendation': recommendation,
            'calculation_details': details,
            'state': 'computed',
        }

        if score_rec:
            score_rec.write(vals)
        else:
            score_rec = Score.create(vals)

        score_rec.purchase_order_ids = [(6, 0, period_orders.ids)]
        score_rec.picking_ids = [(6, 0, picking_ids.ids)]

        return score_rec

    def _get_delay_days(self, po, picking):
        planned = False

        # Prefer custom/standard commitment dates if available
        for fname in ['date_planned', 'effective_date', 'expected_date']:
            if fname in po._fields and po[fname]:
                planned = fields.Date.to_date(po[fname])
                break

        if not planned and po.order_line:
            dates = [fields.Date.to_date(l.date_planned) for l in po.order_line if l.date_planned]
            if dates:
                planned = min(dates)

        if not planned and po.date_order:
            planned = fields.Date.to_date(po.date_order)

        actual = fields.Date.to_date(picking.date_done) if picking.date_done else False

        if planned and actual and actual > planned:
            return (actual - planned).days
        return 0.0

    def _get_penalty_counts(self, partner, date_from, date_to):
        total = 0
        open_total = 0

        candidate_models = [
            'port_said.vendor.penalty',
            'port_said.vendor.penalty.alert',
            'port_said.penalty',
            'port_said.penalties',
            'penalties.said.port',
        ]

        for model_name in candidate_models:
            if model_name not in self.env:
                continue

            Model = self.env[model_name].sudo()

            partner_field = False
            for fname in ['partner_id', 'supplier_id', 'vendor_id']:
                if fname in Model._fields:
                    partner_field = fname
                    break
            if not partner_field:
                continue

            domain = [(partner_field, '=', partner.id)]

            date_field = False
            for fname in ['date', 'penalty_date', 'create_date']:
                if fname in Model._fields:
                    date_field = fname
                    break

            if date_field:
                domain += [(date_field, '>=', date_from), (date_field, '<=', date_to)]

            try:
                records = Model.search(domain)
            except Exception:
                continue

            total += len(records)

            if 'state' in Model._fields:
                open_records = records.filtered(lambda r: r.state not in ['done', 'closed', 'cancelled', 'paid'])
                open_total += len(open_records)
            elif 'active' in Model._fields:
                open_total += len(records.filtered(lambda r: r.active))
            else:
                open_total += len(records)

        return total, open_total

    def _recommendation(self, final_score, quality_score, delay_score, penalty_score):
        min_score = self._get_min_warning_score()

        if final_score < min_score:
            return (
                'تحذير: المورد عالي المخاطر. لا يوصى بالاعتماد عليه في الترسية إلا بعد مراجعة أسباب انخفاض التقييم، '
                'خصوصًا الجودة أو التأخير أو الجزاءات.'
            )

        if quality_score < 70:
            return 'يوصى بمراجعة جودة التوريدات السابقة قبل أي ترسية جديدة.'
        if delay_score < 70:
            return 'يوصى بوضع شرط جزائي أو متابعة زمنية أقوى بسبب تكرار التأخير.'
        if penalty_score < 70:
            return 'يوصى بمراجعة سجل الجزاءات قبل التعامل الجديد.'

        if final_score >= 85:
            return 'المورد ممتاز ويمكن اعتباره موردًا موثوقًا عند المفاضلة الفنية والمالية.'
        if final_score >= 70:
            return 'المورد جيد مع الاستمرار في المتابعة الدورية.'
        return 'المورد متوسط ويحتاج متابعة عند العمليات القادمة.'
