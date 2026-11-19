# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

TRANSFER_TYPES = [
    ('secondment', 'ندب'),
    ('loan', 'إعارة'),
    ('internal_transfer', 'نقل داخلي'),
    ('external_transfer', 'نقل خارجي بالدرجة'),
    ('settlement', 'إعادة تعيين (تسوية)'),
]

ENTITY_CHOICES = [
    ('diwan_general', 'الديوان العام'),
    ('districts', 'الأحياء'),
    ('port_fouad', 'المدينة الثانية'),
    ('external', 'جهة خارجية'),
]


class HrTransfer(models.Model):
    _name = 'demo_gov.hr.transfer'
    _description = 'حركة نقل / ندب / إعارة (FDD-HR-06)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='رقم الحركة', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True, tracking=True)
    transfer_type = fields.Selection(TRANSFER_TYPES, string='نوع الحركة', required=True, tracking=True)
    from_entity = fields.Selection(ENTITY_CHOICES, string='من جهة')
    to_entity_name = fields.Char(string='إلى جهة (اسم الجهة)')
    decision_number = fields.Char(string='رقم القرار')
    decision_date = fields.Date(string='تاريخ القرار')
    start_date = fields.Date(string='تاريخ البداية', required=True)
    end_date = fields.Date(string='تاريخ الانتهاء')
    renewal_count = fields.Integer(string='عدد مرات التجديد', default=0, readonly=True)
    alert_sent = fields.Boolean(string='تم إرسال تنبيه الانتهاء', default=False, copy=False)

    is_settlement = fields.Boolean(compute='_compute_is_settlement', store=True,
                                    string='تسوية؟')
    central_agency_approved = fields.Boolean(string='موافقة الجهاز المركزي')
    finance_ministry_approved = fields.Boolean(string='موافقة وزارة المالية')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('approved', 'معتمَدة'),
        ('active', 'سارية'),
        ('ended', 'منتهية'),
        ('cancelled', 'ملغاة'),
    ], default='draft', string='الحالة', tracking=True)

    @api.depends('transfer_type')
    def _compute_is_settlement(self):
        for rec in self:
            rec.is_settlement = rec.transfer_type == 'settlement'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.transfer') or '/'
        return super().create(vals_list)

    def action_approve(self):
        for rec in self:
            if rec.is_settlement and not (rec.central_agency_approved and rec.finance_ministry_approved):
                raise UserError(_('التسوية تحتاج موافقة الجهاز المركزي ووزارة المالية أولاً.'))
        self.write({'state': 'approved'})

    def action_activate(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('الحركة لازم تكون معتمَدة أولاً.'))
        self.write({'state': 'active'})

    def action_end(self):
        self.write({'state': 'ended'})

    def action_renew(self):
        for rec in self:
            if rec.state != 'active':
                raise UserError(_('لا يمكن تجديد حركة غير سارية.'))
            rec.renewal_count += 1
            rec.alert_sent = False

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def _cron_alert_ending_transfers(self):
        today = fields.Date.today()
        limit = today + timedelta(days=30)
        transfers = self.search([
            ('state', '=', 'active'),
            ('alert_sent', '=', False),
            ('end_date', '!=', False),
            ('end_date', '<=', limit),
            ('end_date', '>=', today),
        ])
        type_labels = dict(TRANSFER_TYPES)
        for rec in transfers:
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('اقتراب انتهاء %(type)s للموظف %(employee)s') % {
                    'type': type_labels.get(rec.transfer_type, ''),
                    'employee': rec.employee_id.name,
                },
                note=_('تاريخ الانتهاء: %s') % rec.end_date,
                user_id=rec.create_uid.id,
            )
            rec.alert_sent = True
