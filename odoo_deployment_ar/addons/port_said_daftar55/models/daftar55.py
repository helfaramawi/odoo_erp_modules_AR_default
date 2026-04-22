from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


# ── التفقيط ───────────────────────────────────────────────────────────────────
_ONES = ['', 'واحد', 'اثنان', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة',
         'عشرة', 'أحد عشر', 'اثنا عشر', 'ثلاثة عشر', 'أربعة عشر', 'خمسة عشر',
         'ستة عشر', 'سبعة عشر', 'ثمانية عشر', 'تسعة عشر']
_TENS     = ['', '', 'عشرون', 'ثلاثون', 'أربعون', 'خمسون', 'ستون', 'سبعون', 'ثمانون', 'تسعون']
_HUNDREDS = ['', 'مئة', 'مئتان', 'ثلاثمئة', 'أربعمئة', 'خمسمئة', 'ستمئة', 'سبعمئة', 'ثمانمئة', 'تسعمئة']

def _three(n):
    if n == 0: return ''
    h, r = divmod(n, 100)
    t, o = divmod(r, 10)
    parts = []
    if h: parts.append(_HUNDREDS[h])
    if r < 20 and r > 0: parts.append(_ONES[r])
    elif t:
        parts.append(f'{_ONES[o]} و{_TENS[t]}' if o else _TENS[t])
    return ' و'.join(parts)

def amount_to_words(amount):
    if not amount: return ''
    amount = round(float(amount), 2)
    pounds, piasters = int(amount), round((amount - int(amount)) * 100)
    billions, r  = divmod(pounds, 1_000_000_000)
    millions, r  = divmod(r, 1_000_000)
    thousands, r = divmod(r, 1_000)
    parts = []
    if billions:  parts.append(f'{_three(billions)} مليار' if billions > 2 else ['', 'مليار', 'ملياران'][billions])
    if millions:  parts.append(f'{_three(millions)} مليون' if millions > 2 else ['', 'مليون', 'مليونان'][millions])
    if thousands: parts.append(f'{_three(thousands)} ألف'  if thousands > 2 else ['', 'ألف', 'ألفان'][thousands])
    if r: parts.append(_three(r))
    result = ' و'.join(p for p in parts if p) or 'صفر'
    result += ' جنيه'
    if piasters: result += f' و{_ONES[piasters] if piasters < 20 else _three(piasters)} قرش'
    return result + ' فقط لا غير'


class Daftar55(models.Model):
    _name = 'port_said.daftar55'
    _description = 'دفتر 55 ع.ح - سجل الصرف وأوامر الدفع'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence_number desc'
    _rec_name = 'sequence_number'

    # ── رقم المسلسل ──────────────────────────────────────────────────────────
    sequence_number = fields.Char(string='رقم المسلسل بدفتر 55', readonly=True, copy=False, index=True)
    fiscal_year     = fields.Char(string='السنة المالية', readonly=True, copy=False)

    # ── قسم أ ─────────────────────────────────────────────────────────────────
    department_name  = fields.Char(string='اسم المصلحة', required=True)
    division_name    = fields.Char(string='القسم / الإدارة')
    date_received    = fields.Date(string='تاريخ ورود الاستمارة', required=True, default=fields.Date.today)
    date_returned    = fields.Date(string='تاريخ الإعادة من المراجع')
    form50_ref       = fields.Char(string='رقم استمارة 50', required=True, index=True)
    register_z_ref   = fields.Char(string='تقييد في سجل "ز" رقم')
    writer_assigned  = fields.Char(string='الكاتب المنوط')
    attachment_count_declared = fields.Integer(string='عدد المرفقات')
    real_attachment_count = fields.Integer(
        string='العدد الفعلي للمرفقات',
        compute='_compute_real_attachment_count'
    )

    # ── بيانات صاحب الحق ─────────────────────────────────────────────────────
    vendor_id        = fields.Many2one('res.partner', string='اسم الشركة / صاحب الحق', required=True)
    national_id      = fields.Char(string='رقم القومي / رقم الحساب')
    bank_name        = fields.Char(string='اسم البنك')
    bank_branch      = fields.Char(string='الفرع')
    bank_account_no  = fields.Char(string='رقم الحساب البنكي')
    iban             = fields.Char(string='رقم IBAN')
    payment_method   = fields.Selection([
        ('bank_transfer', 'تحويل بنكي'),
        ('central_bank_check', 'شيك على البنك المركزي'),
        ('payment_order', 'أمر دفع إلكتروني'),
    ], string='طريقة الصرف', default='bank_transfer')

    # ── الموازنة ──────────────────────────────────────────────────────────────
    budget_line  = fields.Char(string='بند الميزانية', required=True)
    budget_bab   = fields.Char(string='باب')
    budget_fasle = fields.Char(string='فصل')

    # ── المبالغ والاستقطاعات ─────────────────────────────────────────────────
    amount_gross = fields.Monetary(string='إجمالي الأصل', required=True, currency_field='currency_id')
    deductions_stamp_normal       = fields.Monetary(string='الدمغة العادية (1%)',    compute='_compute_deductions', store=True, currency_field='currency_id')
    deductions_stamp_extra        = fields.Monetary(string='الدمغة الإضافية (3×)',   compute='_compute_deductions', store=True, currency_field='currency_id')
    deductions_stamp_proportional = fields.Monetary(string='الدمغة النسبية (0.008)', compute='_compute_deductions', store=True, currency_field='currency_id')
    deductions_commercial_tax     = fields.Monetary(string='ضريبة الأرباح (3%)',     compute='_compute_deductions', store=True, currency_field='currency_id')
    total_deductions              = fields.Monetary(string='إجمالي الاستقطاعات',     compute='_compute_deductions', store=True, currency_field='currency_id')
    amount_net                    = fields.Monetary(string='صافي المبلغ',             compute='_compute_deductions', store=True, currency_field='currency_id')
    amount_words                  = fields.Char(string='الصافي بالتفقيط',             compute='_compute_deductions', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # ── قسم ج — المراجعة ─────────────────────────────────────────────────────
    reviewer_id         = fields.Many2one('res.users', string='المراجع')
    reviewer_stamp_date = fields.Date(string='تاريخ ختم "روجع"')
    auditor_id          = fields.Many2one('res.users', string='مراقب الحسابات')
    accounts_head_id    = fields.Many2one('res.users', string='رئيس الحسابات')
    section_head_id     = fields.Many2one('res.users', string='رئيس المصلحة')

    # ── قسم د — مراجع (نصية فقط لتجنب circular deps) ────────────────────────
    daftar224_sequence  = fields.Char(string='رقم مسلسل دفتر 224 (قسم د)', readonly=True)
    crossout_signed     = fields.Boolean(string='وُقِّع موظفو الشطب')
    crossout_signed_by  = fields.Char(string='موظف الشطب')

    # ── روابط نصية ───────────────────────────────────────────────────────────
    payment_order_ref = fields.Char(string='رقم أمر الدفع')
    dossier_ref       = fields.Char(string='رقم الاضبارة', readonly=True)
    commitment_ref    = fields.Char(string='رقم الارتباط', index=True, help='رقم الارتباط المرتبط بهذا القيد — يُربط برقم الارتباط من دفتر الارتباطات')

    notes      = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    state      = fields.Selection([
        ('draft',    'مسودة'),
        ('received', 'مستلم'),
        ('reviewed', 'تحت المراجعة'),
        ('cleared',  'مُسمَّح'),
        ('posted',   'مرحّل'),
        ('archived', 'محفوظ'),
    ], default='draft', string='الحالة', tracking=True)

    @api.depends('amount_gross')
    def _compute_deductions(self):
        for rec in self:
            g = rec.amount_gross or 0.0
            normal = round(g * 0.01, 2)
            extra  = round(normal * 3, 2)
            prop   = round(max(g - 50.0, 0) * 0.008, 2)
            prop   = round(prop * 2) / 2
            comm   = round(g * 0.03, 2)
            total  = normal + extra + prop + comm
            rec.deductions_stamp_normal       = normal
            rec.deductions_stamp_extra        = extra
            rec.deductions_stamp_proportional = prop
            rec.deductions_commercial_tax     = comm
            rec.total_deductions              = total
            rec.amount_net                    = round(g - total, 2)
            rec.amount_words                  = amount_to_words(round(g - total, 2))
    @api.depends('dossier_ref')
    def _compute_real_attachment_count(self):
        dossier_model = self.env['port_said.dossier']
        for rec in self:
            dossier = dossier_model.search([('daftar55_id', '=', rec.id)], limit=1)
            rec.real_attachment_count = dossier.attachment_count if dossier else 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sequence_number'):
                vals['sequence_number'] = self.env['ir.sequence'].next_by_code('port_said.daftar55') or '/'
                vals['fiscal_year'] = str(fields.Date.today().year)
        return super().create(vals_list)

    def unlink(self):
        raise UserError(_('لا يمكن حذف سجلات دفتر 55 ع.ح — لائحة المالية.'))

    def write(self, vals):
        if 'sequence_number' in vals:
            raise ValidationError(_('لا يمكن تعديل رقم المسلسل بدفتر 55 بعد الإنشاء.'))
        return super().write(vals)

    def action_receive(self):       self.write({'state': 'received'})
    def action_send_for_review(self): self.write({'state': 'reviewed', 'reviewer_id': self.env.uid})
    def action_clear(self):         self.write({'state': 'cleared', 'reviewer_stamp_date': fields.Date.today()})

    def action_post(self):
        for rec in self:
            if rec.state != 'cleared':
                raise UserError(_('يجب التسميح أولاً قبل الترحيل.'))
            self.env['port_said.daftar224'].create_dual_entry_from_daftar55(rec.id)
            rec.write({'state': 'posted'})

    def action_archive_dossier(self):
        self.write({'state': 'archived'})

    def action_print_daftar55(self):
        return self.env.ref('port_said_daftar55.action_report_daftar55').report_action(self)
