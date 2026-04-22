# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AssetDepreciationLine(models.Model):
    """
    قيد الإهلاك الدوري — Depreciation Line
    كل سطر = قيد محاسبي سنوي في account.move
    """
    _name = 'port_said.asset.depreciation.line'
    _description = 'قيد إهلاك دوري'
    _order = 'asset_id, sequence'

    asset_id = fields.Many2one(
        'port_said.fixed.asset', string='الأصل الثابت',
        required=True, ondelete='cascade', index=True
    )
    name = fields.Char(string='الوصف', required=True)
    sequence = fields.Integer(string='السنة رقم', default=1)
    amount = fields.Monetary(
        string='مبلغ الإهلاك (ج.م)', required=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        related='asset_id.currency_id'
    )
    depreciation_date = fields.Date(
        string='تاريخ الإهلاك', required=True
    )
    fiscal_year = fields.Char(string='السنة المالية')
    remaining_value = fields.Monetary(
        string='القيمة الدفترية المتبقية',
        currency_field='currency_id'
    )
    move_id = fields.Many2one(
        'account.move', string='قيد المحاسبة',
        readonly=True, ondelete='set null'
    )
    move_state = fields.Selection(
        related='move_id.state', string='حالة القيد'
    )

    def action_post(self):
        """إنشاء وترحيل قيد الإهلاك في account.move"""
        for line in self:
            if line.move_id:
                continue
            asset = line.asset_id
            cat = asset.category_id
            # تحقق من الحسابات
            if not cat.journal_id:
                raise UserError(_(f'يجب تحديد دفتر القيود في فئة الأصل "{cat.name}" قبل الترحيل'))
            if not cat.expense_account_id:
                raise UserError(_(f'يجب تحديد حساب مصروف الإهلاك في فئة "{cat.name}"'))
            if not cat.depreciation_account_id:
                raise UserError(_(f'يجب تحديد حساب مجمع الإهلاك في فئة "{cat.name}"'))

            move_vals = {
                'ref': f'إهلاك — {asset.asset_number} — السنة {line.sequence}',
                'date': line.depreciation_date,
                'journal_id': cat.journal_id.id,
                'line_ids': [
                    # مدين: مصروف الإهلاك
                    (0, 0, {
                        'account_id': cat.expense_account_id.id,
                        'name': f'مصروف إهلاك — {asset.name}',
                        'debit': line.amount,
                        'credit': 0.0,
                    }),
                    # دائن: مجمع الإهلاك
                    (0, 0, {
                        'account_id': cat.depreciation_account_id.id,
                        'name': f'مجمع إهلاك — {asset.name} — {asset.asset_number}',
                        'debit': 0.0,
                        'credit': line.amount,
                    }),
                ],
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            line.move_id = move

            asset.message_post(
                body=_(f'تم ترحيل قيد إهلاك السنة {line.sequence}: {line.amount:,.2f} ج.م')
            )

    def action_reverse(self):
        """عكس قيد الإهلاك — للتصحيح فقط"""
        self.ensure_one()
        if not self.move_id:
            raise UserError(_('لا يوجد قيد محاسبي لعكسه'))
        reversal = self.move_id._reverse_moves(
            default_values_list=[{'date': fields.Date.today()}]
        )
        self.move_id = False
        return reversal
