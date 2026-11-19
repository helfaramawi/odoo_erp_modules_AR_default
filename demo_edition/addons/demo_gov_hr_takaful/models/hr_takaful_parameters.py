# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrTakafulParameters(models.Model):
    _name = 'demo_gov.hr.takaful.parameters'
    _description = 'إعدادات صندوق التكافل — أكواد الحسابات ومبالغ الاستحقاقات المرجعية'

    name = fields.Char(string='الاسم', default='إعدادات صندوق التكافل', readonly=True)
    fund_account_id = fields.Many2one('account.account', string='حساب رصيد الصندوق')
    income_account_id = fields.Many2one('account.account', string='حساب إيرادات الاشتراكات')
    expense_account_id = fields.Many2one('account.account', string='حساب مصروفات الصرف')

    # مبالغ استحقاقات توضيحية فقط (زي المثال الوارد في وثيقة التصميم) —
    # تُخصَّص فعلياً بالاتفاق مع الجهة قبل أي استخدام حقيقي.
    marriage_payout = fields.Float(string='استحقاق الزواج', default=2000.0)
    birth_payout = fields.Float(string='استحقاق المولود', default=500.0)
    death_payout = fields.Float(string='استحقاق الوفاة', default=5000.0)

    @api.model
    def get_parameters(self):
        params = self.search([], limit=1)
        if not params:
            params = self.create({})
        return params
