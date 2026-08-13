# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidPaymentCycleDelay(models.Model):
    _name = 'port_said.payment.cycle.delay'
    _description = 'تنبيه تأخير في دورة الصرف'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'delay_days desc, create_date desc'

    name = fields.Char(string='رقم التنبيه', required=True, copy=False, readonly=True, default=lambda self: _('New'))

    source_model = fields.Char(string='النموذج المصدر', readonly=True, index=True)
    source_res_id = fields.Integer(string='رقم السجل المصدر', readonly=True, index=True)
    source_display_name = fields.Char(string='اسم السجل المصدر', readonly=True)

    cycle_reference = fields.Char(string='مرجع دورة الصرف', index=True, tracking=True)
    document_number = fields.Char(string='رقم المستند', tracking=True)
    beneficiary_name = fields.Char(string='المستفيد')
    department_name = fields.Char(string='الإدارة / الجهة')
    amount = fields.Monetary(string='القيمة', currency_field='currency_id')

    stage = fields.Selection([
        ('dossier_creation', 'إنشاء الإضبارة'),
        ('dossier_completion', 'اكتمال المستندات'),
        ('daftar55_approval', 'اعتماد دفتر 55'),
        ('payment_order', 'إنشاء أمر الدفع'),
        ('cheque_issue', 'إصدار الشيك'),
        ('cheque_delivery', 'تسليم الشيك / إغلاق الدفع'),
        ('accounting_posting', 'الترحيل المحاسبي'),
        ('general', 'مرحلة عامة'),
    ], string='مرحلة التأخير', required=True, tracking=True)

    current_state = fields.Char(string='الحالة الحالية')
    start_date = fields.Datetime(string='بداية المرحلة', tracking=True)
    due_date = fields.Datetime(string='تاريخ الاستحقاق حسب SLA')
    delay_days = fields.Integer(string='أيام التأخير', tracking=True)
    sla_days = fields.Integer(string='حد SLA بالأيام')

    risk_level = fields.Selection([
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'مرتفعة'),
        ('critical', 'حرجة'),
    ], string='مستوى الخطورة', tracking=True)

    delay_reason = fields.Text(string='سبب التنبيه', readonly=True)
    recommendation = fields.Text(string='التوصية', readonly=True)

    currency_id = fields.Many2one('res.currency', string='العملة', default=lambda self: self.env.company.currency_id.id)

    state = fields.Selection([
        ('new', 'جديد'),
        ('under_review', 'تحت المراجعة'),
        ('action_required', 'يتطلب إجراء'),
        ('resolved', 'تمت المعالجة'),
        ('justified', 'مبرر'),
        ('cancelled', 'ملغي'),
    ], string='حالة التنبيه', default='new', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_notes = fields.Text(string='ملاحظات المراجعة')

    _sql_constraints = [
        ('unique_payment_cycle_delay', 'unique(source_model, source_res_id, stage)', 'يوجد تنبيه سابق لنفس السجل ونفس المرحلة.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('port_said.payment.cycle.delay') or _('New')
        return super().create(vals_list)

    def action_open_source(self):
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'السجل المصدر',
            'res_model': self.source_model,
            'res_id': self.source_res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_review(self):
        self.write({'state': 'under_review', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_required(self):
        self.write({'state': 'action_required', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_resolve(self):
        self.write({'state': 'resolved', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_justify(self):
        self.write({'state': 'justified', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})
