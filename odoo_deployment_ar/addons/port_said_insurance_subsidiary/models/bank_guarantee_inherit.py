# -*- coding: utf-8 -*-
"""
تمديد خطاب الضمان البنكي
==========================
يضيف للنموذج port_said.bank.guarantee الأساسي:
1. الترقيم القانوني لدفتر 78 (form78_sequence)
2. توليد القيود المحاسبية تلقائياً عند activate / release / forfeit
3. ربط بحساب تحت الحفظ (holding account) لربط الضمان بالمقاول
4. ربط بفولية الدفتر القانوني (insurance_folio_id)
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BankGuaranteeInherit(models.Model):
    _inherit = 'port_said.bank.guarantee'

    # ── الترقيم القانوني لدفتر 78 ──────────────────────────────────────────
    form78_sequence = fields.Char(string='تسلسل دفتر 78',
        readonly=True, copy=False, index=True,
        help='رقم مسلسل قانوني داخل دفتر التأمينات 78 ع.ح. '
             'يُولَّد بعد نجاح التفعيل الأول فقط.')

    # ── تصنيف دفتر 78 (مؤقت/نهائي) ─────────────────────────────────────────
    book_classification = fields.Selection([
        ('provisional', 'تأمين مؤقت (دفتر 19)'),
        ('final',       'تأمين نهائي (دفتر 20)'),
    ], string='تصنيف الدفتر', compute='_compute_book_classification',
       store=True, index=True,
       help='يُحدَّد تلقائياً من guarantee_type.')

    # ── السنة المالية ────────────────────────────────────────────────────────
    fiscal_year = fields.Char(string='السنة المالية', readonly=True, copy=False)

    # ── ربط القيود المحاسبية ───────────────────────────────────────────────
    activation_move_id = fields.Many2one('account.move',
        string='قيد التفعيل', readonly=True,
        help='قيد إثبات الضمان في الحسابات النظامية عند التفعيل.')
    release_move_id = fields.Many2one('account.move',
        string='قيد الإفراج', readonly=True)
    forfeiture_move_id = fields.Many2one('account.move',
        string='قيد المصادرة', readonly=True)

    # ── ربط بالفولية ───────────────────────────────────────────────────────
    insurance_folio_id = fields.Many2one('port_said.insurance.folio',
        string='الفولية المرتبطة', readonly=True, index=True)

    # ── Computed ─────────────────────────────────────────────────────────────
    @api.depends('guarantee_type')
    def _compute_book_classification(self):
        """يُسند التصنيف القانوني حسب نوع الضمان."""
        # Preliminary, Advance, Maintenance → تأمين مؤقت
        # Final, Performance → تأمين نهائي
        for rec in self:
            if rec.guarantee_type in ('final', 'performance'):
                rec.book_classification = 'final'
            else:
                rec.book_classification = 'provisional'

    # ── Override action_activate: توليد القيد + التسلسل ─────────────────────
    def action_activate(self):
        """يُفعِّل الضمان، يُولِّد القيد النظامي، ويرقِّمه في دفتر 78."""
        Seq = self.env['ir.sequence']
        Move = self.env['account.move']

        # نفِّذ super أولاً — إن فشل لا نُكوِّن قيداً أو تسلسلاً
        result = super().action_activate()

        for rec in self:
            # Set fiscal year
            if rec.issue_date and not rec.fiscal_year:
                m, y = rec.issue_date.month, rec.issue_date.year
                if m >= 7:
                    rec.fiscal_year = '%d/%d' % (y, y + 1)
                else:
                    rec.fiscal_year = '%d/%d' % (y - 1, y)

            # Generate legal sequence
            if not rec.form78_sequence:
                seq_code = ('port_said.insurance.final' if rec.book_classification == 'final'
                           else 'port_said.insurance.provisional')
                rec.form78_sequence = Seq.next_by_code(seq_code) or '/'

            # Generate accounting move (memo accounts)
            if not rec.activation_move_id:
                rec._create_activation_move()
                # Create a movement record in the folio system
                rec._create_folio_movement('deposit')
        return result

    def _create_activation_move(self):
        """ينشئ قيداً في الحسابات النظامية لإثبات الضمان."""
        self.ensure_one()
        company = self.company_id or self.env.company
        dr_account = company.guarantee_memo_dr_account_id
        cr_account = company.guarantee_memo_cr_account_id

        if not dr_account or not cr_account:
            # لا تفشل — فقط سجل تحذيراً (الإعدادات لم تُعبَّأ بعد)
            self.message_post(body=_(
                '⚠ لم يُنشأ قيد التفعيل لعدم تعيين الحسابات النظامية في إعدادات الشركة. '
                'يمكن إنشاؤه يدوياً لاحقاً عبر Settings → Insurance Accounts.'
            ))
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
            'date': self.issue_date or fields.Date.today(),
            'ref': _('تفعيل تأمين %s — %s') % (
                self.form78_sequence, self.vendor_id.name or ''),
            'line_ids': [
                (0, 0, {
                    'account_id': dr_account.id,
                    'partner_id': self.vendor_id.id if self.vendor_id else False,
                    'name': _('إثبات خطاب ضمان %s') % self.name,
                    'debit': self.amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': cr_account.id,
                    'partner_id': self.vendor_id.id if self.vendor_id else False,
                    'name': _('التزام مقابل خطاب ضمان %s') % self.name,
                    'debit': 0.0,
                    'credit': self.amount,
                }),
            ],
        })
        self.activation_move_id = move.id

    def _create_folio_movement(self, movement_type):
        """يضيف حركة إيداع/استرداد في سجل الحركات."""
        self.ensure_one()
        self.env['port_said.insurance.movement'].create({
            'movement_type': movement_type,
            'movement_date': fields.Date.today(),
            'partner_id': self.vendor_id.id if self.vendor_id else False,
            'collateral_type': 'guarantee',
            'bank_guarantee_id': self.id,
            'amount': self.amount,
            'description': _('%s خطاب ضمان %s') % (
                _('إيداع') if movement_type == 'deposit' else _('استرداد'),
                self.name),
        })

    # ── Override action_release: توليد القيد العكسي ─────────────────────────
    def action_release(self):
        # نفِّذ super أولاً
        result = super().action_release()
        Move = self.env['account.move']
        for rec in self:
            if not rec.release_move_id and rec.activation_move_id:
                # عكس القيد النظامي
                reverse = rec.activation_move_id._reverse_moves(
                    default_values_list=[{
                        'date': rec.release_date or fields.Date.today(),
                        'ref': _('إفراج عن تأمين %s') % rec.form78_sequence,
                    }],
                    cancel=True,
                )
                rec.release_move_id = reverse.id if reverse else False
                rec._create_folio_movement('withdrawal')
        return result

    # ── Override action_forfeit: قيد التحويل إلى الإيرادات ─────────────────
    def action_forfeit(self):
        result = super().action_forfeit()
        for rec in self:
            if not rec.forfeiture_move_id:
                rec._create_forfeiture_move()
                rec._create_folio_movement('forfeiture')
        return result

    def _create_forfeiture_move(self):
        """ينشئ قيد تحويل التأمين المُصادَر إلى إيرادات."""
        self.ensure_one()
        company = self.company_id or self.env.company
        dr_account = company.guarantee_memo_cr_account_id  # عكس المدين الأصلي
        cr_account = company.insurance_forfeiture_revenue_account_id

        if not dr_account or not cr_account:
            self.message_post(body=_(
                '⚠ لم يُنشأ قيد المصادرة لعدم تعيين حساب إيرادات المصادرة.'
            ))
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
            'ref': _('مصادرة تأمين %s') % self.form78_sequence,
            'line_ids': [
                (0, 0, {
                    'account_id': dr_account.id,
                    'partner_id': self.vendor_id.id if self.vendor_id else False,
                    'name': _('مصادرة خطاب ضمان %s') % self.name,
                    'debit': self.amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': cr_account.id,
                    'name': _('إيرادات مصادرة تأمين %s') % self.name,
                    'debit': 0.0,
                    'credit': self.amount,
                }),
            ],
        })
        self.forfeiture_move_id = move.id
