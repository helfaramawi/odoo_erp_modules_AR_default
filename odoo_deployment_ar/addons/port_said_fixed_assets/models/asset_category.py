# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssetCategory(models.Model):
    """
    فئات الأصول الثابتة — وفق معيار المحاسبة المصري رقم 10
    Egyptian Accounting Standard No. 10 — Fixed Assets & Depreciation
    """
    _name = 'port_said.asset.category'
    _description = 'فئة الأصل الثابت — Asset Category'
    _rec_name = 'name'
    _order = 'code'

    code = fields.Char(string='كود الفئة', required=True, size=10)
    name = fields.Char(string='اسم الفئة', required=True)
    name_en = fields.Char(string='Category Name (EN)')

    # ── إهلاك — Depreciation ─────────────────────────────────────
    method = fields.Selection([
        ('straight_line',    'القسط الثابت (Straight-Line)'),
        ('declining',        'القسط المتناقص (Declining Balance)'),
        ('sum_of_years',     'مجموع أرقام السنوات (Sum-of-Years)'),
        ('units_production', 'وحدات الإنتاج (Units of Production)'),
    ], string='طريقة الإهلاك', required=True, default='straight_line')

    # نسب الإهلاك وفق اللائحة المالية الحكومية المصرية
    depreciation_rate = fields.Float(
        string='معدل الإهلاك (%)',
        help='النسبة السنوية وفق اللائحة المالية: مباني 4%، أثاث 20%، سيارات 25%، حاسبات 33%'
    )
    useful_life_years = fields.Integer(
        string='العمر الإنتاجي (سنوات)',
        compute='_compute_useful_life', store=True
    )
    residual_value_pct = fields.Float(
        string='القيمة التخريدية (%)',
        default=0.0,
        help='نسبة القيمة المتبقية في نهاية العمر الإنتاجي'
    )

    # ── حسابات الأستاذ ──────────────────────────────────────────
    asset_account_id = fields.Many2one(
        'account.account', string='حساب الأصل',
        domain="[('account_type', 'not in', ['asset_receivable', 'liability_payable'])]"
    )
    depreciation_account_id = fields.Many2one(
        'account.account', string='حساب مجمع الإهلاك',
        help='الحساب المقابل — مجمع إهلاك الأصل'
    )
    expense_account_id = fields.Many2one(
        'account.account', string='حساب مصروف الإهلاك',
        help='حساب قيد الإهلاك الدوري — ينعكس على الحسابات الختامية'
    )
    gain_account_id = fields.Many2one(
        'account.account', string='حساب أرباح التصرف'
    )
    loss_account_id = fields.Many2one(
        'account.account', string='حساب خسائر التصرف'
    )

    journal_id = fields.Many2one(
        'account.journal', string='دفتر القيود',
        domain="[('type', 'in', ['general', 'misc'])]"
    )

    # ── إحصاء ───────────────────────────────────────────────────
    asset_count = fields.Integer(
        string='عدد الأصول', compute='_compute_asset_count'
    )
    active = fields.Boolean(default=True)
    notes = fields.Text(string='ملاحظات')

    @api.depends('depreciation_rate')
    def _compute_useful_life(self):
        for rec in self:
            rec.useful_life_years = (
                int(100 / rec.depreciation_rate)
                if rec.depreciation_rate > 0 else 0
            )

    def _compute_asset_count(self):
        for rec in self:
            rec.asset_count = self.env['port_said.fixed.asset'].search_count([
                ('category_id', '=', rec.id),
                ('state', '!=', 'disposed'),
            ])

    @api.constrains('depreciation_rate')
    def _check_rate(self):
        for rec in self:
            if rec.depreciation_rate < 0 or rec.depreciation_rate > 100:
                raise ValidationError(_('معدل الإهلاك يجب أن يكون بين 0 و 100'))

    def action_view_assets(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'أصول — {self.name}',
            'res_model': 'port_said.fixed.asset',
            'view_mode': 'list,form',
            'domain': [('category_id', '=', self.id)],
        }
