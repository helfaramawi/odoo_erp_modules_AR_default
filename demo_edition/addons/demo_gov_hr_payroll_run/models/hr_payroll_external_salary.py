# -*- coding: utf-8 -*-
from odoo import models, fields


class HrPayrollExternalSalary(models.Model):
    _name = 'demo_gov.hr.payroll.external.salary'
    _description = 'مرتب العاملين بالخارج — المتطلب الوظيفي 9'
    _order = 'name'

    # هؤلاء غير مسجَّلين كموظفين بالنظام (منتدبون/معارون لجهات أخرى ومازالت
    # هذه الجهة تتولى صرف مرتباتهم)، لذلك تُدرج بياناتهم مباشرة بدل الربط
    # بسجل hr.employee.
    name = fields.Char(string='الاسم', required=True)
    national_id = fields.Char(string='الرقم القومي', size=14)
    work_entity = fields.Char(string='جهة العمل الحالية')
    bank_code = fields.Char(string='كود البنك')
    bank_branch = fields.Char(string='اسم الفرع')
    bank_account_number = fields.Char(string='رقم الحساب البنكي')
    amount = fields.Float(string='المبلغ الشهري')
    notes = fields.Char(string='ملاحظات')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_national_id', 'unique(national_id)',
         'هذا الرقم القومي مسجَّل بالفعل في قائمة العاملين بالخارج.'),
    ]
