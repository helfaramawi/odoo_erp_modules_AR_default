# -*- coding: utf-8 -*-
"""
تعريف دفتر نقدية/بنكي (Cash Book Definition)
=============================================

سجل واحد لكل دفتر من دفاتر النقدية والبنك الواردة في استمارة 78:
- دفتر النقدية
- دفتر جاري البنك المركزي المصري
- دفتر حساب الوحدة الحسابية المركزية

المصدر: account.bank.statement.line (كشوف الحسابات البنكية / النقدية).
كل دفتر مربوط بـ account.journal واحد أو أكثر.
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CashBook(models.Model):
    _name = 'port_said.cash.book'
    _description = 'تعريف دفتر نقدية/بنكي حكومي'
    _order = 'sequence, code'
    _inherit = ['mail.thread']

    # ── المعرفات القانونية ────────────────────────────────────────────────────
    name = fields.Char(string='اسم الدفتر', required=True, translate=False)
    code = fields.Char(string='الكود الفني', required=True, index=True)
    form_number = fields.Char(string='رقم النموذج', required=True,
                              default='78 ع.ح')
    sequence = fields.Integer(string='ترتيب العرض', default=10)

    # ── نوع الدفتر ───────────────────────────────────────────────────────────
    book_type = fields.Selection([
        ('cash',          'نقدية (Cash)'),
        ('cbe',           'البنك المركزي المصري (CBE)'),
        ('cau',           'الوحدة الحسابية المركزية (CAU)'),
        ('other_bank',    'بنك آخر'),
    ], string='نوع الدفتر', required=True, default='cash', index=True)

    # ── ربط الدفتر باليومية أو بالحساب ────────────────────────────────────
    journal_ids = fields.Many2many(
        'account.journal', string='اليوميات المربوطة',
        required=True,
        domain="[('type', 'in', ['bank', 'cash'])]",
        help='اليوميات البنكية/النقدية المُكوِّنة لهذا الدفتر. '
             'الدفتر يقرأ من account.bank.statement.line على هذه اليوميات فقط.')

    bank_account_id = fields.Many2one(
        'res.partner.bank', string='الحساب البنكي الرسمي',
        help='معلومات إضافية: رقم الحساب البنكي للدفتر (إن وجد).')

    # ── معايير الطباعة ──────────────────────────────────────────────────────
    show_running_balance = fields.Boolean(
        string='عرض الرصيد الجاري', default=True)
    include_unreconciled = fields.Boolean(
        string='شمل غير المطابَق', default=True,
        help='إن عُطِّل: يقرأ فقط السطور المطابَقة (reconciled).')

    # ── التسلسل القانوني ────────────────────────────────────────────────────
    sequence_id = fields.Many2one('ir.sequence', string='التسلسل القانوني')

    # ── الحالة ──────────────────────────────────────────────────────────────
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    notes = fields.Text(string='ملاحظات قانونية')

    folio_count = fields.Integer(string='عدد الفوليوهات',
                                  compute='_compute_folio_count')

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code, company_id)',
         'كود الدفتر يجب أن يكون فريداً.'),
    ]

    def _compute_folio_count(self):
        Folio = self.env['port_said.cash.folio']
        for rec in self:
            rec.folio_count = Folio.search_count([('book_id', '=', rec.id)])

    def action_open_folios(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('فوليوهات: %s') % self.name,
            'res_model': 'port_said.cash.folio',
            'view_mode': 'list,form',
            'domain': [('book_id', '=', self.id)],
            'context': {'default_book_id': self.id},
        }

    def action_print_book(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('طباعة: %s') % self.name,
            'res_model': 'port_said.cash.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_book_id': self.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if not rec.sequence_id:
                rec.sequence_id = self.env['ir.sequence'].create({
                    'name': _('تسلسل %s') % rec.name,
                    'code': 'port_said.cash.book.%s' % rec.code.lower(),
                    'prefix': '78/%(year)s/',
                    'padding': 4,
                    'use_date_range': True,
                    'company_id': rec.company_id.id,
                }).id
                rec._create_fy_range_for_sequence()
        return recs

    def _create_fy_range_for_sequence(self):
        self.ensure_one()
        from datetime import date
        today = fields.Date.today()
        if today.month >= 7:
            fy_start = date(today.year, 7, 1)
            fy_end = date(today.year + 1, 6, 30)
        else:
            fy_start = date(today.year - 1, 7, 1)
            fy_end = date(today.year, 6, 30)
        self.env['ir.sequence.date_range'].create({
            'sequence_id': self.sequence_id.id,
            'date_from': fy_start,
            'date_to': fy_end,
            'number_next': 1,
        })

    def name_get(self):
        return [(r.id, '%s — %s' % (r.form_number, r.name)) for r in self]
