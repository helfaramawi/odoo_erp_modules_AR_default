# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidDuplicateClaimAlert(models.Model):
    _name = 'port_said.duplicate.claim.alert'
    _description = 'تنبيه تكرار مستند أو مطالبة صرف'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'similarity_score desc, create_date desc'

    name = fields.Char(string='رقم التنبيه', required=True, copy=False, readonly=True, default=lambda self: _('New'))

    alert_type = fields.Selection([
        ('same_file', 'نفس الملف مرفوع أكثر من مرة'),
        ('same_invoice', 'نفس رقم الفاتورة لنفس المورد'),
        ('same_amount_date', 'نفس المبلغ ونفس التاريخ'),
        ('similar_filename', 'تشابه اسم الملف والمورد والمبلغ'),
        ('duplicate_daftar55_claim', 'مطالبة صرف مكررة في دفتر 55'),
        ('duplicate_account_bill', 'فاتورة مورد مكررة محاسبيًا'),
    ], string='نوع التكرار', required=True, tracking=True)

    similarity_score = fields.Float(string='نسبة التشابه %', digits=(16, 2), tracking=True)
    risk_level = fields.Selection([
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'مرتفعة'),
        ('critical', 'حرجة'),
    ], string='مستوى الخطورة', tracking=True)

    source_model = fields.Char(string='النموذج المصدر', readonly=True, index=True)
    source_res_id = fields.Integer(string='رقم السجل المصدر', readonly=True, index=True)
    source_display_name = fields.Char(string='السجل المصدر', readonly=True)

    duplicate_model = fields.Char(string='نموذج السجل المكرر', readonly=True)
    duplicate_res_id = fields.Integer(string='رقم السجل المكرر', readonly=True)
    duplicate_display_name = fields.Char(string='السجل المكرر', readonly=True)

    original_attachment_id = fields.Many2one('ir.attachment', string='المستند الأصلي')
    duplicate_attachment_id = fields.Many2one('ir.attachment', string='المستند المكرر')
    checksum = fields.Char(string='Checksum / بصمة الملف', index=True)

    partner_id = fields.Many2one('res.partner', string='المورد / المستفيد', index=True, tracking=True)
    invoice_number = fields.Char(string='رقم الفاتورة / المرجع', tracking=True)
    claim_date = fields.Date(string='تاريخ المطالبة')
    amount = fields.Monetary(string='قيمة المطالبة', currency_field='currency_id', tracking=True)
    difference_amount = fields.Monetary(string='فرق القيمة', currency_field='currency_id')

    reason = fields.Text(string='سبب التنبيه', readonly=True)
    recommendation = fields.Text(string='التوصية', readonly=True)

    currency_id = fields.Many2one('res.currency', string='العملة', default=lambda self: self.env.company.currency_id.id)

    state = fields.Selection([
        ('new', 'جديد'),
        ('under_review', 'تحت المراجعة'),
        ('confirmed_duplicate', 'تكرار مؤكد'),
        ('false_positive', 'ليس تكرارًا'),
        ('blocked', 'تم إيقاف الصرف'),
        ('resolved', 'تمت المعالجة'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='new', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_notes = fields.Text(string='ملاحظات المراجعة')

    _sql_constraints = [
        (
            'unique_duplicate_claim_alert',
            'unique(alert_type, source_model, source_res_id, duplicate_model, duplicate_res_id, original_attachment_id, duplicate_attachment_id)',
            'يوجد تنبيه سابق لنفس التكرار.'
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('port_said.duplicate.claim.alert') or _('New')
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

    def action_open_duplicate(self):
        self.ensure_one()
        if not self.duplicate_model or not self.duplicate_res_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'السجل المكرر',
            'res_model': self.duplicate_model,
            'res_id': self.duplicate_res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_review(self):
        self.write({'state': 'under_review', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_confirm_duplicate(self):
        self.write({'state': 'confirmed_duplicate', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_false_positive(self):
        self.write({'state': 'false_positive', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_block_payment(self):
        self.write({'state': 'blocked', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_resolve(self):
        self.write({'state': 'resolved', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})
