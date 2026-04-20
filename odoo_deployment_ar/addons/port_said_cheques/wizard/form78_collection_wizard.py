# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Form78CollectionWizard(models.TransientModel):
    _name = 'port_said.cheque.form78.collection.wizard'
    _description = 'ساحر طباعة دفتر 78 - شيكات رسم التحصيل'

    fiscal_year = fields.Char(string='السنة المالية', required=True,
        default=lambda s: s._default_fiscal_year())
    period_from = fields.Date(string='من تاريخ', required=True)
    period_to = fields.Date(string='إلى تاريخ', required=True)
    state_filter = fields.Selection([
        ('all',       'كل الشيكات'),
        ('pending',   'المُعلَّقة (مودَعة ولم تُحصَّل)'),
        ('cleared',   'المُحصَّلة'),
        ('returned',  'المرتدة'),
    ], string='الحالة', default='all', required=True)

    @api.model
    def _default_fiscal_year(self):
        today = fields.Date.today()
        if today.month >= 7:
            return '%d/%d' % (today.year, today.year + 1)
        return '%d/%d' % (today.year - 1, today.year)

    def action_print(self):
        self.ensure_one()
        Cheque = self.env['port_said.cheque']
        domain = [
            ('cheque_category', '=', 'for_collection'),
            ('direction', '=', 'incoming'),
            ('issue_date', '>=', self.period_from),
            ('issue_date', '<=', self.period_to),
        ]
        if self.state_filter == 'pending':
            domain.append(('state', '=', 'deposited'))
        elif self.state_filter == 'cleared':
            domain.append(('state', '=', 'cleared'))
        elif self.state_filter == 'returned':
            domain.append(('state', '=', 'returned'))

        records = Cheque.search(domain, order='issue_date, cheque_number')
        if not records:
            raise UserError(_('لا توجد شيكات رسم تحصيل مطابقة.'))
        return self.env.ref(
            'port_said_cheques.action_report_form78_collection'
        ).report_action(records)
