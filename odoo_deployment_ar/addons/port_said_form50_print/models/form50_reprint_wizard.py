# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class Form50ReprintWizard(models.TransientModel):
    _name = 'form50.reprint.wizard'
    _description = 'معالج إعادة طباعة استمارة 50 ع.ح'

    daftar55_id = fields.Many2one('port_said.daftar55', required=True, readonly=True)
    reason      = fields.Text(string='سبب إعادة الطباعة', required=True)

    def action_confirm_reprint(self):
        rec = self.daftar55_id
        if not self.env.user.has_group('account.group_account_manager'):
            raise UserError(_('إعادة الطباعة للمدير المالي فقط.'))
        rec.write({'reprint_reason': self.reason})
        return rec.action_print_final()
