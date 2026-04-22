# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date


class BankGuarantee(models.Model):
    """
    خطاب الضمان البنكي — Bank Guarantee
    مُستخدَم في المناقصات والعقود الحكومية وفق قانون 182/2018
    أنواع: ابتدائي (5%) | نهائي (10%) | دفعة مقدمة | حسن تنفيذ
    """
    _name = 'port_said.bank.guarantee'
    _description = 'خطاب الضمان البنكي'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'issue_date desc'

    name = fields.Char(
        string='رقم خطاب الضمان', required=True, copy=False,
        readonly=True, default='/', tracking=True,
    )
    guarantee_type = fields.Selection([
        ('preliminary', 'تأمين ابتدائي — 5% من قيمة العقد'),
        ('final',       'تأمين نهائي — 10% من قيمة العقد'),
        ('advance',     'ضمان دفعة مقدمة'),
        ('performance', 'ضمان حسن التنفيذ'),
        ('maintenance', 'ضمان صيانة'),
    ], string='نوع خطاب الضمان', required=True, tracking=True)

    # ── تفاصيل الضمان ────────────────────────────────────────────
    issue_date = fields.Date(
        string='تاريخ الإصدار', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    expiry_date = fields.Date(
        string='تاريخ الانتهاء', required=True, tracking=True,
    )
    amount = fields.Monetary(
        string='قيمة الضمان', required=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency', default=lambda s: s.env.company.currency_id,
    )
    guarantee_percentage = fields.Float(
        string='نسبة الضمان %', digits=(5, 2),
    )

    # ── الأطراف ──────────────────────────────────────────────────
    issuing_bank = fields.Char(
        string='البنك المُصدِر', required=True,
    )
    bank_branch = fields.Char(string='الفرع')
    bank_ref_no = fields.Char(string='رقم مرجع البنك')
    beneficiary = fields.Char(
        string='الجهة المستفيدة',
        default='محافظة بورسعيد — الديوان العام',
    )
    vendor_id = fields.Many2one(
        'res.partner', string='المورد / المقاول',
        tracking=True,
    )

    # ── الربط بالتعاقدات ─────────────────────────────────────────
    purchase_order_id = fields.Many2one(
        'purchase.order', string='أمر الشراء / العقد',
    )
    contract_value = fields.Monetary(
        string='قيمة العقد الأصلية',
        currency_field='currency_id',
    )

    # ── الحالة ───────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',    'مسودة'),
        ('active',   'ساري المفعول'),
        ('extended', 'مُمدَّد'),
        ('released', 'مُفرَج عنه'),
        ('expired',  'منتهي الصلاحية'),
        ('forfeited','مُصادَر'),
    ], string='الحالة', default='draft', tracking=True)

    days_to_expiry = fields.Integer(
        string='أيام حتى الانتهاء',
        compute='_compute_days_to_expiry',
    )
    is_expiring_soon = fields.Boolean(
        string='ينتهي قريباً (30 يوم)',
        compute='_compute_days_to_expiry',
    )

    extension_history = fields.Text(string='تاريخ التمديدات')
    release_date = fields.Date(string='تاريخ الإفراج', readonly=True)
    release_reason = fields.Text(string='سبب الإفراج')
    notes = fields.Text(string='ملاحظات')

    @api.depends('expiry_date')
    def _compute_days_to_expiry(self):
        today = date.today()
        for rec in self:
            if rec.expiry_date:
                delta = (rec.expiry_date - today).days
                rec.days_to_expiry = delta
                rec.is_expiring_soon = 0 < delta <= 30
            else:
                rec.days_to_expiry = 0
                rec.is_expiring_soon = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'port_said.bank.guarantee') or '/'
        return super().create(vals_list)

    def action_activate(self):
        self.write({'state': 'active'})
        return True

    def action_extend(self):
        """تمديد خطاب الضمان"""
        self.ensure_one()
        old_expiry = self.expiry_date
        # يُستخدم مع wizard للتمديد — هنا نغير الحالة فقط
        self.write({'state': 'extended'})
        self.message_post(body=_(f'تم تمديد خطاب الضمان — تاريخ الانتهاء القديم: {old_expiry}'))
        return True

    def action_release(self):
        """الإفراج عن خطاب الضمان"""
        for rec in self:
            rec.write({
                'state': 'released',
                'release_date': date.today(),
            })
            rec.message_post(body=_(f'تم الإفراج عن خطاب الضمان بتاريخ {date.today()}'))
        return True

    def action_forfeit(self):
        """مصادرة خطاب الضمان"""
        for rec in self:
            rec.write({'state': 'forfeited'})
            rec.message_post(body=_('تم مصادرة خطاب الضمان'))
        return True
