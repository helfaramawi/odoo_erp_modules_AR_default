# -*- coding: utf-8 -*-
"""
الكفالات (Sureties)
====================
دفتر حساب الكفالات - استمارة 78 ع.ح.

الكفالة = مبلغ مالي أو ضمان شخصي يُسجَّل على موظف أو جهة كضمان
لحسن الأداء أو عهدة مستديمة. هذا الدفتر يختلف عن البنك الضمان في
port_said_advances لأن الأخير للموردين/المقاولين، بينما الكفالة هنا
داخلية غالباً (موظفون، عاملون، أمناء خزائن).
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Surety(models.Model):
    _name = 'port_said.surety'
    _description = 'كفالة'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'registration_date desc, sequence_number desc'
    _rec_name = 'display_name'

    # ── الترقيم ──────────────────────────────────────────────────────────────
    sequence_number = fields.Char(
        string='رقم بالدفتر', readonly=True, copy=False, index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ── نوع الكفالة ─────────────────────────────────────────────────────────
    surety_type = fields.Selection([
        ('personal',  'شخصية (كفيل فرد)'),
        ('cash',      'نقدية (إيداع مالي)'),
        ('mixed',     'مختلطة'),
    ], string='نوع الكفالة', required=True, default='cash', index=True)

    # ── الأطراف ─────────────────────────────────────────────────────────────
    employee_id = fields.Many2one('hr.employee',
        string='الموظف المكفول', required=True)
    employee_job = fields.Char(string='وظيفة المكفول',
        related='employee_id.job_title', store=True)
    national_id = fields.Char(string='الرقم القومي',
        related='employee_id.identification_id', store=True)

    guarantor_partner_id = fields.Many2one('res.partner',
        string='الكفيل', help='للكفالات الشخصية: من يكفل الموظف.')
    guarantor_national_id = fields.Char(string='الرقم القومي للكفيل')

    # ── المبالغ ──────────────────────────────────────────────────────────────
    amount = fields.Monetary(string='قيمة الكفالة',
        required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    cash_deposit_amount = fields.Monetary(
        string='المُودَع نقداً',
        currency_field='currency_id',
        help='الجزء النقدي من الكفالة — للكفالات من نوع cash أو mixed.')
    cash_deposit_account_id = fields.Many2one('account.account',
        string='حساب الإيداع',
        domain="[('account_type', '=', 'asset_cash')]",
        help='الحساب الذي يحتفظ بالمبلغ النقدي المودَع.')

    # ── الغرض ───────────────────────────────────────────────────────────────
    purpose = fields.Selection([
        ('permanent_imprest', 'عهدة مستديمة'),
        ('temporary_imprest', 'عهدة مؤقتة'),
        ('position',          'كفالة الوظيفة (أمين خزينة / مخازن)'),
        ('other',             'أخرى'),
    ], string='الغرض', required=True, default='position')
    purpose_detail = fields.Text(string='تفاصيل الغرض')

    # ── التواريخ ────────────────────────────────────────────────────────────
    registration_date = fields.Date(string='تاريخ القيد',
        default=fields.Date.today, required=True)
    effective_from = fields.Date(string='سارية من', required=True)
    review_date = fields.Date(string='تاريخ المراجعة',
        help='التاريخ المخطط لمراجعة الكفالة (كل سنة مالياً عادةً).')
    release_date = fields.Date(string='تاريخ الإفراج', readonly=True)

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',     'مسودة'),
        ('active',    'سارية'),
        ('suspended', 'موقوفة'),
        ('released',  'مُفرَج عنها'),
        ('forfeited', 'مُصادَرة'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    release_reason = fields.Text(string='سبب الإفراج / المصادرة')

    # ── الربط المحاسبي ──────────────────────────────────────────────────────
    move_id = fields.Many2one('account.move',
        string='القيد المحاسبي للإيداع', readonly=True)

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', readonly=True, copy=False)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.depends('sequence_number', 'employee_id', 'amount')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '%s — %s — %s ج.م.' % (
                rec.sequence_number or '—',
                rec.employee_id.name or '?',
                rec.amount or 0,
            )

    @api.constrains('amount', 'cash_deposit_amount')
    def _check_amounts(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('قيمة الكفالة يجب أن تكون موجبة.'))
            if rec.surety_type == 'cash' and rec.cash_deposit_amount != rec.amount:
                raise ValidationError(_(
                    'الكفالة النقدية: المُودَع يجب أن يساوي قيمة الكفالة.'))
            if rec.surety_type == 'mixed' and rec.cash_deposit_amount >= rec.amount:
                raise ValidationError(_(
                    'الكفالة المختلطة: المُودَع نقداً يجب أن يكون أقل من الإجمالي.'))

    @api.constrains('surety_type', 'guarantor_partner_id')
    def _check_guarantor(self):
        for rec in self:
            if rec.surety_type in ('personal', 'mixed') and not rec.guarantor_partner_id:
                raise ValidationError(_(
                    'الكفالة الشخصية أو المختلطة تتطلب تحديد الكفيل.'))

    # ── دورة الحياة ──────────────────────────────────────────────────────────
    def action_activate(self):
        Seq = self.env['ir.sequence']
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الكفالة ليست في حالة مسودة.'))
            if not rec.sequence_number:
                rec.sequence_number = Seq.next_by_code('port_said.surety') or '/'
            if rec.registration_date and not rec.fiscal_year:
                m = rec.registration_date.month
                y = rec.registration_date.year
                if m >= 7:
                    rec.fiscal_year = '%d/%d' % (y, y + 1)
                else:
                    rec.fiscal_year = '%d/%d' % (y - 1, y)
            rec.state = 'active'

    def action_suspend(self):
        for rec in self:
            if rec.state != 'active':
                raise UserError(_('الكفالة ليست سارية.'))
            rec.state = 'suspended'

    def action_resume(self):
        for rec in self:
            if rec.state != 'suspended':
                raise UserError(_('الكفالة ليست موقوفة.'))
            rec.state = 'active'

    def action_release(self):
        for rec in self:
            if rec.state not in ('active', 'suspended'):
                raise UserError(_('لا يمكن الإفراج عن كفالة غير سارية.'))
            if not rec.release_reason:
                raise UserError(_('يجب تسجيل سبب الإفراج.'))
            rec.state = 'released'
            rec.release_date = fields.Date.today()

    def action_forfeit(self):
        """مصادرة — تتطلب موافقة مدير."""
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('المصادرة تتطلب صلاحية مدير حسابات.'))
        for rec in self:
            if rec.state not in ('active', 'suspended'):
                raise UserError(_('لا يمكن مصادرة كفالة غير سارية.'))
            if not rec.release_reason:
                raise UserError(_('يجب تسجيل سبب المصادرة.'))
            rec.state = 'forfeited'
            rec.release_date = fields.Date.today()
            rec.message_post(body=_('تمت المصادرة بواسطة %s. السبب: %s')
                              % (self.env.user.name, rec.release_reason))
