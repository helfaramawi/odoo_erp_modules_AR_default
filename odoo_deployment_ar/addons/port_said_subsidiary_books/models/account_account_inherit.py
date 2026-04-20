# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    x_subsidiary_classification_id = fields.Many2one(
        'port_said.subsidiary.account.classification',
        string='تصنيف الدفاتر المساعدة',
        index=True,
        help='التصنيف الحكومي الذي ينتمي إليه هذا الحساب لأغراض الدفاتر المساعدة.')

    x_subsidiary_book_ids = fields.Many2many(
        'port_said.subsidiary.book',
        compute='_compute_subsidiary_books',
        string='يظهر في الدفاتر',
        help='الدفاتر القانونية التي يظهر فيها هذا الحساب.')

    def _compute_subsidiary_books(self):
        Book = self.env['port_said.subsidiary.book']
        for acc in self:
            if not acc.x_subsidiary_classification_id:
                acc.x_subsidiary_book_ids = False
                continue
            acc.x_subsidiary_book_ids = Book.search([
                ('account_classification_ids', 'in',
                 acc.x_subsidiary_classification_id.id)
            ])
