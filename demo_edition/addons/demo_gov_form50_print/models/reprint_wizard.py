# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Form50ReprintWizard(models.TransientModel):
    _name = 'form50.reprint.wizard'
    _description = 'سبب إعادة طباعة استمارة 50'

    daftar55_id = fields.Many2one('demo_gov.daftar55', required=True)
    reason      = fields.Text(string='سبب إعادة الطباعة', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.daftar55_id.write({'reprint_reason': self.reason})
        return self.daftar55_id.action_print_final()
