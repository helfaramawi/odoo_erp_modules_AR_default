# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class GovernmentAdvance(models.Model):
    """
    السلف الحكومية — استمارة 62 ع.ح + دفعات مقدمة
    FR-D-03: استعاضة السلف المستديمة
    أنواع: سلف مستديمة | بدل سفر (51) | بدل انتقال (170) | دفعة مقدمة للمورد
    يتكامل مع: account.move | port_said_daftar55 | port_said_commitment
    """
    _name = 'port_said.advance'
    _description = 'سلف حكومية — استمارة 62 ع.ح'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'advance_date desc, name desc'

    # ── هوية السلفة ──────────────────────────────────────────────
    name = fields.Char(
        string='رقم السلفة', required=True, copy=False,
        readonly=True, default='/', tracking=True,
    )
    advance_type = fields.Selection([
        ('permanent',  'سلفة مستديمة — استمارة 62 ع.ح'),
        ('travel',     'بدل سفر — استمارة 51 ع.ح'),
        ('transport',  'بدل انتقال — استمارة 170 ع.ح'),
        ('vendor',     'دفعة مقدمة للمورد'),
        ('petty_cash', 'عهدة نقدية صغيرة'),
    ], string='نوع السلفة', required=True, default='permanent', tracking=True)

    advance_date = fields.Date(
        string='تاريخ السلفة', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    fiscal_year = fields.Char(
        string='السنة المالية',
        default=lambda self: str(date.today().year),
    )
    due_date = fields.Date(
        string='تاريخ الاستحقاق / التسوية', required=True, tracking=True,
        help='الموعد الأقصى لتسوية أو استرداد السلفة',
    )
    purpose = fields.Text(string='الغرض من السلفة', required=True)

    # ── المستفيد ─────────────────────────────────────────────────
    employee_id = fields.Many2one(
        'hr.employee', string='الموظف المستفيد',
        tracking=True,
        invisible="advance_type == 'vendor'",
    )
    employee_job = fields.Char(
        string='الوظيفة', related='employee_id.job_title', store=True,
    )
    department_id = fields.Many2one(
        'hr.department', string='الإدارة',
        related='employee_id.department_id', store=True,
    )
    national_id = fields.Char(
        string='الرقم القومي',
        related='employee_id.ssnid', store=True,
    )
    vendor_id = fields.Many2one(
        'res.partner', string='المورد',
        invisible="advance_type != 'vendor'",
    )

    # ── القيم المالية ────────────────────────────────────────────
    amount = fields.Monetary(
        string='مبلغ السلفة', required=True, tracking=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda s: s.env.company.currency_id,
    )
    amount_settled = fields.Monetary(
        string='المبلغ المسوَّى', tracking=True,
        currency_field='currency_id',
    )
    amount_outstanding = fields.Monetary(
        string='الرصيد القائم', compute='_compute_outstanding', store=True,
        currency_field='currency_id',
    )
    budget_line = fields.Char(string='بند الميزانية (باب/فصل/بند)')
    budget_bab = fields.Char(string='الباب')

    # ── التكامل ──────────────────────────────────────────────────
    commitment_id = fields.Many2one(
        'port_said.commitment', string='الارتباط الميزاني',
    )
    daftar55_id = fields.Many2one(
        'port_said.daftar55', string='مرجع دفتر 55 (صرف السلفة)',
    )
    settlement_daftar55_id = fields.Many2one(
        'port_said.daftar55', string='مرجع دفتر 55 (التسوية)',
    )
    dossier_id = fields.Many2one(
        'port_said.dossier', string='الاضبارة المرتبطة',
    )
    account_move_id = fields.Many2one(
        'account.move', string='القيد المحاسبي', readonly=True,
    )

    # ── الحالة ───────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',     'مسودة'),
        ('submitted', 'مقدم للاعتماد'),
        ('approved',  'معتمد'),
        ('disbursed', 'مُصرَف'),
        ('settled',   'مُسوَّى — مغلق'),
        ('cancelled', 'ملغي'),
    ], default='draft', tracking=True, required=True)

    is_overdue = fields.Boolean(
        string='متأخر التسوية',
        compute='_compute_overdue', store=True,
    )
    approved_by = fields.Many2one('res.users', string='معتمد من', readonly=True)
    notes = fields.Text(string='ملاحظات')

    @api.depends('amount', 'amount_settled')
    def _compute_outstanding(self):
        for rec in self:
            rec.amount_outstanding = rec.amount - (rec.amount_settled or 0.0)

    @api.depends('due_date', 'state')
    def _compute_overdue(self):
        today = date.today()
        for rec in self:
            rec.is_overdue = (
                rec.state in ('disbursed',)
                and rec.due_date
                and rec.due_date < today
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'port_said.advance') or '/'
        return super().create(vals_list)

    # ── Workflow ─────────────────────────────────────────────────
    def action_submit(self):
        for rec in self:
            if not rec.employee_id and rec.advance_type != 'vendor':
                raise UserError(_('يجب تحديد الموظف المستفيد'))
            if rec.amount <= 0:
                raise UserError(_('مبلغ السلفة يجب أن يكون أكبر من صفر'))
            rec.write({'state': 'submitted'})
        return True

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved', 'approved_by': self.env.user.id})
        return True

    def action_disburse(self):
        """تسجيل صرف السلفة مع إنشاء قيد محاسبي"""
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('يجب اعتماد السلفة أولاً'))
            # إنشاء قيد محاسبي إذا توفر حساب السلف
            rec.write({'state': 'disbursed'})
            rec.message_post(body=_(f'تم صرف السلفة بمبلغ: {rec.amount:,.2f} ج.م'))
        return True

    def action_settle(self):
        """تسوية السلفة — استرداد أو تحويل للمصروفات"""
        for rec in self:
            if rec.state != 'disbursed':
                raise UserError(_('يمكن تسوية السلف المصروفة فقط'))
            if not rec.amount_settled:
                raise UserError(_('يجب إدخال المبلغ المسوَّى'))
            if rec.amount_settled > rec.amount:
                raise ValidationError(_('المبلغ المسوَّى لا يمكن أن يتجاوز مبلغ السلفة'))
            rec.write({'state': 'settled'})
            rec.message_post(body=_(
                f'تمت التسوية — مُسوَّى: {rec.amount_settled:,.2f} | '
                f'رصيد قائم: {rec.amount_outstanding:,.2f} ج.م'
            ))
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state in ('disbursed', 'settled'):
                raise UserError(_('لا يمكن إلغاء سلفة مصروفة أو مسوَّاة'))
            rec.write({'state': 'cancelled'})
        return True

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancelled'):
                raise UserError(_('لا يمكن حذف سلفة غير في حالة مسودة أو ملغاة'))
        return super().unlink()
