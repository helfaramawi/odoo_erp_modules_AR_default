# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidExecutiveBriefing(models.Model):
    _name = 'port_said.executive.briefing'
    _description = 'الملخص التنفيذي اليومي للقيادة العليا'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'briefing_date desc, risk_score desc'

    name = fields.Char(string='رقم الملخص', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    briefing_date = fields.Date(string='تاريخ الملخص', required=True, default=fields.Date.today, index=True, tracking=True)

    risk_score = fields.Float(string='درجة الخطورة العامة من 100', digits=(16, 2), tracking=True)
    risk_level = fields.Selection([
        ('low', 'مستقر'),
        ('medium', 'متوسط المخاطر'),
        ('high', 'مرتفع المخاطر'),
        ('critical', 'حرج'),
    ], string='مستوى الخطورة العام', tracking=True)

    summary_text = fields.Text(string='الملخص النصي')
    summary_html = fields.Html(string='الملخص التنفيذي العربي')
    action_items = fields.Text(string='الإجراءات المطلوبة')
    management_message = fields.Html(string='رسالة الإدارة الجاهزة للإرسال')

    budget_risk_count = fields.Integer(string='مخاطر الموازنة')
    late_cheque_count = fields.Integer(string='شيكات متأخرة')
    eta_failed_count = fields.Integer(string='فواتير ETA مرفوضة')
    penalty_count = fields.Integer(string='جزاءات جديدة')
    pending_procurement_count = fields.Integer(string='مشتريات تحتاج اعتماد')
    payment_delay_count = fields.Integer(string='تأخيرات إدارية')
    dead_stock_count = fields.Integer(string='مخزون راكد')
    total_exception_count = fields.Integer(string='إجمالي الاستثناءات')

    line_ids = fields.One2many('port_said.executive.briefing.line', 'briefing_id', string='بنود الملخص')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('generated', 'تم التوليد'),
        ('sent', 'تم الإرسال'),
        ('archived', 'مؤرشف'),
    ], string='الحالة', default='draft', tracking=True)

    sent_date = fields.Datetime(string='تاريخ الإرسال', readonly=True)
    sent_to = fields.Text(string='تم الإرسال إلى', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('port_said.executive.briefing') or _('New')
        return super().create(vals_list)

    def action_generate_now(self):
        briefing = self.env['port_said.executive.briefing.engine'].sudo().generate_daily_briefing()
        return {
            'type': 'ir.actions.act_window',
            'name': 'الملخص التنفيذي اليومي',
            'res_model': 'port_said.executive.briefing',
            'res_id': briefing.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_send_internal_mail(self):
        for rec in self:
            rec._send_internal_mail()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('تم الإرسال'), 'message': _('تم إرسال الملخص التنفيذي للمديرين.'), 'type': 'success', 'sticky': False}
        }

    def _send_internal_mail(self):
        self.ensure_one()
        users = self._management_users()
        emails = [u.email for u in users if u.email]

        subject = 'الملخص التنفيذي اليومي - %s - مستوى الخطورة: %s' % (
            self.briefing_date,
            dict(self._fields['risk_level'].selection).get(self.risk_level, self.risk_level or '')
        )

        body = self.management_message or self.summary_html or self.summary_text or ''

        # Internal chatter for users
        self.message_post(
            body=body,
            subject=subject,
            partner_ids=users.mapped('partner_id').ids,
            message_type='comment',
            subtype_xmlid='mail.mt_comment'
        )

        # Email if addresses exist
        if emails:
            self.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': body,
                'email_to': ','.join(emails),
                'auto_delete': False,
            }).send()

        self.write({
            'state': 'sent',
            'sent_date': fields.Datetime.now(),
            'sent_to': '\\n'.join(['%s <%s>' % (u.name, u.email or '') for u in users]),
        })

    def _management_users(self):
        users = self.env['res.users'].sudo()
        groups_xmlids = [
            'base.group_system',
            'purchase.group_purchase_manager',
            'account.group_account_manager',
        ]
        for xmlid in groups_xmlids:
            try:
                group = self.env.ref(xmlid, raise_if_not_found=False)
                if group:
                    users |= group.users
            except Exception:
                pass
        return users.filtered(lambda u: u.active and not u.share)

    def action_archive(self):
        self.write({'state': 'archived'})


class PortSaidExecutiveBriefingLine(models.Model):
    _name = 'port_said.executive.briefing.line'
    _description = 'بند في الملخص التنفيذي اليومي'
    _order = 'severity desc, amount desc, id desc'

    briefing_id = fields.Many2one('port_said.executive.briefing', string='الملخص التنفيذي', required=True, ondelete='cascade', index=True)

    section = fields.Selection([
        ('budget_risks', 'مخاطر الموازنة'),
        ('late_cheques', 'شيكات متأخرة'),
        ('eta_failed', 'فواتير ETA مرفوضة'),
        ('new_penalties', 'جزاءات جديدة'),
        ('pending_procurement', 'مشتريات تحتاج اعتماد'),
        ('payment_delays', 'تأخيرات إدارية'),
        ('dead_stock', 'مخزون راكد'),
        ('other', 'أخرى'),
    ], string='القسم', required=True, index=True)

    title = fields.Char(string='العنوان', required=True)
    description = fields.Text(string='الوصف')
    recommended_action = fields.Text(string='الإجراء المطلوب')

    severity = fields.Selection([
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'مرتفعة'),
        ('critical', 'حرجة'),
    ], string='الخطورة', default='medium', index=True)

    amount = fields.Monetary(string='القيمة', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='العملة', default=lambda self: self.env.company.currency_id.id)

    source_model = fields.Char(string='النموذج المصدر')
    source_res_id = fields.Integer(string='رقم السجل المصدر')
    source_display_name = fields.Char(string='السجل المصدر')

    metric_1 = fields.Char(string='مؤشر 1')
    metric_2 = fields.Char(string='مؤشر 2')
    record_date = fields.Date(string='تاريخ السجل')

    def action_open_source(self):
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': self.source_display_name or 'السجل المصدر',
            'res_model': self.source_model,
            'res_id': self.source_res_id,
            'view_mode': 'form',
            'target': 'current',
        }
