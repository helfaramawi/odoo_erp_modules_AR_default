# -*- coding: utf-8 -*-
from odoo import models, fields


class HrPensionPlan(models.Model):
    _name = 'demo_gov.hr.pension.plan'
    _description = 'خطة معاش أو تأمين — Benefit plans (FDD-HR-08)'

    name = fields.Char(string='اسم الخطة', required=True)
    plan_type = fields.Selection([
        ('retirement_pension', 'معاش الشيخوخة'),
        ('comprehensive_health', 'التأمين الصحي الشامل'),
    ], string='نوع الخطة', required=True)
    # نسب الخصم تتغير وفقاً لقانون التأمينات الاجتماعية والمعاشات — لازم
    # الإدارة المالية تراجعها دورياً.
    employee_contribution_pct = fields.Float(string='نسبة خصم الموظف %')
    employer_contribution_pct = fields.Float(string='نسبة خصم الجهة %')
    description = fields.Text(string='وصف الخطة')
    active = fields.Boolean(string='نشطة', default=True)
