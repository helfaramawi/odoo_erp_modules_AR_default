# -*- coding: utf-8 -*-
from odoo import models, fields

GOV_TERMINATION_TYPES = [
    ('retirement_60', 'بلوغ سن المعاش (60 سنة)'),
    ('resignation', 'استقالة'),
    ('death', 'وفاة'),
    ('dismissal', 'فصل'),
    ('abandonment', 'انقطاع عن العمل'),
]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    gov_termination_type = fields.Selection(GOV_TERMINATION_TYPES,
                                             string='نوع إنهاء الخدمة', tracking=True)
    termination_date = fields.Date(string='تاريخ إنهاء الخدمة', tracking=True)
    termination_decision_number = fields.Char(string='رقم قرار إنهاء الخدمة')
