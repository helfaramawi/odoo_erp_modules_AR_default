# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CashPrintWizard(models.TransientModel):
    _name = 'port_said.cash.print.wizard'
    _description = 'ساحر طباعة دفاتر النقدية والبنك'

    book_id = fields.Many2one('port_said.cash.book',
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
    only_closed = fields.Boolean(string='المُقفَلة فقط', default=True)

    @api.model
    def _default_fiscal_year(self):
        today = fields.Date.today()
        if today.month >= 7:
            return '%d/%d' % (today.year, today.year + 1)
        return '%d/%d' % (today.year - 1, today.year)

    def action_print(self):
        self.ensure_one()
        Folio = self.env['port_said.cash.folio']
        domain = [
            ('book_id', '=', self.book_id.id),
            ('fiscal_year', '=', self.fiscal_year),
        ]
        if self.period_month != 'all':
            domain.append(('period_month', '=', self.period_month))
        if self.only_closed:
            domain.append(('state', 'in', ['closed', 'audited', 'archived']))

        folios = Folio.search(domain, order='period_month')
        if not folios:
            raise UserError(_('لا توجد فوليوهات مطابقة.'))

        return self.env.ref(
            'port_said_cash_books.action_report_cash_register'
        ).report_action(folios)
