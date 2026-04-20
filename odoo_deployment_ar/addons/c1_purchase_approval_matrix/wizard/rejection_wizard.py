from odoo import models, fields, _
from odoo.exceptions import UserError

class PurchaseRejectionWizard(models.TransientModel):
    _name = 'purchase.rejection.wizard'
    _description = 'Purchase Order Rejection'

    purchase_id = fields.Many2one('purchase.order', required=True, readonly=True)
    rejection_comment = fields.Text(required=True)

    def action_confirm_rejection(self):
        self.ensure_one()
        po = self.purchase_id
        if self.env.user not in po.current_approver_ids:
            raise UserError(_('Not authorised to reject.'))
        tier = po.approval_state.replace('pending_t', '')
        po._log_approval('rejected', tier)
        po.write({
            'approval_state': 'rejected',
            'current_approver_ids': [(5,)],
            'rejection_comment': self.rejection_comment,
        })
        return {'type': 'ir.actions.act_window_close'}
