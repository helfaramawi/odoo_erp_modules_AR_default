# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PrintRegisterWizard(models.TransientModel):
    _name = 'port_said.cash_transfer.print.wizard'
    _description = 'ساحر طباعة دفتر حركة النقود'

    direction = fields.Selection([
        ('outgoing', 'نقود مرسلة'),
        ('incoming', 'نقود واردة'),
        ('both',     'الاتجاهان معاً'),
    ], string='الاتجاه', required=True, default='both')

    fiscal_year = fields.Char(string='السنة المالية', required=True,
        default=lambda s: s._default_fiscal_year())
    date_from = fields.Date(string='من تاريخ', required=True)
    date_to = fields.Date(string='إلى تاريخ', required=True)
    include_disputed = fields.Boolean(string='شمل المتنازَع فيها', default=True)
    include_lost = fields.Boolean(string='شمل المفقودة', default=True)

    @api.model
    def _default_fiscal_year(self):
        today = fields.Date.today()
        if today.month >= 7:
            return '%d/%d' % (today.year, today.year + 1)
        return '%d/%d' % (today.year - 1, today.year)

    def action_print(self):
        self.ensure_one()
        domain = [
            ('transfer_date', '>=', self.date_from),
            ('transfer_date', '<=', self.date_to),
            ('state', '!=', 'draft'),
        ]
        if self.direction != 'both':
            domain.append(('direction', '=', self.direction))
        # Exclude states if requested
        excluded_states = []
        if not self.include_disputed:
            excluded_states.append('disputed')
        if not self.include_lost:
            excluded_states.append('lost')
        if excluded_states:
            domain.append(('state', 'not in', excluded_states))

        transfers = self.env['port_said.cash_transfer'].search(
            domain, order='transfer_date, sequence_number')
        if not transfers:
            raise UserError(_('لا توجد تحويلات مطابقة.'))

        return self.env.ref(
            'port_said_cash_transfers.action_report_transfer_register'
        ).report_action(transfers)
