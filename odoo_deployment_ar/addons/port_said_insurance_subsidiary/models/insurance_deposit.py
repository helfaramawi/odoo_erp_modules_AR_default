# -*- coding: utf-8 -*-
"""
إيداع تأمين نقدي أو بشيك
==========================
يغطي الحالات التي لا تندرج تحت خطاب الضمان البنكي:
- المناقصات الصغيرة حيث يُودَع المبلغ نقداً
- المناقصات التي تُقبَل فيها الشيكات كتأمين
- تأمينات أداء متغيرة

يُكمِّل port_said.bank.guarantee ليغطي الثلاث أعمدة في الدفتر الورقي:
خطاب ضمان | نقد | شيك
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class InsuranceDeposit(models.Model):
    _name = 'port_said.insurance_deposit'
    _description = 'إيداع تأمين نقدي / بشيك'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deposit_date desc, name desc'
    _rec_name = 'name'

    # ── الهوية ───────────────────────────────────────────────────────────────
    name = fields.Char(string='رقم الإيداع', required=True, copy=False,
        readonly=True, default='/', tracking=True)
    form78_sequence = fields.Char(string='تسلسل دفتر 78', readonly=True,
        copy=False, index=True)

    # ── التصنيف ──────────────────────────────────────────────────────────────
    deposit_type = fields.Selection([
        ('provisional', 'تأمين مؤقت (5%)'),
        ('final',       'تأمين نهائي (10%)'),
        ('advance',     'ضمان دفعة مقدمة'),
        ('performance', 'ضمان حسن التنفيذ'),
        ('maintenance', 'ضمان صيانة'),
    ], string='نوع التأمين', required=True, tracking=True)

    book_classification = fields.Selection([
        ('provisional', 'تأمين مؤقت (دفتر 19)'),
        ('final',       'تأمين نهائي (دفتر 20)'),
    ], string='تصنيف الدفتر', compute='_compute_book_classification',
       store=True, index=True)

    collateral_type = fields.Selection([
        ('cash',   'نقدية'),
        ('cheque', 'شيك'),
    ], string='صيغة الإيداع', required=True, default='cash', index=True)

    # ── الأطراف ─────────────────────────────────────────────────────────────
    vendor_id = fields.Many2one('res.partner', string='المورد / المقاول',
        required=True, tracking=True)
    purchase_order_id = fields.Many2one('purchase.order',
        string='أمر الشراء / العقد')
    contract_value = fields.Monetary(string='قيمة العقد',
        currency_field='currency_id')

    # ── المبلغ والعملة ───────────────────────────────────────────────────────
    amount = fields.Monetary(string='قيمة التأمين', required=True,
        currency_field='currency_id')
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)
    percentage = fields.Float(string='النسبة من العقد %', digits=(5, 2))

    # ── تفاصيل الإيداع النقدي ───────────────────────────────────────────────
    cash_receipt_number = fields.Char(string='رقم إيصال التوريد',
        help='مطلوب للتأمين النقدي — الإيصال الذي استلمه المورد من الخزينة.')
    cash_account_id = fields.Many2one('account.account',
        string='حساب الإيداع (الخزينة/البنك)',
        domain="[('account_type', 'in', ['asset_cash'])]")

    # ── تفاصيل الإيداع بشيك ─────────────────────────────────────────────────
    cheque_id = fields.Many2one('port_said.cheque',
        string='الشيك المُودَع',
        domain="[('direction', '=', 'incoming')]",
        help='مطلوب إن كانت صيغة الإيداع = شيك.')

    # ── التواريخ ─────────────────────────────────────────────────────────────
    deposit_date = fields.Date(string='تاريخ الإيداع', required=True,
        default=fields.Date.context_today)
    expiry_date = fields.Date(string='تاريخ الانتهاء المخطط',
        help='للتأمينات ذات فترة صلاحية (عادةً تأمين نهائي = مدة العقد).')
    release_date = fields.Date(string='تاريخ الإفراج', readonly=True)

    # ── الحالة ──────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',    'مسودة'),
        ('active',   'مُودَع'),
        ('released', 'مُفرَج عنه'),
        ('forfeited','مُصادَر'),
    ], string='الحالة', default='draft', tracking=True, required=True)

    release_reason = fields.Text(string='سبب الإفراج / المصادرة')

    # ── القيود المحاسبية ────────────────────────────────────────────────────
    activation_move_id = fields.Many2one('account.move',
        string='قيد الإيداع', readonly=True)
    release_move_id = fields.Many2one('account.move',
        string='قيد الإفراج', readonly=True)

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', readonly=True, copy=False)

    # ── الفولية ──────────────────────────────────────────────────────────────
    insurance_folio_id = fields.Many2one('port_said.insurance.folio',
        string='الفولية المرتبطة', readonly=True, index=True)

    notes = fields.Text(string='ملاحظات')
    company_id = fields.Many2one('res.company',
        default=lambda s: s.env.company)

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('deposit_type')
    def _compute_book_classification(self):
        for rec in self:
            if rec.deposit_type in ('final', 'performance'):
                rec.book_classification = 'final'
            else:
                rec.book_classification = 'provisional'

    # ── Constraints ──────────────────────────────────────────────────────────
    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('قيمة التأمين يجب أن تكون موجبة.'))

    @api.constrains('collateral_type', 'cash_receipt_number', 'cheque_id')
    def _check_collateral_details(self):
        for rec in self:
            if rec.collateral_type == 'cash' and not rec.cash_receipt_number:
                raise ValidationError(_(
                    'التأمين النقدي يتطلب رقم إيصال التوريد.'))
            if rec.collateral_type == 'cheque' and not rec.cheque_id:
                raise ValidationError(_(
                    'الإيداع بشيك يتطلب تحديد الشيك المُستلَم.'))

    @api.constrains('cheque_id', 'amount')
    def _check_cheque_amount_matches(self):
        for rec in self:
            if rec.cheque_id and abs(rec.cheque_id.amount - rec.amount) > 0.01:
                raise ValidationError(_(
                    'مبلغ الشيك (%s) لا يطابق قيمة التأمين (%s).'
                ) % (rec.cheque_id.amount, rec.amount))

    # ── Create ───────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'port_said.insurance_deposit') or '/'
        return super().create(vals_list)

    # ── Lifecycle ────────────────────────────────────────────────────────────
    def action_activate(self):
        """يُفعِّل التأمين ويُنشئ قيد الإيداع."""
        Seq = self.env['ir.sequence']
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('الإيداع ليس في حالة مسودة.'))

            # Set fiscal year
            if rec.deposit_date and not rec.fiscal_year:
                m, y = rec.deposit_date.month, rec.deposit_date.year
                if m >= 7:
                    rec.fiscal_year = '%d/%d' % (y, y + 1)
                else:
                    rec.fiscal_year = '%d/%d' % (y - 1, y)

            rec.state = 'active'

            # Legal sequence
            if not rec.form78_sequence:
                seq_code = ('port_said.insurance.final'
                           if rec.book_classification == 'final'
                           else 'port_said.insurance.provisional')
                rec.form78_sequence = Seq.next_by_code(seq_code) or '/'

            # Accounting move
            if not rec.activation_move_id:
                rec._create_activation_move()

            # Folio movement
            rec._create_folio_movement('deposit')

    def _create_activation_move(self):
        """قيد الإيداع: Dr خزينة / Cr التزام تأمينات (حقيقي، ليس نظامي)."""
        self.ensure_one()
        if self.collateral_type == 'cheque':
            # الشيكات تُسجَّل عبر cheque.action_deposit — لا ننشئ قيداً هنا
            return

        company = self.company_id
        dr_account = self.cash_account_id or company.insurance_cash_asset_account_id
        cr_account = company.insurance_cash_liability_account_id

        if not dr_account or not cr_account:
            self.message_post(body=_(
                '⚠ لم يُنشأ قيد الإيداع لعدم تعيين حسابات التأمينات النقدية '
                'في إعدادات الشركة.'))
            return

        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', company.id),
        ], limit=1)
        if not journal:
            return

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': self.deposit_date,
            'ref': _('إيداع تأمين %s') % self.name,
            'line_ids': [
                (0, 0, {
                    'account_id': dr_account.id,
                    'partner_id': self.vendor_id.id,
                    'name': _('تأمين %s من %s') % (
                        self.name, self.vendor_id.name),
                    'debit': self.amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': cr_account.id,
                    'partner_id': self.vendor_id.id,
                    'name': _('التزام بإرجاع تأمين %s') % self.name,
                    'debit': 0.0,
                    'credit': self.amount,
                }),
            ],
        })
        self.activation_move_id = move.id

    def action_release(self):
        """إفراج عن التأمين بعد انتهاء العقد / اعتماد التسليم."""
        for rec in self:
            if rec.state != 'active':
                raise UserError(_('الإيداع ليس مُودَعاً.'))
            if not rec.release_reason:
                raise UserError(_('يجب تسجيل سبب الإفراج.'))
            rec.state = 'released'
            rec.release_date = fields.Date.today()
            if rec.activation_move_id and rec.collateral_type == 'cash':
                reverse = rec.activation_move_id._reverse_moves(
                    default_values_list=[{
                        'date': rec.release_date,
                        'ref': _('إفراج عن تأمين %s') % rec.name,
                    }], cancel=True)
                rec.release_move_id = reverse.id if reverse else False
            rec._create_folio_movement('withdrawal')

    def action_forfeit(self):
        """مصادرة — يتطلب صلاحية مدير."""
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('المصادرة تتطلب صلاحية مدير حسابات.'))
        for rec in self:
            if rec.state != 'active':
                raise UserError(_('الإيداع ليس مُودَعاً.'))
            if not rec.release_reason:
                raise UserError(_('يجب تسجيل سبب المصادرة.'))
            rec.state = 'forfeited'
            rec.release_date = fields.Date.today()
            rec._create_forfeiture_move()
            rec._create_folio_movement('forfeiture')

    def _create_forfeiture_move(self):
        """قيد المصادرة: Dr التزام / Cr إيراد مصادرة."""
        self.ensure_one()
        if self.collateral_type != 'cash':
            return

        company = self.company_id
        dr_account = company.insurance_cash_liability_account_id
        cr_account = company.insurance_forfeiture_revenue_account_id

        if not dr_account or not cr_account:
            self.message_post(body=_(
                '⚠ لم يُنشأ قيد المصادرة — الحسابات غير معيَّنة.'))
            return

        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', company.id),
        ], limit=1)
        if not journal:
            return

        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': fields.Date.today(),
            'ref': _('مصادرة تأمين %s') % self.name,
            'line_ids': [
                (0, 0, {
                    'account_id': dr_account.id,
                    'partner_id': self.vendor_id.id,
                    'name': _('مصادرة تأمين %s') % self.name,
                    'debit': self.amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': cr_account.id,
                    'name': _('إيراد مصادرة تأمين %s') % self.name,
                    'debit': 0.0,
                    'credit': self.amount,
                }),
            ],
        })
        # We use release_move_id to store the forfeiture move too
        self.release_move_id = move.id

    def _create_folio_movement(self, movement_type):
        self.ensure_one()
        self.env['port_said.insurance.movement'].create({
            'movement_type': movement_type,
            'movement_date': fields.Date.today(),
            'partner_id': self.vendor_id.id,
            'collateral_type': self.collateral_type,
            'insurance_deposit_id': self.id,
            'amount': self.amount,
            'description': _('%s %s') % (
                _('إيداع') if movement_type == 'deposit' else
                _('استرداد') if movement_type == 'withdrawal' else
                _('مصادرة'),
                self.name),
        })
