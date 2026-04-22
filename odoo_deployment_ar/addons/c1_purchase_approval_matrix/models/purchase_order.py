from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_t1', 'Pending T1'),
        ('pending_t2', 'Pending T2'),
        ('pending_t3', 'Pending T3'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', copy=False, tracking=True)

    current_approver_ids = fields.Many2many(
        'res.users', 'po_current_approver_rel', 'order_id', 'user_id',
        string='Pending Approvers', copy=False)
    approval_log_ids = fields.One2many('purchase.approval.log', 'purchase_id', readonly=True)
    rejection_comment = fields.Text(copy=False, tracking=True)
    requires_approval = fields.Boolean(compute='_compute_requires_approval', store=True)

    @api.depends('amount_total', 'company_id')
    def _compute_requires_approval(self):
        Threshold = self.env['purchase.approval.threshold']
        for po in self:
            po.requires_approval = bool(
                Threshold.get_approvers_for_amount(po.amount_total, po.company_id.id))

    def button_confirm(self):
        for po in self:
            if po.state not in ('draft', 'sent'):
                continue
            if po.requires_approval and po.approval_state not in ('approved',):
                po._submit_for_approval()
                return
        return super().button_confirm()

    def _submit_for_approval(self):
        self.ensure_one()
        Threshold = self.env['purchase.approval.threshold']
        thresholds = Threshold.get_approvers_for_amount(
            self.amount_total, self.company_id.id).sorted('tier')
        if not thresholds:
            return super().button_confirm()
        first = thresholds[0]
        self.write({
            'approval_state': 'pending_t%s' % first.tier,
            'current_approver_ids': [(6, 0, first.approver_ids.ids)],
        })
        self._log_approval('submitted', first.tier)

    def action_approve(self):
        self.ensure_one()
        if self.env.user not in self.current_approver_ids:
            raise UserError(_('Not authorised to approve.'))
        current_tier = self.approval_state.replace('pending_t', '')
        Threshold = self.env['purchase.approval.threshold']
        all_t = Threshold.get_approvers_for_amount(
            self.amount_total, self.company_id.id).sorted('tier')
        next_t = all_t.filtered(lambda t: int(t.tier) > int(current_tier))
        self._log_approval('approved', current_tier)
        if next_t:
            nxt = next_t[0]
            self.write({
                'approval_state': 'pending_t%s' % nxt.tier,
                'current_approver_ids': [(6, 0, nxt.approver_ids.ids)],
            })
        else:
            self.write({'approval_state': 'approved', 'current_approver_ids': [(5,)]})
            super(PurchaseOrder, self).button_confirm()

    def action_reject(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Purchase Order'),
            'res_model': 'purchase.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_purchase_id': self.id},
        }

    def action_reset_to_draft(self):
        self._log_approval('reset', '')
        self.write({'approval_state': 'draft', 'current_approver_ids': [(5,)]})

    def _log_approval(self, action, tier):
        self.env['purchase.approval.log'].create({
            'purchase_id': self.id,
            'tier': str(tier),
            'action': action,
            'user_id': self.env.user.id,
        })
