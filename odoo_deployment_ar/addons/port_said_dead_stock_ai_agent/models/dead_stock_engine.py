# -*- coding: utf-8 -*-
import re
from datetime import timedelta
from odoo import api, fields, models, _


class PortSaidDeadStockEngine(models.TransientModel):
    _name = 'port_said.dead.stock.engine'
    _description = 'محرك كشف المخزون الراكد وبطيء الحركة'

    @api.model
    def _get_slow_days(self):
        return int(float(self.env['ir.config_parameter'].sudo().get_param(
            'port_said_dead_stock.slow_days', '180'
        )))

    @api.model
    def _get_dead_days(self):
        return int(float(self.env['ir.config_parameter'].sudo().get_param(
            'port_said_dead_stock.dead_days', '365'
        )))

    @api.model
    def _get_high_value_threshold(self):
        return float(self.env['ir.config_parameter'].sudo().get_param(
            'port_said_dead_stock.high_value_threshold', '10000'
        ))

    @api.model
    def _get_overstock_months(self):
        return int(float(self.env['ir.config_parameter'].sudo().get_param(
            'port_said_dead_stock.overstock_months', '24'
        )))

    def action_run_full_scan(self):
        count = self.sudo().cron_monthly_dead_stock_scan()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تشغيل فحص المخزون الراكد'),
                'message': _('تم إنشاء/تحديث %s تنبيه مخزون راكد أو بطيء الحركة.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_monthly_dead_stock_scan(self):
        Product = self.env['product.product'].sudo()
        products = Product.search([
            ('type', 'in', ['product', 'consu']),
            ('active', '=', True),
        ])
        count = 0
        for product in products:
            count += self._scan_product(product)
        count += self._scan_duplicate_products(products)
        return count

    def _scan_product(self, product):
        if product.qty_available <= 0:
            return 0

        today = fields.Date.today()
        slow_days = self._get_slow_days()
        dead_days = self._get_dead_days()
        high_value_threshold = self._get_high_value_threshold()

        last_out_move = self._get_last_outgoing_move(product)
        last_in_date = self._get_last_incoming_date(product)

        if last_out_move and last_out_move.date:
            last_out_date = fields.Date.to_date(last_out_move.date)
            days_no_movement = (today - last_out_date).days
        else:
            last_out_date = False
            days_no_movement = 9999

        qty_available = product.qty_available
        standard_price = product.standard_price or 0.0
        stock_value = qty_available * standard_price

        movement_count_6m, movement_count_12m, outgoing_qty_12m = self._movement_stats(product)

        created = 0

        if days_no_movement >= dead_days and stock_value >= high_value_threshold:
            created += self._create_or_update_alert(
                product=product,
                alert_type='high_value_dead',
                last_out_move=last_out_move,
                last_out_date=last_out_move.date if last_out_move else False,
                last_in_date=last_in_date,
                days_no_movement=days_no_movement,
                qty_available=qty_available,
                standard_price=standard_price,
                stock_value=stock_value,
                movement_count_6m=movement_count_6m,
                movement_count_12m=movement_count_12m,
                outgoing_qty_12m=outgoing_qty_12m,
            )

        elif days_no_movement >= dead_days:
            created += self._create_or_update_alert(
                product=product,
                alert_type='dead_12m',
                last_out_move=last_out_move,
                last_out_date=last_out_move.date if last_out_move else False,
                last_in_date=last_in_date,
                days_no_movement=days_no_movement,
                qty_available=qty_available,
                standard_price=standard_price,
                stock_value=stock_value,
                movement_count_6m=movement_count_6m,
                movement_count_12m=movement_count_12m,
                outgoing_qty_12m=outgoing_qty_12m,
            )

        elif days_no_movement >= slow_days:
            created += self._create_or_update_alert(
                product=product,
                alert_type='slow_6m',
                last_out_move=last_out_move,
                last_out_date=last_out_move.date if last_out_move else False,
                last_in_date=last_in_date,
                days_no_movement=days_no_movement,
                qty_available=qty_available,
                standard_price=standard_price,
                stock_value=stock_value,
                movement_count_6m=movement_count_6m,
                movement_count_12m=movement_count_12m,
                outgoing_qty_12m=outgoing_qty_12m,
            )

        if self._is_overstock(product, qty_available, outgoing_qty_12m):
            created += self._create_or_update_alert(
                product=product,
                alert_type='overstock',
                last_out_move=last_out_move,
                last_out_date=last_out_move.date if last_out_move else False,
                last_in_date=last_in_date,
                days_no_movement=days_no_movement,
                qty_available=qty_available,
                standard_price=standard_price,
                stock_value=stock_value,
                movement_count_6m=movement_count_6m,
                movement_count_12m=movement_count_12m,
                outgoing_qty_12m=outgoing_qty_12m,
            )

        return created

    def _get_last_outgoing_move(self, product):
        return self.env['stock.move'].sudo().search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('location_dest_id.usage', 'in', ['customer', 'inventory', 'production']),
        ], order='date desc', limit=1)

    def _get_last_incoming_date(self, product):
        move = self.env['stock.move'].sudo().search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('location_id.usage', 'in', ['supplier', 'inventory', 'production']),
            ('location_dest_id.usage', '=', 'internal'),
        ], order='date desc', limit=1)
        return move.date if move else False

    def _movement_stats(self, product):
        today = fields.Datetime.now()
        six_months = today - timedelta(days=180)
        twelve_months = today - timedelta(days=365)

        moves_6m = self.env['stock.move'].sudo().search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('date', '>=', six_months),
            ('location_dest_id.usage', 'in', ['customer', 'inventory', 'production']),
        ])

        moves_12m = self.env['stock.move'].sudo().search([
            ('product_id', '=', product.id),
            ('state', '=', 'done'),
            ('date', '>=', twelve_months),
            ('location_dest_id.usage', 'in', ['customer', 'inventory', 'production']),
        ])

        qty_12m = sum(moves_12m.mapped('quantity')) if 'quantity' in self.env['stock.move']._fields else sum(moves_12m.mapped('product_uom_qty'))

        return len(moves_6m), len(moves_12m), qty_12m

    def _is_overstock(self, product, qty_available, outgoing_qty_12m):
        if qty_available <= 0:
            return False
        if outgoing_qty_12m <= 0 and qty_available > 0:
            return True

        monthly_consumption = outgoing_qty_12m / 12.0
        if monthly_consumption <= 0:
            return True

        coverage_months = qty_available / monthly_consumption
        return coverage_months >= self._get_overstock_months()

    def _recommendation(self, alert_type, stock_value, days_no_movement):
        if alert_type == 'high_value_dead':
            return (
                'إجراء عاجل: مراجعة الصنف عالي القيمة الراكد، ودراسة إعادة توزيعه على إدارة أخرى أو التصرف فيه وفق الإجراءات الرسمية.'
            ), 'redistribute'

        if alert_type == 'dead_12m':
            return (
                'الصنف راكد لأكثر من 12 شهر. يوصى بمراجعة الاحتياج الفعلي، ووقف الشراء الجديد، ودراسة البيع أو إعادة التوزيع.'
            ), 'sell'

        if alert_type == 'slow_6m':
            return (
                'الصنف بطيء الحركة لأكثر من 6 أشهر. يوصى بتخفيض الشراء ومراجعة خطة الاحتياج قبل طلب كميات جديدة.'
            ), 'reduce_purchase'

        if alert_type == 'overstock':
            return (
                'الرصيد يغطي فترة طويلة مقارنة بالاستهلاك السنوي. يوصى بمراجعة الحد الاقتصادي للتخزين وتقليل الشراء المستقبلي.'
            ), 'review_need'

        if alert_type == 'duplicate_name':
            return (
                'يوجد أصناف متشابهة في الاسم. يوصى بمراجعة التكويد ودمج الأصناف المتكررة إن كانت تمثل نفس الصنف فعليًا.'
            ), 'merge_duplicate'

        return 'مراجعة الصنف بواسطة المخازن والإدارة المالية.', 'review_need'

    def _reason(self, alert_type, product, stock_value, days_no_movement, movement_count_12m):
        if alert_type == 'high_value_dead':
            return 'الصنف لم يتم صرفه لمدة %s يوم مع قيمة مخزون مجمدة %.2f، وهي أعلى من حد القيمة العالية.' % (days_no_movement, stock_value)
        if alert_type == 'dead_12m':
            return 'الصنف لم يتم صرفه لمدة %s يوم، مما يجعله راكدًا وفق قاعدة 12 شهر.' % days_no_movement
        if alert_type == 'slow_6m':
            return 'الصنف لم يتم صرفه لمدة %s يوم، مما يجعله بطيء الحركة وفق قاعدة 6 أشهر.' % days_no_movement
        if alert_type == 'overstock':
            return 'الرصيد الحالي كبير مقارنة بكمية الصرف خلال آخر 12 شهر. عدد حركات الصرف خلال 12 شهر: %s.' % movement_count_12m
        if alert_type == 'duplicate_name':
            return 'يوجد أصناف أخرى بأسماء متقاربة قد تؤدي إلى تكرار التخزين أو الشراء.'
        return ''

    def _create_or_update_alert(self, product, alert_type, last_out_move, last_out_date, last_in_date,
                                days_no_movement, qty_available, standard_price, stock_value,
                                movement_count_6m, movement_count_12m, outgoing_qty_12m,
                                duplicate_products=False):
        Alert = self.env['port_said.dead.stock.alert'].sudo()
        recommendation, recommendation_type = self._recommendation(alert_type, stock_value, days_no_movement)

        vals = {
            'product_id': product.id,
            'qty_available': qty_available,
            'standard_price': standard_price,
            'stock_value': stock_value,
            'last_outgoing_move_id': last_out_move.id if last_out_move else False,
            'last_outgoing_date': last_out_date,
            'last_incoming_date': last_in_date,
            'days_no_movement': days_no_movement,
            'movement_count_6m': movement_count_6m,
            'movement_count_12m': movement_count_12m,
            'outgoing_qty_12m': outgoing_qty_12m,
            'alert_type': alert_type,
            'recommendation_type': recommendation_type,
            'reason': self._reason(alert_type, product, stock_value, days_no_movement, movement_count_12m),
            'recommendation': recommendation,
        }

        existing = Alert.search([
            ('product_id', '=', product.id),
            ('alert_type', '=', alert_type),
        ], limit=1)

        if existing:
            existing.write(vals)
            if duplicate_products:
                existing.duplicate_product_ids = [(6, 0, duplicate_products.ids)]
            return 0

        alert = Alert.create(vals)
        if duplicate_products:
            alert.duplicate_product_ids = [(6, 0, duplicate_products.ids)]
        return 1

    def _normalize_name(self, name):
        if not name:
            return ''
        txt = name.lower()
        txt = re.sub(r'[\W_]+', ' ', txt, flags=re.UNICODE)
        ignore = {'the', 'and', 'for', 'pcs', 'piece', 'شركة', 'صنف', 'عدد', 'قطعة'}
        tokens = [t for t in txt.split() if len(t) >= 3 and t not in ignore]
        return ' '.join(sorted(tokens))

    def _scan_duplicate_products(self, products):
        created = 0
        buckets = {}
        for product in products:
            key = self._normalize_name(product.display_name)
            if not key:
                continue
            buckets.setdefault(key, self.env['product.product'])
            buckets[key] |= product

        for key, group in buckets.items():
            if len(group) < 2:
                continue
            for product in group:
                if product.qty_available <= 0:
                    continue
                stock_value = product.qty_available * (product.standard_price or 0)
                created += self._create_or_update_alert(
                    product=product,
                    alert_type='duplicate_name',
                    last_out_move=self._get_last_outgoing_move(product),
                    last_out_date=False,
                    last_in_date=self._get_last_incoming_date(product),
                    days_no_movement=0,
                    qty_available=product.qty_available,
                    standard_price=product.standard_price or 0,
                    stock_value=stock_value,
                    movement_count_6m=0,
                    movement_count_12m=0,
                    outgoing_qty_12m=0,
                    duplicate_products=group - product,
                )
        return created
