# -*- coding: utf-8 -*-
"""
دفتر إيرادات/مصروفات (Revenue/Expense Book Definition)
========================================================

سجل واحد لكل دفتر قانوني من دفاتر الإيرادات والمصروفات الحكومية.
يحدد:
- الجهة (إيرادات / مصروفات / كلاهما)
- المستوى (باب / فصل / بند الكامل)
- نطاق الأبواب (مثلاً 1-6 للاستخدامات، 7-9 للموارد)
- قالب الطباعة (نموذج 10 cross-tab أو نموذج 81 لقائم)
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RevenueBook(models.Model):
    _name = 'port_said.revenue.book'
    _description = 'تعريف دفتر إيرادات/مصروفات حكومي'
    _order = 'sequence, code'
    _inherit = ['mail.thread']

    # ── المعرفات القانونية ────────────────────────────────────────────────────
    name = fields.Char(string='اسم الدفتر', required=True, translate=False)
    code = fields.Char(string='الكود الفني', required=True, index=True)
    form_number = fields.Char(string='رقم النموذج', required=True,
                              help='10 حسابات / 81 ع.ح وما إلى ذلك')
    sequence = fields.Integer(string='ترتيب العرض', default=10)

    # ── أبعاد التصنيف ────────────────────────────────────────────────────────
    direction = fields.Selection([
        ('revenues',    'إيرادات (Resources)'),
        ('expenses',    'مصروفات (Uses)'),
        ('both',        'كلاهما (إيرادات + مصروفات)'),
        ('settlements', 'تسويات'),
    ], string='الاتجاه', required=True, index=True)

    grouping_level = fields.Selection([
        ('bab',       'مستوى الباب (رقم واحد)'),
        ('fasle',     'مستوى الفصل (4 أرقام)'),
        ('full_code', 'مستوى البند الكامل (8 أرقام)'),
    ], string='مستوى التجميع', required=True, default='full_code')

    # ── نطاق الأبواب (Babs included) ────────────────────────────────────────
    bab_range_from = fields.Char(string='من باب', size=1, default='1',
        help='الباب الأول المشمول (1-9). مثال: 1 للاستخدامات.')
    bab_range_to = fields.Char(string='إلى باب', size=1, default='9',
        help='الباب الأخير المشمول. مثال: 6 للاستخدامات، 9 للموارد.')

    # ── قواعد الفلترة ───────────────────────────────────────────────────────
    journal_ids = fields.Many2many(
        'account.journal', string='اليوميات المؤهلة',
        help='اختياري: قصر القراءة على يوميات بعينها (مثلاً يومية الإيرادات فقط)')

    include_unposted = fields.Boolean(
        string='شمل غير المرحَّل', default=False)

    # ── قالب الطباعة ────────────────────────────────────────────────────────
    print_template = fields.Selection([
        ('form10', 'نموذج 10 — Cross-tab يومي × بنود'),
        ('form81', 'نموذج 81 — قائم بالأبواب والفصول'),
    ], string='قالب الطباعة', required=True, default='form10')

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

    @api.constrains('bab_range_from', 'bab_range_to')
    def _check_bab_range(self):
        for rec in self:
            if rec.bab_range_from and rec.bab_range_to:
                try:
                    f = int(rec.bab_range_from)
                    t = int(rec.bab_range_to)
                    if not (1 <= f <= 9 and 1 <= t <= 9 and f <= t):
                        raise ValidationError(_(
                            'نطاق الباب يجب أن يكون بين 1 و 9 و from <= to.'))
                except ValueError:
                    raise ValidationError(_('الباب يجب أن يكون رقماً (1-9).'))

    def _compute_folio_count(self):
        Folio = self.env['port_said.revenue.folio']
        for rec in self:
            rec.folio_count = Folio.search_count([('book_id', '=', rec.id)])

    def action_open_folios(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('فوليوهات: %s') % self.name,
            'res_model': 'port_said.revenue.folio',
            'view_mode': 'list,form',
            'domain': [('book_id', '=', self.id)],
            'context': {'default_book_id': self.id},
        }

    def action_print_book(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('طباعة: %s') % self.name,
            'res_model': 'port_said.revenue.print.wizard',
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
                    'code': 'port_said.revenue.book.%s' % rec.code.lower(),
                    'prefix': '%s/%%(year)s/' % rec.form_number.split()[0],
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
        return [(rec.id, '%s — %s' % (rec.form_number, rec.name)) for rec in self]
