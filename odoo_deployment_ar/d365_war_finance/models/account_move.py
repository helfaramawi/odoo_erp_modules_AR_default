from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('amount_total', 'move_type', 'state', 'company_id')
    def _check_war_finance_threshold(self):
        for move in self:
            if move.state != 'posted' or move.move_type != 'entry':
                continue
            control = self.env['war.finance.control'].search([
                ('company_id', '=', move.company_id.id),
                ('active', '=', True),
            ], limit=1)
            if control and move.amount_total > control.journal_threshold:
                raise ValidationError(
                    _(
                        'Posted journal amount %(amount)s exceeds control threshold %(threshold)s for company %(company)s.',
                        amount=move.amount_total,
                        threshold=control.journal_threshold,
                        company=move.company_id.display_name,
                    )
                )
