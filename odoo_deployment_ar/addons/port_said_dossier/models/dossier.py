from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 9 required attachment categories per Form-50 Procedures document
REQUIRED_ATTACHMENTS = [
    ('national_id',      'صورة بطاقة الرقم القومي'),
    ('bank_letter',      'خطاب معتمد من البنك'),
    ('commitment_form',  'طلب الارتباط'),
    ('purchase_memo',    'مذكرة شراء'),
    ('supply_order',     'أمر التوريد'),
    ('invoices',         'الفواتير'),
    ('store_declaration','إقرار أمين المخازن'),
    ('committee_report', 'محضر لجنة الفحص (نموذج 12 مخازن)'),
    ('addition_permit',  'إذن إضافة (نموذج 1)'),
    ('tender_docs',      'مستندات إجراءات الشراء (كراسة الشروط)'),
]


class DossierAttachment(models.Model):
    _name = 'port_said.dossier.attachment'
    _description = 'مرفق الاضبارة'

    dossier_id      = fields.Many2one('port_said.dossier', string='الاضبارة', ondelete='cascade')
    attachment_type = fields.Selection(REQUIRED_ATTACHMENTS, string='نوع المرفق', required=True)
    attachment_id   = fields.Many2one('ir.attachment', string='الملف', required=True)
    notes           = fields.Char(string='ملاحظة')


class Dossier(models.Model):
    """
    الاضبارة - Form 101 ساير
    Dossier number per budget line: [YEAR]/[BUDGET_LINE]/[SEQ]
    ENFORCES 9 required attachments for Form 50 disbursements.
    """
    _name = 'port_said.dossier'
    _description = 'الاضبارة - استمارة 101 ساير'
    _order = 'dossier_number desc'
    _rec_name = 'dossier_number'

    dossier_number  = fields.Char(string='رقم الاضبارة', readonly=True, copy=False, index=True)
    budget_line     = fields.Char(string='البند (باب/بند/نوع)', required=True, index=True)
    fiscal_year     = fields.Integer(string='السنة المالية', required=True, default=lambda s: fields.Date.today().year)
    daftar55_id     = fields.Many2one('port_said.daftar55', string='مرجع دفتر 55')
    form50_ref      = fields.Char(string='رقم استمارة 50', related='daftar55_id.form50_ref', store=True)
    vendor_id       = fields.Many2one('res.partner', string='صاحب الحق', related='daftar55_id.vendor_id', store=True)
    amount          = fields.Monetary(string='المبلغ', related='daftar55_id.amount_gross', store=True, currency_field='currency_id')
    currency_id     = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)

    attachment_ids  = fields.One2many('port_said.dossier.attachment', 'dossier_id', string='المرفقات')
    attachment_count = fields.Integer(string='عدد المرفقات', compute='_compute_attachment_count', store=True)
    missing_attachments = fields.Char(string='المرفقات الناقصة', compute='_compute_missing', store=True)
    is_complete     = fields.Boolean(string='مكتملة (9 مرفقات)', compute='_compute_missing', store=True)

    physical_shelf  = fields.Char(string='موقع الأرشيف الورقي (رف/صندوق)')
    notes           = fields.Text(string='ملاحظات')
    state           = fields.Selection([
        ('open',   'مفتوحة'),
        ('closed', 'مغلقة'),
    ], default='open', string='الحالة')
    company_id      = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    @api.depends('attachment_ids.attachment_type')
    def _compute_missing(self):
        required = {k for k, _ in REQUIRED_ATTACHMENTS}
        for rec in self:
            present = set(rec.attachment_ids.mapped('attachment_type'))
            missing = required - present
            rec.missing_attachments = ', '.join(
                dict(REQUIRED_ATTACHMENTS).get(m, m) for m in missing
            ) if missing else ''
            rec.is_complete = len(rec.attachment_ids) >= 9 and len(missing) == 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('dossier_number'):
                bl = (vals.get('budget_line') or 'GEN').replace('/', '-')
                yr = vals.get('fiscal_year', fields.Date.today().year)
                seq_code = f'port_said.dossier.{bl}.{yr}'
                # Use global sequence and build number manually
                seq = self.env['ir.sequence'].next_by_code('port_said.dossier') or '0001'
                vals['dossier_number'] = f"{yr}/{bl}/{seq}"
        return super().create(vals_list)

    def action_validate_attachments(self):
        """Validate 9 required attachments — called before payment posting."""
        for rec in self:
            if not rec.is_complete:
                raise UserError(_(
                    'لا يمكن إتمام عملية الصرف.\n'
                    'الاضبارة ناقصة المرفقات التالية:\n%(missing)s\n\n'
                    'يجب إرفاق جميع المستندات التسعة المطلوبة وفقاً لإجراءات استمارة 50 ع.ح.',
                    missing=rec.missing_attachments,
                ))
        return True

    def action_print_dossier(self):
        return self.env.ref('port_said_dossier.action_report_dossier').report_action(self)
