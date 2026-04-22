# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Form56PrintWizard(models.TransientModel):
    _name = 'port_said.cheque.form56.print.wizard'
    _description = 'ساحر طباعة دفتر 56'

    register_type = fields.Selection([
        ('cheques',    'دفتر حساب الشيكات (صادرة)'),
        ('outgoing_po','دفتر حساب أوامر الدفع المرسلة'),
    ], string='نوع السجل', required=True, default='cheques')

    fiscal_year = fields.Char(string='السنة المالية', required=True,
        default=lambda s: s._default_fiscal_year())
    period_from = fields.Date(string='من تاريخ', required=True)
    period_to = fields.Date(string='إلى تاريخ', required=True)

    cheque_book_id = fields.Many2one('port_said.cheque.book',
        string='دفتر شيكات ورقي (اختياري)',
        help='فلترة على دفتر ورقي معين فقط.')

    only_issued = fields.Boolean(string='الصادرة فعلياً فقط', default=True,
        help='استبعاد المسودات والملغيات.')

    @api.model
    def _default_fiscal_year(self):
        today = fields.Date.today()
        if today.month >= 7:
            return '%d/%d' % (today.year, today.year + 1)
        return '%d/%d' % (today.year - 1, today.year)

    def action_print(self):
        self.ensure_one()
        if self.register_type == 'cheques':
            Cheque = self.env['port_said.cheque']
            domain = [
                ('direction', '=', 'outgoing'),
                ('issue_date', '>=', self.period_from),
                ('issue_date', '<=', self.period_to),
            ]
            if self.cheque_book_id:
                domain.append(('cheque_book_id', '=', self.cheque_book_id.id))
            if self.only_issued:
                domain.append(('state', 'not in', ['draft', 'cancelled']))
            records = Cheque.search(domain, order='issue_date, cheque_number')
            if not records:
                raise UserError(_('لا توجد شيكات مطابقة.'))
            return self.env.ref(
                'port_said_cheques.action_report_form56_cheques'
            ).report_action(records)
        else:
            PO = self.env['port_said.outgoing_po']
            domain = [
                ('issue_date', '>=', self.period_from),
                ('issue_date', '<=', self.period_to),
            ]
            if self.only_issued:
                domain.append(('state', 'not in', ['draft', 'cancelled']))
            records = PO.search(domain, order='issue_date, sequence_number')
            if not records:
                raise UserError(_('لا توجد أوامر دفع مطابقة.'))
            return self.env.ref(
                'port_said_cheques.action_report_form56_outgoing_po'
            ).report_action(records)
