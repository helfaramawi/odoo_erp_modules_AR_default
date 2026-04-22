# -*- coding: utf-8 -*-
"""
إعدادات الحسابات المحاسبية لدفاتر التأمينات
=============================================
يُخزِّن الحسابات الافتراضية المُستخدَمة عند توليد القيود المحاسبية
تلقائياً من تفعيل/إفراج/مصادرة التأمين.

يُمتد على res.company ليكون multi-company.
"""
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ── حسابات التأمينات النقدية ─────────────────────────────────────────────
    insurance_cash_asset_account_id = fields.Many2one('account.account',
        string='حساب التأمينات النقدية (أصل)',
        help='الحساب المدين عند استلام تأمين نقدي. '
             'مثال: عُهَد التأمينات المؤقتة/النهائية.')

    insurance_cash_liability_account_id = fields.Many2one('account.account',
        string='حساب التأمينات النقدية (التزام)',
        help='الحساب الدائن مقابل الأصل: التزام بإرجاع التأمين للمورد.')

    # ── حسابات نظامية لخطابات الضمان ────────────────────────────────────────
    guarantee_memo_dr_account_id = fields.Many2one('account.account',
        string='حساب نظامي مدين - خطابات ضمان',
        help='حساب نظامي (off-balance-sheet) لإثبات خطاب الضمان المُستلَم. '
             'يجب أن يكون مُصنَّفاً MEMO_DR.')

    guarantee_memo_cr_account_id = fields.Many2one('account.account',
        string='حساب نظامي دائن - خطابات ضمان',
        help='حساب نظامي مقابل للنظامي المدين. يجب أن يكون مُصنَّفاً MEMO_CR.')

    # ── حسابات المصادرة (إيرادات) ───────────────────────────────────────────
    insurance_forfeiture_revenue_account_id = fields.Many2one('account.account',
        string='حساب إيرادات المصادرة',
        help='الحساب الدائن عند مصادرة التأمين (يُصبح إيراداً للمحافظة).')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    insurance_cash_asset_account_id = fields.Many2one(
        related='company_id.insurance_cash_asset_account_id',
        readonly=False)
    insurance_cash_liability_account_id = fields.Many2one(
        related='company_id.insurance_cash_liability_account_id',
        readonly=False)
    guarantee_memo_dr_account_id = fields.Many2one(
        related='company_id.guarantee_memo_dr_account_id',
        readonly=False)
    guarantee_memo_cr_account_id = fields.Many2one(
        related='company_id.guarantee_memo_cr_account_id',
        readonly=False)
    insurance_forfeiture_revenue_account_id = fields.Many2one(
        related='company_id.insurance_forfeiture_revenue_account_id',
        readonly=False)
