# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class AssetDisposal(models.Model):
    """
    التصرف في الأصل الثابت — Asset Disposal
    البيع / الاستغناء / التحويل — مع قيد محاسبي كامل
    مرتبط بوحدة المزادات للبيع الحكومي
    """
    _name = 'port_said.asset.disposal'
    _description = 'التصرف في أصل ثابت'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'disposal_date desc'

    name = fields.Char(
        string='رقم قرار التصرف', required=True, copy=False,
        default='/', readonly=True
    )
    asset_id = fields.Many2one(
        'port_said.fixed.asset', string='الأصل الثابت',
        required=True, tracking=True, ondelete='restrict',
        domain="[('state', '=', 'active')]"
    )
    disposal_type = fields.Selection([
        ('sale',          'بيع — مزاد حكومي'),
        ('scrap',         'شطب / خردة'),
        ('transfer',      'تحويل لجهة حكومية أخرى'),
        ('loss',          'فقدان / تلف'),
    ], string='نوع التصرف', required=True, tracking=True)

    disposal_date = fields.Date(
        string='تاريخ التصرف', required=True,
        default=date.today, tracking=True
    )
    sale_value = fields.Monetary(
        string='قيمة البيع الفعلية (ج.م)',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        related='asset_id.currency_id'
    )
    # ربط بالمزاد الحكومي
    auction_id = fields.Many2one(
        'auction.request', string='طلب المزاد المرتبط',
        domain="[('state', 'in', ['awarded', 'done'])]",
        help='الربط بوحدة المزادات الحكومية عند البيع'
    )

    # بيانات محاسبية
    book_value_at_disposal = fields.Monetary(
        string='القيمة الدفترية عند التصرف',
        related='asset_id.book_value', readonly=True
    )
    gain_loss = fields.Monetary(
        string='أرباح / (خسائر) التصرف',
        compute='_compute_gain_loss', store=True
    )
    move_id = fields.Many2one(
        'account.move', string='قيد التصرف', readonly=True
    )
    state = fields.Selection([
        ('draft',    'مسودة'),
        ('approved', 'معتمد'),
        ('posted',   'مُرحَّل'),
    ], default='draft', tracking=True)

    approval_user_id = fields.Many2one('res.users', string='معتمد من')
    notes = fields.Text(string='ملاحظات / قرار اللجنة')

    @api.depends('sale_value', 'book_value_at_disposal')
    def _compute_gain_loss(self):
        for rec in self:
            rec.gain_loss = rec.sale_value - rec.book_value_at_disposal

    def action_approve(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('يمكن اعتماد التصرف من حالة مسودة فقط'))
        if self.name == '/':
            self.name = self.env['ir.sequence'].next_by_code(
                'port_said.asset.disposal'
            ) or '/'
        self.state = 'approved'
        self.approval_user_id = self.env.user
        self.message_post(body=_(f'تم اعتماد قرار التصرف من {self.env.user.name}'))
        return True

    def action_post(self):
        """إنشاء قيد التصرف وإنهاء الأصل"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('يجب اعتماد التصرف أولاً'))
        asset = self.asset_id
        cat = asset.category_id

        # ترحيل أي إهلاك متبقي حتى تاريخ التصرف
        pending_lines = asset.depreciation_line_ids.filtered(
            lambda l: not l.move_id and l.depreciation_date <= self.disposal_date
        )
        for line in pending_lines:
            line.action_post()

        book_value = asset.book_value
        lines = [
            # إلغاء التكلفة الأصلية
            (0, 0, {
                'account_id': cat.depreciation_account_id.id,
                'name': f'إلغاء مجمع إهلاك — {asset.name}',
                'debit': asset.accumulated_depreciation,
                'credit': 0.0,
            }),
        ]
        if self.disposal_type == 'sale' and self.sale_value > 0:
            lines.append((0, 0, {
                'account_id': self.env['account.account'].search(
                    [('account_type', '=', 'asset_cash')], limit=1
                ).id or cat.asset_account_id.id,
                'name': f'حصيلة بيع — {asset.name}',
                'debit': self.sale_value,
                'credit': 0.0,
            }))

        # إلغاء قيمة الأصل الأصلية
        lines.append((0, 0, {
            'account_id': cat.asset_account_id.id,
            'name': f'إلغاء قيمة الأصل — {asset.name}',
            'debit': 0.0,
            'credit': asset.purchase_value,
        }))

        # أرباح أو خسائر التصرف
        gl = self.sale_value - book_value
        if abs(gl) > 0.01:
            if gl > 0:
                acc = cat.gain_account_id
                lines.append((0, 0, {
                    'account_id': acc.id if acc else cat.expense_account_id.id,
                    'name': f'أرباح التصرف — {asset.name}',
                    'debit': 0.0,
                    'credit': gl,
                }))
            else:
                acc = cat.loss_account_id
                lines.append((0, 0, {
                    'account_id': acc.id if acc else cat.expense_account_id.id,
                    'name': f'خسائر التصرف — {asset.name}',
                    'debit': abs(gl),
                    'credit': 0.0,
                }))

        move = self.env['account.move'].create({
            'ref': f'تصرف في أصل — {asset.asset_number} — {self.disposal_type}',
            'date': self.disposal_date,
            'journal_id': cat.journal_id.id,
            'line_ids': lines,
        })
        move.action_post()
        self.move_id = move
        self.state = 'posted'

        # إنهاء الأصل
        asset.write({
            'state': 'disposed',
            'disposal_date': self.disposal_date,
        })
        # إلغاء ربط العهدة
        if asset.custody_assignment_id:
            try:
                asset.custody_assignment_id.action_return()
            except Exception:
                pass

        asset.message_post(
            body=_(f'تم التصرف في الأصل: {self.disposal_type} — قيمة: {self.sale_value:,.2f} ج.م')
        )
        return True
