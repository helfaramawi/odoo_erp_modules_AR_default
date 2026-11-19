# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidProcurementLegalCompliance(models.Model):
    _name = 'port_said.procurement.legal.compliance'
    _description = 'مراجعة الالتزام القانوني لمستندات المشتريات'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'compliance_score asc, create_date desc'

    name = fields.Char(string='رقم المراجعة', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    source_model = fields.Char(string='النموذج المصدر', required=True, index=True, tracking=True)
    source_res_id = fields.Integer(string='رقم السجل المصدر', required=True, index=True, tracking=True)
    source_display_name = fields.Char(string='السجل المصدر', readonly=True)

    procurement_method = fields.Selection([
        ('tender', 'مناقصة'),
        ('practice', 'ممارسة'),
        ('direct_order', 'أمر مباشر'),
        ('simple_supply', 'توريد بسيط'),
        ('unknown', 'غير محدد'),
    ], string='نوع عملية الشراء', default='unknown', tracking=True)

    stage = fields.Selection([
        ('before_envelopes', 'قبل فتح المظاريف'),
        ('before_technical', 'قبل البت الفني'),
        ('before_award', 'قبل الترسية'),
        ('before_po', 'قبل إصدار أمر الشراء'),
        ('general', 'مراجعة عامة'),
    ], string='مرحلة المراجعة', default='general', tracking=True)

    compliance_score = fields.Float(string='نسبة الالتزام القانوني %', digits=(16, 2), tracking=True)
    legal_status = fields.Selection([
        ('complete', 'مكتمل'),
        ('incomplete', 'ناقص'),
        ('needs_review', 'يحتاج مراجعة'),
        ('blocked', 'نقص جوهري - إيقاف'),
    ], string='الحالة القانونية', tracking=True)

    missing_docs = fields.Text(string='المستندات الناقصة', readonly=True)
    existing_docs = fields.Text(string='المستندات الموجودة', readonly=True)
    unknown_docs = fields.Text(string='مرفقات غير مصنفة', readonly=True)
    critical_missing_docs = fields.Text(string='نواقص جوهرية', readonly=True)

    attachment_ids = fields.Many2many('ir.attachment', 'legal_compliance_attachment_rel', 'compliance_id', 'attachment_id', string='المرفقات التي تم فحصها')

    recommendation = fields.Text(string='التوصية القانونية', readonly=True)
    official_note = fields.Html(string='مذكرة مراجعة قانونية', readonly=True)

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('to_review', 'للمراجعة'),
        ('approved', 'معتمد قانونيًا'),
        ('rejected', 'مرفوض'),
        ('blocked', 'موقوف'),
        ('cancelled', 'ملغي'),
    ], string='حالة المراجعة', default='draft', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_notes = fields.Text(string='ملاحظات المراجعة')

    _sql_constraints = [
        ('unique_procurement_legal_compliance', 'unique(source_model, source_res_id, stage)', 'يوجد مراجعة قانونية سابقة لنفس السجل ونفس المرحلة.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('port_said.procurement.legal.compliance') or _('New')
        return super().create(vals_list)

    def action_open_source(self):
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            return False
        return {'type': 'ir.actions.act_window', 'name': 'السجل المصدر', 'res_model': self.source_model, 'res_id': self.source_res_id, 'view_mode': 'form', 'target': 'current'}

    def action_recheck(self):
        self.ensure_one()
        rec = self.env[self.source_model].sudo().browse(self.source_res_id)
        if rec.exists():
            self.env['port_said.procurement.legal.engine'].sudo().check_procurement_record(rec, self.stage)
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('تم الفحص'), 'message': _('تم إعادة فحص الالتزام القانوني.'), 'type': 'success', 'sticky': False}}

    def action_to_review(self):
        self.write({'state': 'to_review'})

    def action_approve(self):
        self.write({'state': 'approved', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_reject(self):
        self.write({'state': 'rejected', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_block(self):
        self.write({'state': 'blocked', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})
