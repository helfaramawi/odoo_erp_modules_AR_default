from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ProcurementCommittee(models.Model):
    """لجنة المناقصة — Procurement Committee"""
    _name = 'procurement.committee'
    _description = 'لجنة - Procurement Committee'
    _inherit = ['mail.thread']
    _order = 'formation_date desc'

    name = fields.Char(string='اسم اللجنة', required=True, tracking=True)
    ref = fields.Char(
        string='رقم قرار التشكيل', required=True, copy=False,
        default='/', tracking=True,
    )
    committee_type = fields.Selection([
        ('technical',  'لجنة البت الفني - Technical Adjudication'),
        ('financial',  'لجنة البت المالي - Financial Adjudication'),
        ('opening',    'لجنة فض المظاريف - Envelope Opening'),
        ('award',      'لجنة الترسية - Award'),
        ('inspection', 'لجنة الفحص - Inspection'),
        ('mixed',      'لجنة مختلطة - Mixed'),
    ], string='نوع اللجنة', required=True, default='technical', tracking=True)

    procurement_type = fields.Selection([
        ('tender_public',   'مناقصة عامة'),
        ('tender_local',    'مناقصة محلية'),
        ('tender_limited',  'مناقصة محدودة'),
        ('direct_supply',   'أمر مباشر توريدات'),
        ('direct_private',  'أمر مباشر شركات خاصة'),
        ('negotiation',     'ممارسة'),
        ('auction',         'مزايدة'),
        ('contracting',     'مقاولات'),
    ], string='وسيلة الطرح', required=True, tracking=True)

    formation_date = fields.Date(
        string='تاريخ قرار التشكيل', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    authority_ref = fields.Char(
        string='السلطة المختصة المصدرة للقرار', tracking=True,
    )
    member_ids = fields.One2many(
        'committee.member', 'committee_id', string='أعضاء اللجنة',
    )
    member_count = fields.Integer(compute='_compute_member_count', string='عدد الأعضاء')
    chairman_id = fields.Many2one(
        'hr.employee', string='رئيس اللجنة',
        compute='_compute_chairman', store=True,
    )
    notes = fields.Text(string='ملاحظات')
    state = fields.Selection([
        ('draft',    'مسودة'),
        ('active',   'نشطة'),
        ('closed',   'منتهية'),
    ], default='draft', tracking=True)

    _sql_constraints = [
        ('ref_uniq', 'unique(ref)', 'رقم قرار التشكيل يجب أن يكون فريداً'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', '/') == '/':
                vals['ref'] = self.env['ir.sequence'].next_by_code('procurement.committee') or '/'
        return super().create(vals_list)

    @api.depends('member_ids')
    def _compute_member_count(self):
        for rec in self:
            rec.member_count = len(rec.member_ids)

    @api.depends('member_ids', 'member_ids.role')
    def _compute_chairman(self):
        for rec in self:
            chairman = rec.member_ids.filtered(lambda m: m.role == 'chairman')
            rec.chairman_id = chairman[0].employee_id if chairman else False

    @api.constrains('member_ids')
    def _check_committee_has_chairman(self):
        for rec in self:
            if rec.member_ids and not any(m.role == 'chairman' for m in rec.member_ids):
                raise ValidationError(_('اللجنة يجب أن تحتوي على رئيس لجنة واحد على الأقل'))
            chairmen = [m for m in rec.member_ids if m.role == 'chairman']
            if len(chairmen) > 1:
                raise ValidationError(_('لا يمكن أن تحتوي اللجنة على أكثر من رئيس واحد'))

    def action_activate(self):
        for rec in self:
            if not rec.member_ids:
                raise UserError(_('يجب إضافة أعضاء اللجنة قبل تفعيلها'))
            rec.write({'state': 'active'})

    def action_close(self):
        for rec in self:
            rec.write({'state': 'closed'})

    def action_print_formation(self):
        return self.env.ref('procurement_committee.action_report_committee_formation').report_action(self)
