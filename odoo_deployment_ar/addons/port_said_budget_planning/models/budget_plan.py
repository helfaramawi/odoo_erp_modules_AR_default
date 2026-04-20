# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class BudgetPlan(models.Model):
    """
    الموازنة التقديرية الحكومية
    FR-S-01: إعداد الموازنة وفق تصنيف الموازنة المصرية (أبواب/فصول/بنود/أنواع)
    """
    _name = 'port_said.budget.plan'
    _description = 'الموازنة التقديرية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'fiscal_year desc, name'

    name = fields.Char(
        string='اسم الموازنة', required=True, tracking=True,
    )
    fiscal_year = fields.Integer(
        string='السنة المالية', required=True,
        default=lambda self: date.today().year, tracking=True,
    )
    date_from = fields.Date(string='من تاريخ', required=True)
    date_to = fields.Date(string='إلى تاريخ', required=True)

    department = fields.Char(string='الإدارة / المصلحة', tracking=True)
    responsible_id = fields.Many2one('res.users', string='المسؤول عن الموازنة')

    line_ids = fields.One2many(
        'port_said.budget.line', 'plan_id', string='بنود الموازنة',
    )

    state = fields.Selection([
        ('draft',    'مسودة'),
        ('submitted','مقدم للاعتماد'),
        ('approved', 'معتمد'),
        ('active',   'جاري التنفيذ'),
        ('closed',   'مغلق'),
    ], default='draft', tracking=True)

    # ── إحصاءات الموازنة ─────────────────────────────────────────
    total_approved = fields.Monetary(
        string='إجمالي الاعتمادات', compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    total_committed = fields.Monetary(
        string='إجمالي الارتباطات', compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    total_actual = fields.Monetary(
        string='إجمالي المصروف الفعلي', compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    total_available = fields.Monetary(
        string='الرصيد المتاح', compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    execution_rate = fields.Float(
        string='نسبة التنفيذ %', compute='_compute_totals', store=True,
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda s: s.env.company.currency_id,
    )
    notes = fields.Text(string='ملاحظات')
    approved_by = fields.Many2one('res.users', string='معتمد من', readonly=True)

    @api.depends('line_ids.amount_approved', 'line_ids.amount_committed',
                 'line_ids.amount_actual')
    def _compute_totals(self):
        for rec in self:
            rec.total_approved = sum(rec.line_ids.mapped('amount_approved'))
            rec.total_committed = sum(rec.line_ids.mapped('amount_committed'))
            rec.total_actual = sum(rec.line_ids.mapped('amount_actual'))
            rec.total_available = rec.total_approved - rec.total_committed - rec.total_actual
            rec.execution_rate = (
                (rec.total_actual / rec.total_approved * 100)
                if rec.total_approved > 0 else 0.0
            )

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('يجب إضافة بنود الموازنة أولاً'))
            rec.write({'state': 'submitted'})
        return True

    def action_approve(self):
        for rec in self:
            rec.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
            })
            rec.message_post(body=_(f'تمت الموافقة على الموازنة من {self.env.user.name}'))
        return True

    def action_activate(self):
        for rec in self:
            if rec.state != 'approved':
                raise UserError(_('يجب اعتماد الموازنة أولاً'))
            rec.write({'state': 'active'})
        return True

    def action_close(self):
        self.write({'state': 'closed'})
        return True

    def action_compute_actual(self):
        """تحديث المصروف الفعلي من دفتر 55 والقيود المحاسبية"""
        for rec in self:
            for line in rec.line_ids:
                line._compute_actual_from_daftar55()
        return True


class BudgetLine(models.Model):
    """بند الموازنة — مستوى التصنيف الحكومي"""
    _name = 'port_said.budget.line'
    _description = 'بند الموازنة التقديرية'
    _order = 'bab, fasle, band, noa'

    plan_id = fields.Many2one(
        'port_said.budget.plan', string='الموازنة',
        required=True, ondelete='cascade', index=True,
    )

    # ── تصنيف الموازنة المصرية ────────────────────────────────────
    bab = fields.Char(string='الباب', required=True, size=2)
    fasle = fields.Char(string='الفصل', size=4)
    band = fields.Char(string='البند', size=6)
    noa = fields.Char(string='النوع', size=8)
    full_code = fields.Char(
        string='الكود الكامل', compute='_compute_full_code', store=True,
    )
    description = fields.Char(string='الوصف / التسمية', required=True)
    budget_category = fields.Selection([
        ('wages',      'أجور ومرتبات'),
        ('purchases',  'مشتريات وتوريدات'),
        ('services',   'خدمات'),
        ('assets',     'أصول ثابتة ومعدات'),
        ('maintenance','صيانة وإصلاح'),
        ('utilities',  'مرافق (كهرباء/مياه)'),
        ('other',      'بنود أخرى'),
    ], string='تصنيف البند', required=True, default='other')

    account_id = fields.Many2one(
        'account.account', string='حساب الأستاذ المرتبط',
    )
    dimension_id = fields.Many2one(
        'financial.dimension', string='البعد المالي',
        domain="[('dimension_type','=','department')]",
    )

    # ── القيم ────────────────────────────────────────────────────
    amount_approved = fields.Monetary(
        string='الاعتماد المعتمد', required=True,
        currency_field='currency_id',
    )
    amount_committed = fields.Monetary(
        string='الارتباطات المرصودة',
        compute='_compute_committed', store=True,
        currency_field='currency_id',
    )
    amount_actual = fields.Monetary(
        string='المصروف الفعلي',
        currency_field='currency_id',
    )
    amount_available = fields.Monetary(
        string='الرصيد المتاح',
        compute='_compute_available', store=True,
        currency_field='currency_id',
    )
    variance = fields.Monetary(
        string='الانحراف', compute='_compute_variance', store=True,
        currency_field='currency_id',
        help='موجب = وفر | سالب = تجاوز',
    )
    variance_pct = fields.Float(
        string='نسبة الانحراف %', compute='_compute_variance', store=True,
    )
    execution_pct = fields.Float(
        string='نسبة التنفيذ %', compute='_compute_available', store=True,
    )
    currency_id = fields.Many2one(
        related='plan_id.currency_id',
    )
    notes = fields.Char(string='ملاحظات')

    @api.depends('bab', 'fasle', 'band', 'noa')
    def _compute_full_code(self):
        for rec in self:
            parts = [x for x in [rec.bab, rec.fasle, rec.band, rec.noa] if x]
            rec.full_code = '/'.join(parts)

    @api.depends('plan_id.fiscal_year', 'full_code')
    def _compute_committed(self):
        """استخراج الارتباطات من دفتر الارتباطات"""
        for line in self:
            if not line.plan_id or not line.full_code:
                line.amount_committed = 0.0
                continue
            commitments = self.env['port_said.commitment'].search([
                ('fiscal_year', '=', line.plan_id.fiscal_year),
                ('budget_line_code', '=', line.full_code),
                ('state', 'in', ['approved', 'reserved', 'cleared']),
            ])
            line.amount_committed = sum(commitments.mapped('amount_requested'))

    @api.depends('amount_approved', 'amount_committed', 'amount_actual')
    def _compute_available(self):
        for line in self:
            line.amount_available = (
                line.amount_approved - line.amount_committed - line.amount_actual
            )
            line.execution_pct = (
                (line.amount_actual / line.amount_approved * 100)
                if line.amount_approved > 0 else 0.0
            )

    @api.depends('amount_approved', 'amount_actual')
    def _compute_variance(self):
        for line in self:
            line.variance = line.amount_approved - line.amount_actual
            line.variance_pct = (
                (line.variance / line.amount_approved * 100)
                if line.amount_approved > 0 else 0.0
            )

    def _compute_actual_from_daftar55(self):
        """حساب المصروف الفعلي من دفتر 55"""
        self.ensure_one()
        if not self.plan_id or not self.full_code:
            return
        daftar55_lines = self.env['port_said.daftar55'].search([
            ('fiscal_year', '=', str(self.plan_id.fiscal_year)),
            ('budget_line', '=', self.full_code),
            ('state', 'in', ['posted', 'archived']),
        ])
        self.amount_actual = sum(daftar55_lines.mapped('amount_gross'))
