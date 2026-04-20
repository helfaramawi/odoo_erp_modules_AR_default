# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class GenerateFolioWizard(models.TransientModel):
    _name = 'port_said.insurance.generate.folio.wizard'
    _description = 'ساحر توليد فولية تأمينات'

    book_classification = fields.Selection([
        ('provisional', 'تأمين مؤقت (دفتر 19)'),
        ('final',       'تأمين نهائي (دفتر 20)'),
        ('both',        'كلاهما'),
    ], string='الدفتر', required=True, default='both')

    fiscal_year = fields.Char(string='السنة المالية', required=True,
        default=lambda s: s._default_fiscal_year())
    period_month = fields.Selection([
        ('07', 'يوليو'), ('08', 'أغسطس'), ('09', 'سبتمبر'),
        ('10', 'أكتوبر'), ('11', 'نوفمبر'), ('12', 'ديسمبر'),
        ('01', 'يناير'), ('02', 'فبراير'), ('03', 'مارس'),
        ('04', 'أبريل'), ('05', 'مايو'), ('06', 'يونيو'),
    ], string='الشهر', required=True)

    @api.model
    def _default_fiscal_year(self):
        today = fields.Date.today()
        if today.month >= 7:
            return '%d/%d' % (today.year, today.year + 1)
        return '%d/%d' % (today.year - 1, today.year)

    def action_generate(self):
        self.ensure_one()
        Folio = self.env['port_said.insurance.folio']

        # حسِّب date_from / date_to من الشهر
        month = int(self.period_month)
        # أول سنة من السلسلة YYYY/YYYY+1
        start_year = int(self.fiscal_year.split('/')[0])
        # الأشهر 07-12 تقع في السنة الأولى، 01-06 في الثانية
        year = start_year if month >= 7 else start_year + 1

        date_from = date(year, month, 1)
        from calendar import monthrange
        _last, last = monthrange(year, month)
        date_to = date(year, month, last)

        classifications = ['provisional', 'final'] if self.book_classification == 'both' \
            else [self.book_classification]

        created = []
        for cls in classifications:
            exists = Folio.search([
                ('book_classification', '=', cls),
                ('fiscal_year', '=', self.fiscal_year),
                ('period_month', '=', self.period_month),
            ], limit=1)
            if exists:
                continue
            folio = Folio.create({
                'book_classification': cls,
                'fiscal_year': self.fiscal_year,
                'period_month': self.period_month,
                'date_from': date_from,
                'date_to': date_to,
            })
            created.append(folio.id)

        if not created:
            raise UserError(_('الفولية/الفوليوهات موجودة بالفعل لهذه الفترة.'))

        return {
            'type': 'ir.actions.act_window',
            'name': _('الفوليوهات المُولَّدة'),
            'res_model': 'port_said.insurance.folio',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created)],
        }
