from odoo import models, fields, _
from odoo.exceptions import UserError


class Form50ReprintWizard(models.TransientModel):
    _name = 'form50.reprint.wizard'
    _description = 'معالج إعادة طباعة استمارة 50 ع.ح'

    daftar55_id = fields.Many2one('port_said.daftar55', required=True, ondelete='cascade')
    reason = fields.Text(string='سبب إعادة الطباعة', required=True)

    def action_confirm_reprint(self):
        self.ensure_one()
        if not self.reason or not self.reason.strip():
            raise UserError(_('يجب إدخال سبب إعادة الطباعة.'))
        self.daftar55_id.write({'reprint_reason': self.reason.strip()})
        return self.daftar55_id.action_print_final()
