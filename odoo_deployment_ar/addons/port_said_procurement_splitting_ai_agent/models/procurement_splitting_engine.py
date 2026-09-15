# -*- coding: utf-8 -*-
from collections import Counter, defaultdict
from datetime import timedelta
from odoo import api, fields, models, _


class PortSaidProcurementSplittingEngine(models.TransientModel):
    _name = 'port_said.procurement.splitting.engine'
    _description = 'محرك كشف تجزئة المشتريات'

    @api.model
    def _get_threshold_amount(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_procurement_splitting.threshold_amount',
            '50000'
        )
        try:
            return float(value)
        except Exception:
            return 50000.0

    @api.model
    def _get_near_ratio(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_procurement_splitting.near_threshold_ratio',
            '0.75'
        )
        try:
            return float(value)
        except Exception:
            return 0.75

    @api.model
    def _get_window_days(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_procurement_splitting.window_days',
            '30'
        )
        try:
            return int(value)
        except Exception:
            return 30

    @api.model
    def _get_scan_days(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_procurement_splitting.scan_days',
            '90'
        )
        try:
            return int(value)
        except Exception:
            return 90

    def action_run_full_scan(self):
        created = self.sudo()._run_full_scan()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تشغيل فحص تجزئة المشتريات'),
                'message': _('تم إنشاء/تحديث %s تنبيه محتمل.') % created,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_daily_procurement_splitting_scan(self):
        return self.sudo()._run_full_scan()

    @api.model
    def _run_full_scan(self):
        created = 0
        if 'purchase.order' in self.env:
            scan_days = self._get_scan_days()
            date_from = fields.Date.today() - timedelta(days=scan_days)
            orders = self.env['purchase.order'].sudo().search([
                ('date_order', '>=', fields.Datetime.to_string(date_from)),
                ('state', 'in', ['purchase', 'done']),
                ('partner_id', '!=', False),
            ])
            created += self._scan_purchase_orders(orders)

        # Optional dynamic requisition scan if model exists.
        if 'port_said.requisition' in self.env:
            reqs = self.env['port_said.requisition'].sudo().search([], limit=1000)
            created += self._scan_requisitions_dynamic(reqs)

        return created

    @api.model
    def scan_purchase_order(self, po):
        if not po or po._name != 'purchase.order':
            return 0
        date_to = fields.Date.to_date(po.date_order) if po.date_order else fields.Date.today()
        date_from = date_to - timedelta(days=self._get_window_days())
        orders = self.env['purchase.order'].sudo().search([
            ('partner_id', '=', po.partner_id.id),
            ('date_order', '>=', fields.Datetime.to_string(date_from)),
            ('date_order', '<=', fields.Datetime.to_string(date_to + timedelta(days=1))),
            ('state', 'in', ['purchase', 'done']),
        ])
        return self._scan_purchase_orders(orders, source_record=po)

    def _scan_purchase_orders(self, orders, source_record=False):
        created = 0
        threshold = self._get_threshold_amount()
        ratio = self._get_near_ratio()
        lower = threshold * ratio
        window_days = self._get_window_days()

        grouped = defaultdict(lambda: self.env['purchase.order'])
        for po in orders:
            if po.amount_total and lower <= po.amount_total < threshold:
                grouped[po.partner_id] |= po

        for supplier, supplier_orders in grouped.items():
            if len(supplier_orders) < 3:
                continue

            sorted_orders = supplier_orders.sorted(lambda x: x.date_order or fields.Datetime.now())
            for anchor in sorted_orders:
                anchor_date = fields.Date.to_date(anchor.date_order) if anchor.date_order else fields.Date.today()
                win_from = anchor_date - timedelta(days=window_days)
                win_to = anchor_date + timedelta(days=window_days)

                window_orders = sorted_orders.filtered(
                    lambda o: o.date_order and win_from <= fields.Date.to_date(o.date_order) <= win_to
                )

                total = sum(window_orders.mapped('amount_total'))
                if len(window_orders) >= 3 and total > threshold:
                    created += self._create_po_alert(
                        supplier=supplier,
                        orders=window_orders,
                        source_record=source_record or anchor,
                        threshold=threshold,
                        lower=lower,
                        date_from=win_from,
                        date_to=win_to,
                    )
                    break

        return created

    def _scan_requisitions_dynamic(self, reqs):
        # Conservative placeholder: only scans if common amount/vendor fields exist.
        created = 0
        threshold = self._get_threshold_amount()
        lower = threshold * self._get_near_ratio()

        buckets = defaultdict(list)
        for req in reqs:
            amount = self._safe_amount(req)
            partner = self._safe_partner(req)
            if partner and amount and lower <= amount < threshold:
                buckets[partner.id].append(req)

        for partner_id, records in buckets.items():
            if len(records) >= 3:
                partner = self.env['res.partner'].browse(partner_id)
                total = sum(self._safe_amount(r) for r in records)
                if total > threshold:
                    source = records[0]
                    created += self._create_generic_alert(
                        source_record=source,
                        supplier=partner,
                        total_amount=total,
                        count=len(records),
                        threshold=threshold,
                        lower=lower,
                        detection_type='same_supplier_near_threshold',
                        reason='تم رصد عدة طلبات احتياج لنفس المورد بقيم قريبة من حد الاعتماد، مما قد يشير إلى تجزئة مشتريات محتملة.',
                    )
        return created

    def _safe_amount(self, rec):
        for fname in ['amount_total', 'total_amount', 'amount_requested', 'estimated_amount']:
            if fname in rec._fields:
                try:
                    return float(rec[fname] or 0)
                except Exception:
                    return 0.0
        return 0.0

    def _safe_partner(self, rec):
        for fname in ['partner_id', 'vendor_id', 'supplier_id']:
            if fname in rec._fields and rec[fname]:
                return rec[fname]
        return False

    def _department_name(self, po):
        for fname in ['department_id', 'requesting_department_id']:
            if fname in po._fields and po[fname]:
                return po[fname].display_name
        if 'user_id' in po._fields and po.user_id:
            return po.user_id.display_name
        return ''

    def _product_summary(self, orders):
        names = []
        categs = []
        for po in orders:
            for line in po.order_line:
                if line.product_id:
                    names.append(line.product_id.display_name)
                    if line.product_id.categ_id:
                        categs.append(line.product_id.categ_id.display_name)

        product_counts = Counter(names)
        categ_counts = Counter(categs)

        top_products = [x[0] for x in product_counts.most_common(5)]
        top_categs = [x[0] for x in categ_counts.most_common(5)]

        parts = []
        if top_products:
            parts.append('أكثر الأصناف تكرارًا: ' + '، '.join(top_products))
        if top_categs:
            parts.append('أكثر التصنيفات تكرارًا: ' + '، '.join(top_categs))
        return '\n'.join(parts)

    def _is_year_end_pattern(self, orders):
        for po in orders:
            if po.date_order:
                d = fields.Date.to_date(po.date_order)
                if d.month in [5, 6, 12]:
                    return True
        return False

    def _risk_score(self, order_count, total, threshold, year_end=False):
        score = 35
        score += min(30, order_count * 8)
        if total >= threshold * 2:
            score += 20
        elif total >= threshold * 1.5:
            score += 12
        elif total > threshold:
            score += 8
        if year_end:
            score += 10
        return min(100, score)

    def _recommendation(self, risk_score):
        if risk_score >= 85:
            return 'تصعيد فوري للمراجعة الداخلية وإيقاف الاعتماد لحين التحقق من عدم وجود تجزئة متعمدة.'
        if risk_score >= 65:
            return 'عرض العمليات على السلطة المختصة وطلب مذكرة تبرير تفصيلية قبل الاستكمال.'
        if risk_score >= 45:
            return 'مراجعة العمليات المرتبطة والتحقق من مبرر تعدد الأوامر.'
        return 'متابعة دورية دون إيقاف إجرائي.'

    def _create_po_alert(self, supplier, orders, source_record, threshold, lower, date_from, date_to):
        total = sum(orders.mapped('amount_total'))
        order_count = len(orders)
        year_end = self._is_year_end_pattern(orders)
        detection_type = 'year_end_pattern' if year_end else 'same_supplier_near_threshold'
        risk = self._risk_score(order_count, total, threshold, year_end=year_end)

        reason = (
            'تم رصد %s أوامر شراء لنفس المورد خلال فترة قصيرة بقيم أقل من حد الاعتماد وأعلى من نطاق الاشتباه.\n'
            'إجمالي العمليات: %.2f\n'
            'حد الاعتماد: %.2f\n'
            'هذا قد يشير إلى تجزئة مشتريات محتملة لتفادي موافقة أعلى أو لجنة مختصة.'
        ) % (order_count, total, threshold)

        product_summary = self._product_summary(orders)
        if product_summary:
            reason += '\n' + product_summary

        return self._create_generic_alert(
            source_record=source_record,
            supplier=supplier,
            total_amount=total,
            count=order_count,
            threshold=threshold,
            lower=lower,
            detection_type=detection_type,
            reason=reason,
            purchase_orders=orders,
            date_from=date_from,
            date_to=date_to,
            product_summary=product_summary,
            risk_score=risk,
        )

    def _create_generic_alert(self, source_record, supplier, total_amount, count, threshold, lower,
                              detection_type, reason, purchase_orders=False, date_from=False, date_to=False,
                              product_summary='', risk_score=False):
        Alert = self.env['port_said.procurement.splitting.alert'].sudo()
        date_from = date_from or (fields.Date.today() - timedelta(days=self._get_window_days()))
        date_to = date_to or fields.Date.today()
        risk_score = risk_score if risk_score is not False else self._risk_score(count, total_amount, threshold)

        domain = [
            ('supplier_id', '=', supplier.id if supplier else False),
            ('date_from', '=', date_from),
            ('date_to', '=', date_to),
            ('detection_type', '=', detection_type),
        ]

        vals = {
            'supplier_id': supplier.id if supplier else False,
            'department_name': self._department_name(source_record) if source_record and source_record._name == 'purchase.order' else '',
            'source_model': source_record._name if source_record else False,
            'source_res_id': source_record.id if source_record else 0,
            'source_display_name': source_record.display_name if source_record else 'فحص عام',
            'threshold_amount': threshold,
            'lower_limit_amount': lower,
            'total_amount': total_amount,
            'order_count': count,
            'date_from': date_from,
            'date_to': date_to,
            'window_days': self._get_window_days(),
            'detection_type': detection_type,
            'risk_score': risk_score,
            'reason': reason,
            'recommendation': self._recommendation(risk_score),
            'suspected_product_names': product_summary,
        }

        existing = Alert.search(domain, limit=1)
        if existing:
            existing.write(vals)
            if purchase_orders:
                existing.purchase_order_ids = [(6, 0, purchase_orders.ids)]
            return 0

        alert = Alert.create(vals)
        if purchase_orders:
            alert.purchase_order_ids = [(6, 0, purchase_orders.ids)]
        return 1
