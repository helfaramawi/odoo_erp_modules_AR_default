from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProcurementCommitteeMixin(models.AbstractModel):
    """
    Mixin: adds committee_id to any procurement document.
    Apply via _inherit = ['procurement.committee.mixin'] on RFQ, PO, Auction.
    FR-P7 (sovereign entities): has_committee = False, skip validation.
    """
    _name = 'procurement.committee.mixin'
    _description = 'مزيج تشكيل اللجنة - Committee Formation Mixin'

    committee_id = fields.Many2one(
        'procurement.committee',
        string='اللجنة المعينة',
        tracking=True,
        copy=False,
    )
    has_committee = fields.Boolean(
        string='يستلزم تشكيل لجنة',
        default=True,
        help='FR-P7 Sovereign entities are exempt from committee requirement',
    )
    committee_status = fields.Selection(
        related='committee_id.state',
        string='حالة اللجنة',
        store=True,
    )
    committee_chairman = fields.Many2one(
        related='committee_id.chairman_id',
        string='رئيس اللجنة',
        store=True,
    )

    def _validate_committee(self):
        """Call this before state transitions requiring a committee."""
        for rec in self:
            if rec.has_committee and not rec.committee_id:
                raise ValidationError(_(
                    'يجب تشكيل اللجنة قبل المتابعة.\n'
                    'Committee must be assigned before proceeding.\n'
                    'Document: %s'
                ) % rec.display_name)
            if rec.committee_id and rec.committee_id.state == 'draft':
                raise ValidationError(_(
                    'اللجنة في مرحلة المسودة. يجب تفعيل اللجنة أولاً.\n'
                    'Committee %s is still in Draft state.'
                ) % rec.committee_id.ref)

    def action_assign_committee(self):
        """Quick action to open committee selection dialog."""
        return {
            'name': _('تعيين لجنة'),
            'type': 'ir.actions.act_window',
            'res_model': 'procurement.committee',
            'view_mode': 'tree,form',
            'target': 'new',
            'domain': [('state', '=', 'active')],
        }
