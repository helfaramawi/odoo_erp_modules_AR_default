# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _


class PortSaidVendorDataQuality(models.Model):
    _name = 'port_said.vendor.data.quality'
    _description = 'جودة بيانات المورد'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'score asc, write_date desc'

    name = fields.Char(string='المرجع', compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', string='المورد', required=True, index=True, ondelete='cascade', tracking=True)

    score = fields.Integer(string='درجة الجودة', default=0, tracking=True)
    status = fields.Selection([
        ('valid', 'صالح للتعامل'),
        ('needs_completion', 'يحتاج استكمال'),
        ('blocked', 'موقوف رقابيًا'),
    ], string='حالة المورد', default='needs_completion', tracking=True)

    issue_count = fields.Integer(string='عدد النواقص', compute='_compute_issue_count', store=True)
    issue_summary = fields.Text(string='قائمة النواقص / الملاحظات', tracking=True)
    recommendation = fields.Text(string='التوصية')

    missing_vat = fields.Boolean(string='رقم ضريبي مفقود')
    invalid_vat = fields.Boolean(string='رقم ضريبي غير صحيح')
    missing_bank = fields.Boolean(string='لا يوجد حساب بنكي')
    missing_address = fields.Boolean(string='العنوان غير مكتمل')
    missing_contact = fields.Boolean(string='لا يوجد مسؤول اتصال')
    duplicate_vat = fields.Boolean(string='رقم ضريبي مكرر')
    open_penalties = fields.Boolean(string='جزاءات مفتوحة')
    eta_not_ready = fields.Boolean(string='غير جاهز للفاتورة الإلكترونية')

    duplicate_partner_ids = fields.Many2many(
        'res.partner',
        'vendor_quality_duplicate_partner_rel',
        'quality_id',
        'partner_id',
        string='موردون بنفس الرقم الضريبي'
    )

    open_penalty_count = fields.Integer(string='عدد الجزاءات المفتوحة')
    last_check_date = fields.Datetime(string='آخر فحص', readonly=True)
    checked_by = fields.Many2one('res.users', string='آخر فحص بواسطة', readonly=True)

    _sql_constraints = [
        ('unique_partner_quality', 'unique(partner_id)', 'يوجد سجل جودة بيانات سابق لهذا المورد.')
    ]

    @api.depends('partner_id')
    def _compute_name(self):
        for rec in self:
            rec.name = 'جودة بيانات المورد: %s' % (rec.partner_id.display_name or '')

    @api.depends(
        'missing_vat', 'invalid_vat', 'missing_bank', 'missing_address',
        'missing_contact', 'duplicate_vat', 'open_penalties', 'eta_not_ready'
    )
    def _compute_issue_count(self):
        fields_to_count = [
            'missing_vat', 'invalid_vat', 'missing_bank', 'missing_address',
            'missing_contact', 'duplicate_vat', 'open_penalties', 'eta_not_ready'
        ]
        for rec in self:
            rec.issue_count = sum(1 for fname in fields_to_count if rec[fname])

    def action_open_vendor(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'المورد',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_recheck(self):
        for rec in self:
            rec.partner_id.sudo().action_recalculate_vendor_quality()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم الفحص'),
                'message': _('تم إعادة حساب جودة بيانات المورد.'),
                'type': 'success',
                'sticky': False,
            }
        }


class PortSaidVendorDataQualityEngine(models.TransientModel):
    _name = 'port_said.vendor.data.quality.engine'
    _description = 'محرك فحص جودة بيانات الموردين'

    @api.model
    def _get_min_score(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_vendor_quality.min_purchase_score',
            '60'
        )
        try:
            return int(float(value))
        except Exception:
            return 60

    @api.model
    def _get_block_purchase(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'port_said_vendor_quality.block_purchase_confirmation',
            '1'
        )
        return str(value).lower() in ('1', 'true', 'yes')

    def action_run_full_scan(self):
        partners = self.env['res.partner'].sudo().search([
            ('supplier_rank', '>', 0),
            ('active', '=', True),
        ])
        count = 0
        for partner in partners:
            partner.action_recalculate_vendor_quality()
            count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تشغيل فحص جودة الموردين'),
                'message': _('تم فحص %s مورد نشط.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_weekly_vendor_quality_scan(self):
        partners = self.env['res.partner'].sudo().search([
            ('supplier_rank', '>', 0),
            ('active', '=', True),
        ])
        for partner in partners:
            partner.action_recalculate_vendor_quality()
        return True
