# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Form50ReprintWizard(models.TransientModel):
    """معالج إعادة طباعة استمارة 50 — يُلزم بإدخال السبب."""
    _name = 'form50.reprint.wizard'
    _description = 'معالج إعادة طباعة استمارة 50 ع.ح'

    daftar55_id = fields.Many2one(
        'port_said.daftar55',
        string='سجل دفتر 55',
        required=True,
        readonly=True,
    )
    sequence_number = fields.Char(
        related='daftar55_id.sequence_number',
        string='رقم الاستمارة',
        readonly=True,
    )
    final_print_count = fields.Integer(
        related='daftar55_id.final_print_count',
        string='طُبعت سابقاً',
        readonly=True,
    )
    reprint_reason = fields.Text(
        string='سبب إعادة الطباعة',
        required=True,
        help='اذكر السبب الكامل لإعادة الطباعة — يُسجَّل في سجل الأنشطة',
    )

    def action_confirm_reprint(self):
        self.ensure_one()
        if not self.reprint_reason or len(self.reprint_reason.strip()) < 10:
            raise UserError(_('يجب إدخال سبب واضح لإعادة الطباعة (10 أحرف على الأقل).'))

        rec = self.daftar55_id
        rec.write({
            'reprint_reason': self.reprint_reason,
        })
        return rec.action_print_final()
