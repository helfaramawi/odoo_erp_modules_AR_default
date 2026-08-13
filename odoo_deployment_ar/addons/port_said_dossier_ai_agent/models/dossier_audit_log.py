# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidDossierAuditLog(models.Model):
    _name = 'port_said.dossier.audit.log'
    _description = 'سجل فحص الإضبارة قبل الصرف'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'check_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='رقم الفحص', required=True, copy=False, default='جديد', tracking=True)

    check_date = fields.Datetime(string='تاريخ الفحص', default=fields.Datetime.now, required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='المستخدم', default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda self: self.env.company)

    daftar55_id = fields.Many2one('port_said.daftar55', string='دفتر 55', index=True, ondelete='set null')
    dossier_id = fields.Many2one('port_said.dossier', string='الإضبارة', index=True, ondelete='set null')

    vendor_id = fields.Many2one('res.partner', string='المورد / المستفيد', index=True)
    amount_gross = fields.Float(string='إجمالي المبلغ')
    reference = fields.Char(string='مرجع أمر التوريد / المستند')

    is_complete = fields.Boolean(string='الإضبارة مكتملة')
    missing_attachments = fields.Text(string='المرفقات الناقصة')

    result = fields.Selection([
        ('passed', 'تم السماح'),
        ('blocked_missing', 'تم المنع لنقص المستندات'),
        ('blocked_ai', 'تم المنع لعدم تطابق محتوى المرفقات'),
        ('warning', 'تحذير فقط'),
        ('skipped', 'لم يتم الفحص'),
    ], string='نتيجة الفحص', default='skipped', required=True, tracking=True, index=True)

    ai_check_enabled = fields.Boolean(string='تم تفعيل الفحص الذكي')
    ai_check_status = fields.Selection([
        ('not_configured', 'غير مفعّل'),
        ('passed', 'مطابق'),
        ('failed', 'غير مطابق'),
        ('warning', 'تحذير'),
        ('not_readable', 'تعذر قراءة المرفق'),
    ], string='نتيجة الفحص الذكي', default='not_configured')

    discrepancy_note = fields.Text(string='ملاحظات عدم المطابقة')
    technical_details = fields.Text(string='تفاصيل تقنية')
    attachment_ids = fields.Many2many('ir.attachment', string='المرفقات المفحوصة')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = seq.next_by_code('port_said.dossier.audit.log') or 'جديد'
        return super().create(vals_list)

    def action_open_daftar55(self):
        self.ensure_one()
        if not self.daftar55_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('دفتر 55'),
            'res_model': 'port_said.daftar55',
            'res_id': self.daftar55_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_dossier(self):
        self.ensure_one()
        if not self.dossier_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('الإضبارة'),
            'res_model': 'port_said.dossier',
            'res_id': self.dossier_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
