# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PrintRegisterWizard(models.TransientModel):
    _name = 'port_said.penalty.print.wizard'
    _description = 'ساحر طباعة دفتر الجزاءات'

    subject_type = fields.Selection([
        ('employee', 'موظفين'),
        ('vendor',   'موردين'),
        ('both',     'الكل'),
    ], string='النوع', required=True, default='both')

    fiscal_year = fields.Char(string='السنة المالية', required=True,
        default=lambda s: s._default_fiscal_year())
    date_from = fields.Date(string='من تاريخ', required=True)
    date_to = fields.Date(string='إلى تاريخ', required=True)

    only_executed = fields.Boolean(string='المُنفَّذ فقط', default=False)

    @api.model
    def _default_fiscal_year(self):
        today = fields.Date.today()
        if today.month >= 7:
            return '%d/%d' % (today.year, today.year + 1)
        return '%d/%d' % (today.year - 1, today.year)

    def action_print(self):
        self.ensure_one()
        domain = [
            ('incident_date', '>=', self.date_from),
            ('incident_date', '<=', self.date_to),
            ('state', '!=', 'draft'),
        ]
        if self.subject_type != 'both':
            domain.append(('subject_type', '=', self.subject_type))
        if self.only_executed:
            domain.append(('state', 'in', ['executed', 'upheld', 'closed']))

        penalties = self.env['port_said.penalty'].search(
            domain, order='incident_date, sequence_number')
        if not penalties:
            raise UserError(_('لا توجد جزاءات مطابقة في الفترة المحددة.'))

        return self.env.ref(
            'port_said_penalties.action_report_penalty_register'
        ).report_action(penalties)
