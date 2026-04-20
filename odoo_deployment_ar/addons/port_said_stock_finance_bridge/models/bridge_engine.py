# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockFinanceBridgeEngine(models.AbstractModel):
    """
    المحرك الرئيسي لربط المخزن بالمحاسبة
    يُستدعى من أزرار الترحيل في كل نموذج حركة مخزنية
    """
    _name = 'stock.finance.bridge.engine'
    _description = 'محرك ربط المخزن بالمحاسبة'

    @api.model
    def _get_account_rule(self, movement_type, warehouse_id=None, product_category_id=None):
        """
        استخراج قاعدة الحسابات الأنسب بالترتيب:
        1. نوع + مستودع + فئة (الأكثر تحديداً)
        2. نوع + مستودع
        3. نوع + فئة
        4. نوع فقط (القاعدة الافتراضية)
        """
        Rule = self.env['stock.finance.account.rule']

        # الأكثر تحديداً أولاً
        searches = [
            [('movement_type', '=', movement_type),
             ('warehouse_id', '=', warehouse_id),
             ('product_category_id', '=', product_category_id)],
            [('movement_type', '=', movement_type),
             ('warehouse_id', '=', warehouse_id),
             ('product_category_id', '=', False)],
            [('movement_type', '=', movement_type),
             ('warehouse_id', '=', False),
             ('product_category_id', '=', product_category_id)],
            [('movement_type', '=', movement_type),
             ('warehouse_id', '=', False),
             ('product_category_id', '=', False)],
        ]
        for domain in searches:
            rule = Rule.search(domain + [('active', '=', True)], limit=1)
            if rule:
                return rule
        return None

    @api.model
    def _get_dimension(self, warehouse_id=None, product_category_id=None, dept=None):
        """استخراج البعد المالي الأنسب"""
        DimRule = self.env['stock.finance.dimension.rule']

        searches = []
        if warehouse_id and product_category_id:
            searches.append([('warehouse_id', '=', warehouse_id),
                              ('product_category_id', '=', product_category_id)])
        if warehouse_id:
            searches.append([('warehouse_id', '=', warehouse_id),
                              ('product_category_id', '=', False)])
        if product_category_id:
            searches.append([('warehouse_id', '=', False),
                              ('product_category_id', '=', product_category_id)])
        if dept:
            searches.append([('requesting_dept', '=', dept)])

        for domain in searches:
            rule = DimRule.search(domain + [('active', '=', True)],
                                  order='priority asc', limit=1)
            if rule:
                return rule.dimension_id
        return None

    @api.model
    def create_journal_entry(self, movement_type, ref, amount, date,
                             warehouse_id=None, product_category_id=None,
                             dept=None, narration=None, partner_id=None):
        """
        إنشاء قيد محاسبي من حركة مخزنية
        :return: account.move record or raise UserError
        """
        if amount <= 0:
            raise UserError(_('المبلغ يجب أن يكون موجباً لإنشاء القيد'))

        # استخراج القاعدة
        rule = self._get_account_rule(movement_type, warehouse_id, product_category_id)
        if not rule:
            raise UserError(_(
                f'لا توجد قاعدة حسابات لنوع الحركة: {movement_type}\n'
                f'يرجى إعداد القواعد من: إعدادات المخزن ← قواعد الحسابات'
            ))

        # استخراج البعد المالي
        dimension = self._get_dimension(warehouse_id, product_category_id, dept)

        # إنشاء القيد
        move_vals = {
            'journal_id': rule.journal_id.id,
            'date': date,
            'ref': ref,
            'narration': narration or ref,
            'line_ids': [
                (0, 0, {
                    'account_id': rule.debit_account_id.id,
                    'name': narration or ref,
                    'debit': amount,
                    'credit': 0.0,
                    'partner_id': partner_id,
                }),
                (0, 0, {
                    'account_id': rule.credit_account_id.id,
                    'name': narration or ref,
                    'debit': 0.0,
                    'credit': amount,
                    'partner_id': partner_id,
                }),
            ],
        }

        move = self.env['account.move'].create(move_vals)
        move.action_post()

        # تسجيل في السجل
        self.env['stock.finance.bridge.log'].create({
            'movement_type': movement_type,
            'movement_ref': ref,
            'move_id': move.id,
            'amount': amount,
            'dimension_id': dimension.id if dimension else False,
            'debit_account_id': rule.debit_account_id.id,
            'credit_account_id': rule.credit_account_id.id,
            'state': 'posted',
        })

        return move


# ══ Mixins للنماذج ══════════════════════════════════════════════

class StockIssuePermitBridge(models.Model):
    """إضافة زر إنشاء قيد لإذن الصرف"""
    _inherit = 'stock.issue.permit'

    journal_entry_id = fields.Many2one(
        'account.move', string='القيد المحاسبي',
        readonly=True, copy=False,
    )
    journal_entry_state = fields.Char(
        string='حالة القيد',
        compute='_compute_je_state',
    )

    @api.depends('journal_entry_id', 'journal_entry_id.state')
    def _compute_je_state(self):
        for rec in self:
            if rec.journal_entry_id:
                states = {'draft': 'مسودة', 'posted': 'مرحَّل', 'cancel': 'ملغي'}
                rec.journal_entry_state = states.get(rec.journal_entry_id.state, '')
            else:
                rec.journal_entry_state = 'لم يُنشأ بعد'

    def action_create_journal_entry(self):
        """إنشاء القيد المحاسبي لإذن الصرف"""
        self.ensure_one()
        if self.state != 'posted':
            raise UserError(_('يجب ترحيل إذن الصرف أولاً'))
        if self.journal_entry_id:
            raise UserError(_('تم إنشاء القيد المحاسبي مسبقاً'))
        if not self.total_value:
            raise UserError(_('القيمة الإجمالية للإذن صفر — لا يمكن إنشاء قيد'))

        warehouse_id = self.warehouse_id.id if self.warehouse_id else None
        # أخذ فئة أول صنف
        cat_id = (self.line_ids[0].product_id.categ_id.id
                  if self.line_ids and self.line_ids[0].product_id else None)

        move = self.env['stock.finance.bridge.engine'].create_journal_entry(
            movement_type='issue',
            ref=self.name,
            amount=self.total_value,
            date=self.issue_date,
            warehouse_id=warehouse_id,
            product_category_id=cat_id,
            dept=self.requesting_dept,
            narration=f'إذن صرف {self.name} — {self.requesting_dept or ""} — {self.purpose or ""}',
        )
        self.journal_entry_id = move
        # تحديث رابط القيد المحاسبي في سجل الصرف المخزوني
        if self.issue_register_line_id:
            self.issue_register_line_id.journal_entry_id = move
        # تحديث الحالة المحاسبية (finance_status مُعرَّف في stock_bridge.py)
        self.finance_status = 'posted'
        self.message_post(
            body=_(f'تم إنشاء القيد المحاسبي: {move.name} بمبلغ {self.total_value:,.2f} ج.م')
        )
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_journal_entry(self):
        self.ensure_one()
        if not self.journal_entry_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.journal_entry_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class StockAdditionPermitBridge(models.Model):
    """إضافة زر إنشاء قيد لإذن الإضافة"""
    _inherit = 'stock.addition.permit'

    journal_entry_id = fields.Many2one(
        'account.move', string='القيد المحاسبي',
        readonly=True, copy=False,
    )

    def action_create_journal_entry(self):
        self.ensure_one()
        if self.state != 'posted':
            raise UserError(_('يجب ترحيل إذن الإضافة أولاً'))
        if self.journal_entry_id:
            raise UserError(_('تم إنشاء القيد المحاسبي مسبقاً'))

        qty = self.qty or 0
        unit_price = self.product_id.standard_price if self.product_id else 0
        amount = qty * unit_price
        if amount <= 0:
            raise UserError(_('لا يمكن إنشاء قيد بقيمة صفر — يرجى تحديد سعر الصنف'))

        warehouse_id = self.warehouse_id.id if self.warehouse_id else None
        cat_id = self.product_id.categ_id.id if self.product_id else None

        move = self.env['stock.finance.bridge.engine'].create_journal_entry(
            movement_type='addition',
            ref=self.name,
            amount=amount,
            date=self.permit_date,
            warehouse_id=warehouse_id,
            product_category_id=cat_id,
            partner_id=self.partner_id.id if self.partner_id else None,
            narration=f'إذن إضافة {self.name} — {self.product_id.name if self.product_id else ""}',
        )
        self.journal_entry_id = move
        self.message_post(body=_(f'تم إنشاء القيد المحاسبي: {move.name}'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }


class StockTransferPermitBridge(models.Model):
    """إضافة زر إنشاء قيد لإذن التحويل"""
    _inherit = 'stock.transfer.permit'

    journal_entry_id = fields.Many2one(
        'account.move', string='القيد المحاسبي',
        readonly=True, copy=False,
    )

    def action_create_journal_entry(self):
        self.ensure_one()
        if self.state not in ('posted', 'received'):
            raise UserError(_('يجب ترحيل إذن التحويل أولاً'))
        if self.journal_entry_id:
            raise UserError(_('تم إنشاء القيد المحاسبي مسبقاً'))
        if not self.total_value:
            raise UserError(_('القيمة الإجمالية صفر'))

        move = self.env['stock.finance.bridge.engine'].create_journal_entry(
            movement_type='transfer',
            ref=self.name,
            amount=self.total_value,
            date=self.transfer_date,
            warehouse_id=self.from_warehouse_id.id if self.from_warehouse_id else None,
            narration=f'إذن تحويل {self.name} — من {self.from_dept or ""} إلى {self.to_dept or ""}',
        )
        self.journal_entry_id = move
        self.message_post(body=_(f'تم إنشاء القيد المحاسبي: {move.name}'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }


class StockReturnPermitBridge(models.Model):
    """إضافة زر إنشاء قيد لإذن الارتجاع"""
    _inherit = 'stock.return.permit'

    journal_entry_id = fields.Many2one(
        'account.move', string='القيد المحاسبي',
        readonly=True, copy=False,
    )

    def action_create_journal_entry(self):
        self.ensure_one()
        if self.state != 'posted':
            raise UserError(_('يجب ترحيل إذن الارتجاع أولاً'))
        if self.journal_entry_id:
            raise UserError(_('تم إنشاء القيد المحاسبي مسبقاً'))
        if not self.total_value:
            raise UserError(_('القيمة الإجمالية صفر'))

        move = self.env['stock.finance.bridge.engine'].create_journal_entry(
            movement_type='return',
            ref=self.name,
            amount=self.total_value,
            date=self.return_date,
            warehouse_id=self.warehouse_id.id if self.warehouse_id else None,
            dept=self.returning_dept,
            narration=f'إذن ارتجاع {self.name} — {self.returning_dept or ""}',
        )
        self.journal_entry_id = move
        self.message_post(body=_(f'تم إنشاء القيد المحاسبي: {move.name}'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }
