# -*- coding: utf-8 -*-
from odoo import fields, models


class StockFinanceBridgeLog(models.Model):
    """سجل القيود المحاسبية المنشأة من حركات المخزن"""
    _name = 'stock.finance.bridge.log'
    _description = 'سجل ربط المخزن بالمحاسبة'
    _rec_name = 'movement_ref'
    _order = 'create_date desc'

    movement_type = fields.Selection([
        ('addition',  'إذن إضافة'),
        ('issue',     'إذن صرف'),
        ('transfer',  'إذن تحويل'),
        ('return',    'إذن ارتجاع'),
        ('scrap',     'إتلاف'),
        ('adjust_in', 'تسوية زيادة'),
        ('adjust_out','تسوية نقص'),
    ], string='نوع الحركة', required=True)

    movement_ref = fields.Char(string='مرجع الحركة', required=True)
    move_id = fields.Many2one('account.move', string='القيد المحاسبي', readonly=True)
    amount = fields.Monetary(string='المبلغ', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    dimension_id = fields.Many2one('financial.dimension', string='البعد المالي')
    debit_account_id = fields.Many2one('account.account', string='الحساب المدين', readonly=True)
    credit_account_id = fields.Many2one('account.account', string='الحساب الدائن', readonly=True)
    state = fields.Selection([
        ('posted', 'مرحَّل'),
        ('error',  'خطأ'),
        ('manual', 'يدوي'),
    ], string='الحالة', default='posted')
    error_message = fields.Text(string='رسالة الخطأ')
    notes = fields.Text(string='ملاحظات')
