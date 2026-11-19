# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # بيانات تُسحب تلقائياً في ملف مرتب الموظف (المتطلب الوظيفي 8)
    spouse_works = fields.Boolean(string='الزوج/الزوجة يعمل')
    num_dependents = fields.Integer(string='عدد المعولين')
    fund_subscription_amount = fields.Float(string='قيمة اشتراك الصندوق')
