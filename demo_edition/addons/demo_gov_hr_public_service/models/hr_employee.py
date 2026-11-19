# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # نوع تعيين إضافي — خدمة عامة: أداء الخريجات للخدمة العامة لمدة عام
    # بدون راتب، خارج نطاق الرواتب تماماً (C-04).
    gov_employment_type = fields.Selection(
        selection_add=[('public_service', 'خدمة عامة (خريجات - عام واحد بدون راتب)')],
        ondelete={'public_service': 'set default'},
    )

    public_service_start_date = fields.Date(string='تاريخ بدء الخدمة العامة')
    public_service_end_date = fields.Date(string='تاريخ انتهاء الخدمة العامة',
                                           compute='_compute_public_service_end_date', store=True)
    public_service_ended = fields.Boolean(string='انتهت الخدمة العامة', default=False, copy=False)

    @api.depends('public_service_start_date')
    def _compute_public_service_end_date(self):
        for rec in self:
            if rec.public_service_start_date:
                rec.public_service_end_date = rec.public_service_start_date + relativedelta(years=1)
            else:
                rec.public_service_end_date = False

    def _cron_check_public_service_expiry(self):
        today = fields.Date.today()
        expired = self.search([
            ('gov_employment_type', '=', 'public_service'),
            ('public_service_ended', '=', False),
            ('public_service_end_date', '!=', False),
            ('public_service_end_date', '<=', today),
        ])
        for rec in expired:
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('انتهاء مدة الخدمة العامة للموظفة %s') % rec.name,
                note=_('تاريخ الانتهاء: %s — لازم مراجعة الإدارة لإنهاء أو تجديد التكليف.')
                     % rec.public_service_end_date,
                user_id=rec.create_uid.id,
            )
        expired.write({'public_service_ended': True})
