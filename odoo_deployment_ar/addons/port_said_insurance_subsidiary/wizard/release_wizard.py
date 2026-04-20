# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ReleaseWizard(models.TransientModel):
    _name = 'port_said.insurance.release.wizard'
    _description = 'ساحر الإفراج الجماعي'

    release_reason = fields.Text(string='سبب الإفراج', required=True,
        help='سبب قانوني/إداري يُسجَّل على كل سجل مُفرَج عنه.')
    release_date = fields.Date(string='تاريخ الإفراج',
        default=fields.Date.context_today, required=True)

    bank_guarantee_ids = fields.Many2many('port_said.bank.guarantee',
        string='خطابات الضمان')
    deposit_ids = fields.Many2many('port_said.insurance_deposit',
        string='الإيداعات')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        if active_model == 'port_said.bank.guarantee':
            res['bank_guarantee_ids'] = [(6, 0, active_ids)]
        elif active_model == 'port_said.insurance_deposit':
            res['deposit_ids'] = [(6, 0, active_ids)]
        return res

    def action_release_all(self):
        self.ensure_one()
        released_count = 0

        for g in self.bank_guarantee_ids:
            if g.state != 'active':
                continue
            g.release_reason = self.release_reason
            g.release_date = self.release_date
            g.action_release()
            released_count += 1

        for d in self.deposit_ids:
            if d.state != 'active':
                continue
            d.release_reason = self.release_reason
            d.action_release()
            released_count += 1

        if released_count == 0:
            raise UserError(_('لا توجد سجلات مؤهلة للإفراج (يجب أن تكون في حالة "مُودَع/ساري").'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم'),
                'message': _('أُفرِج عن %d تأمين.') % released_count,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
