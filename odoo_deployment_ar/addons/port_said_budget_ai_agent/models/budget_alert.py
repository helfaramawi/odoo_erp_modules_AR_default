# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidBudgetAlert(models.Model):
    _name = 'port_said.budget.alert'
    _description = 'تنبيه مراقبة موازنة بورسعيد'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'alert_date desc, risk_level desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='رقم التنبيه', required=True, copy=False, default='جديد', tracking=True)

    alert_date = fields.Datetime(string='تاريخ التنبيه', default=fields.Datetime.now, required=True, tracking=True)
    fiscal_year = fields.Integer(string='السنة المالية', index=True, tracking=True)

    plan_id = fields.Many2one('port_said.budget.plan', string='خطة الموازنة', required=True, ondelete='cascade', index=True)
    line_id = fields.Many2one('port_said.budget.line', string='بند الموازنة', required=True, ondelete='cascade', index=True)
    responsible_id = fields.Many2one('res.users', string='المستخدم المسؤول', tracking=True)

    risk_level = fields.Selection([
        ('medium', 'متوسط'),
        ('high', 'مرتفع'),
        ('critical', 'حرج'),
    ], string='مستوى الخطورة', required=True, tracking=True, index=True)

    amount_approved = fields.Monetary(string='الاعتماد المعتمد', currency_field='currency_id')
    amount_actual = fields.Monetary(string='الصرف الفعلي', currency_field='currency_id')
    amount_committed = fields.Monetary(string='الارتباطات', currency_field='currency_id')
    amount_available = fields.Monetary(string='الرصيد المتاح', currency_field='currency_id')

    actual_execution_rate = fields.Float(string='نسبة التنفيذ الفعلي %', digits=(16, 2))
    commitment_rate = fields.Float(string='نسبة الارتباط %', digits=(16, 2))
    exposure_rate = fields.Float(string='نسبة التعرض %', digits=(16, 2), help='الصرف الفعلي والارتباطات مقسومة على الاعتماد المعتمد')
    daily_burn_rate = fields.Monetary(string='معدل الصرف اليومي', currency_field='currency_id')
    days_to_exhaust = fields.Float(string='الأيام المتوقعة للاستنفاد', digits=(16, 2))
    expected_exhaustion_date = fields.Date(string='تاريخ الاستنفاد المتوقع')

    surplus_line_ids = fields.Many2many(
        'port_said.budget.line',
        'port_said_budget_alert_surplus_rel',
        'alert_id',
        'line_id',
        string='بنود منخفضة الصرف للمراجعة',
    )

    body_html = fields.Html(string='نص التنبيه')
    recommendation = fields.Text(string='الإجراء المقترح')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('sent', 'تم الإرسال'),
        ('reviewed', 'تمت المراجعة'),
        ('closed', 'مغلق'),
    ], string='الحالة', default='draft', tracking=True)

    currency_id = fields.Many2one('res.currency', related='plan_id.currency_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = seq.next_by_code('port_said.budget.alert') or 'جديد'
        return super().create(vals_list)

    def action_mark_reviewed(self):
        for rec in self:
            rec.state = 'reviewed'
            rec.message_post(body=_('تم تعليم التنبيه كمراجع.'))

    def action_close(self):
        for rec in self:
            rec.state = 'closed'
            rec.message_post(body=_('تم إغلاق التنبيه.'))

    def action_send_notification(self):
        for rec in self:
            rec._send_notification()

    def _send_notification(self):
        self.ensure_one()
        responsible = self.responsible_id or self.plan_id.responsible_id or self.plan_id.create_uid
        body = self.body_html or self.recommendation or ''

        if responsible:
            self.activity_schedule(
                'mail.mail_activity_data_warning',
                user_id=responsible.id,
                summary=_('تنبيه موازنة'),
                note=body,
            )

        email_to = responsible.partner_id.email if responsible and responsible.partner_id else False
        if email_to:
            self.env['mail.mail'].sudo().create({
                'subject': _('تنبيه موازنة: %s') % (self.line_id.display_name,),
                'body_html': body,
                'email_to': email_to,
            }).send()

        self.state = 'sent'
        self.message_post(body=_('تم إرسال إشعار تنبيه الموازنة.'))
