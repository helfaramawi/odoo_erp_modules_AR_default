from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = "account.payment"

    early_pay_discount = fields.Monetary(
        string="Early Pay Discount / خصم الدفع المبكر",
        currency_field="currency_id",
        help="Amount to post as early payment discount journal line / مبلغ للترحيل كخصم دفع مبكر",
    )
    discount_account_id = fields.Many2one(
        "account.account",
        string="Discount Account / حساب الخصم",
        domain="[('account_type','in',['expense','income'])]",
    )
    override_matching = fields.Boolean(
        string="Manual Matching Override / تجاوز المطابقة اليدوية",
        help="Allow manual reconciliation override / السماح بتجاوز التسوية اليدوية",
    )

    def action_post(self):
        res = super().action_post()
        for payment in self:
            if payment.early_pay_discount and payment.discount_account_id:
                payment._post_discount_line()
        return res

    def _post_discount_line(self):
        self.ensure_one()
        journal = self.journal_id
        discount = self.early_pay_discount
        account = self.discount_account_id
        move_vals = {
            "journal_id": journal.id,
            "date": self.date,
            "ref": _("Early Pay Discount — %s / خصم دفع مبكر") % self.name,
            "line_ids": [
                (0, 0, {
                    "account_id": account.id,
                    "debit": discount,
                    "credit": 0,
                    "name": _("Early payment discount / خصم الدفع المبكر"),
                    "partner_id": self.partner_id.id,
                }),
                (0, 0, {
                    "account_id": self.partner_id.property_account_payable_id.id,
                    "debit": 0,
                    "credit": discount,
                    "name": _("Early payment discount offset / مقابل خصم الدفع المبكر"),
                    "partner_id": self.partner_id.id,
                }),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        move.action_post()
        self.message_post(body=_(
            "Early pay discount journal entry posted: %s / تم ترحيل قيد خصم الدفع المبكر") % move.name)
