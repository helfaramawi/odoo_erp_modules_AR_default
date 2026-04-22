# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SubsidiaryPrintWizard(models.TransientModel):
    _name = 'port_said.subsidiary.print.wizard'
    _description = 'ساحر طباعة الدفاتر المساعدة'

    book_id = fields.Many2one('port_said.subsidiary.book',
                               string='الدفتر', required=True)

    fiscal_year = fields.Char(string='السنة المالية', required=True,
                               default=lambda s: s._default_fiscal_year())
    period_month = fields.Selection([
        ('all', 'كل أشهر السنة'),
        ('07', 'يوليو'), ('08', 'أغسطس'), ('09', 'سبتمبر'),
        ('10', 'أكتوبر'), ('11', 'نوفمبر'), ('12', 'ديسمبر'),
        ('01', 'يناير'), ('02', 'فبراير'), ('03', 'مارس'),
        ('04', 'أبريل'), ('05', 'مايو'), ('06', 'يونيو'),
    ], string='الشهر', default='all', required=True)

    partner_ids = fields.Many2many('res.partner', string='شركاء (اختياري)')
    account_ids = fields.Many2many('account.account', string='حسابات (اختياري)')

    include_zero_balance = fields.Boolean(string='شمل الفوليوهات صفرية الرصيد',
                                            default=False)
    only_closed = fields.Boolean(string='المُقفَلة فقط',
                                  default=True,
                                  help='التقارير الرسمية تُطبع فقط من الفوليوهات المُقفَلة.')

    @api.model
    def _default_fiscal_year(self):
        today = fields.Date.today()
        if today.month >= 7:
            return '%d/%d' % (today.year, today.year + 1)
        return '%d/%d' % (today.year - 1, today.year)

    def action_print(self):
        self.ensure_one()
        Folio = self.env['port_said.subsidiary.folio']
        domain = [
            ('book_id', '=', self.book_id.id),
            ('fiscal_year', '=', self.fiscal_year),
        ]
        if self.period_month != 'all':
            domain.append(('period_month', '=', self.period_month))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))
        if self.only_closed:
            domain.append(('state', 'in', ['closed', 'audited', 'archived']))
        if not self.include_zero_balance:
            domain += ['|', '|',
                       ('opening_balance', '!=', 0),
                       ('period_debit', '!=', 0),
                       ('period_credit', '!=', 0)]

        folios = Folio.search(domain)
        if not folios:
            raise UserError(_(
                'لا توجد فوليوهات مطابقة لمعايير البحث. '
                'تحقق من الفلاتر أو من توليد الفوليوهات الشهرية.'))

        # اختر القالب حسب نوع الدفتر
        report_action_xmlid = {
            'detail':   'port_said_subsidiary_books.action_report_subsidiary_detail',
            'totals':   'port_said_subsidiary_books.action_report_subsidiary_totals',
            'personal': 'port_said_subsidiary_books.action_report_personal_dual',
        }[self.book_id.print_template]

        return self.env.ref(report_action_xmlid).report_action(folios)
