# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class Form50ReprintWizard(models.TransientModel):
    _name = 'form50.reprint.wizard'
    _description = 'معالج إعادة طباعة استمارة 50'

    daftar55_id = fields.Many2one('port_said.daftar55', required=True)
    reprint_reason = fields.Text(string='سبب إعادة الطباعة', required=True)

    def action_confirm_reprint(self):
        self.ensure_one()
        record = self.daftar55_id
        record.write({'reprint_reason': self.reprint_reason})
        return record.action_print_final()
