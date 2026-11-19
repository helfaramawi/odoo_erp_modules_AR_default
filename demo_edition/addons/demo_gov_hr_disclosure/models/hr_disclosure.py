# -*- coding: utf-8 -*-
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

DISCLOSURE_TYPES = [
    ('first_appointment', 'أول تعيين'),
    ('periodic_renewal', 'تجديد دوري'),
]


class HrDisclosure(models.Model):
    _name = 'demo_gov.hr.disclosure'
    _description = 'إقرار الذمة المالية — C-02'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'declaration_date desc'

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    disclosure_type = fields.Selection(DISCLOSURE_TYPES, string='نوع الإقرار',
                                        default='first_appointment', required=True)
    declaration_date = fields.Date(string='تاريخ تقديم الإقرار')
    # تاريخ استحقاق *هذه* الدورة تحديداً — يُملأ تلقائياً من next_renewal_date
    # لدورة الإقرار السابقة عند فتح دورة تجديد جديدة، ويُستخدم في تنبيه الـ 30
    # يوم؛ يبقى فارغاً في أول تعيين لأن الإشعار وقتها يبدأ يدوياً من قسم
    # الكسب غير المشروع وليس بموعد استحقاق سابق.
    renewal_due_date = fields.Date(string='تاريخ استحقاق هذه الدورة')
    next_renewal_date = fields.Date(string='تاريخ التجديد القادم (بعد هذا الإقرار)',
                                     compute='_compute_renewal_date', store=True)

    # بيانات الإقرار
    real_estate_value = fields.Float(string='قيمة العقارات')
    vehicle_value = fields.Float(string='قيمة المركبات')
    bank_deposits = fields.Float(string='الودائع البنكية')
    other_assets = fields.Float(string='أصول أخرى')
    liabilities = fields.Float(string='الالتزامات والديون')
    net_worth = fields.Float(compute='_compute_net_worth', store=True, string='صافي الثروة')

    reviewed_by = fields.Many2one('res.users', string='مراجِع قسم الكسب غير المشروع')
    review_date = fields.Date(string='تاريخ المراجعة')
    alert_sent = fields.Boolean(string='تم إرسال تنبيه التجديد', default=False, copy=False)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('notified', 'تم إشعار الموظف'),
        ('submitted', 'مُقدَّم من الموظف'),
        ('approved', 'معتمَد ومؤرشف'),
        ('overdue', 'متأخر'),
    ], default='draft', string='الحالة', tracking=True)

    @api.depends('real_estate_value', 'vehicle_value', 'bank_deposits', 'other_assets',
                 'liabilities')
    def _compute_net_worth(self):
        for rec in self:
            rec.net_worth = (rec.real_estate_value + rec.vehicle_value + rec.bank_deposits
                              + rec.other_assets - rec.liabilities)

    @api.depends('declaration_date')
    def _compute_renewal_date(self):
        for rec in self:
            if rec.declaration_date:
                rec.next_renewal_date = rec.declaration_date + relativedelta(years=6, days=2)
            else:
                rec.next_renewal_date = False

    def action_notify_employee(self):
        self.write({'state': 'notified'})

    def action_submit(self):
        for rec in self:
            if not rec.declaration_date:
                rec.declaration_date = fields.Date.today()
        self.write({'state': 'submitted'})

    def action_approve(self):
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('لازم يقدّم الموظف الإقرار أولاً قبل الاعتماد.'))
            rec.write({
                'state': 'approved',
                'review_date': fields.Date.today(),
                'reviewed_by': self.env.user.id,
            })
            # فتح دورة التجديد القادمة تلقائياً (كل 6 سنوات) — يبدأ كسجل
            # مسودة بتاريخ استحقاق معروف مسبقاً (تاريخ تجديد هذا الإقرار)،
            # وتنبيه الـ 30 يوم في المهمة اليومية بيراقب هذا التاريخ.
            self.create({
                'employee_id': rec.employee_id.id,
                'disclosure_type': 'periodic_renewal',
                'renewal_due_date': rec.next_renewal_date,
            })

    def action_reject_correction(self):
        self.write({'state': 'draft'})

    def _cron_check_disclosure_expiry(self):
        today = fields.Date.today()
        alert_window = today + timedelta(days=30)

        to_alert = self.search([
            ('state', 'not in', ['approved']),
            ('alert_sent', '=', False),
            ('renewal_due_date', '!=', False),
            ('renewal_due_date', '<=', alert_window),
            ('renewal_due_date', '>=', today),
        ])
        for rec in to_alert:
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('اقتراب موعد تجديد إقرار الذمة المالية للموظف %s') % rec.employee_id.name,
                note=_('تاريخ الاستحقاق: %s') % rec.renewal_due_date,
                user_id=rec.create_uid.id,
            )
            rec.alert_sent = True
            if rec.state == 'draft':
                rec.state = 'notified'

        overdue = self.search([
            ('state', 'not in', ['approved', 'overdue']),
            ('renewal_due_date', '!=', False),
            ('renewal_due_date', '<', today),
        ])
        overdue.write({'state': 'overdue'})
