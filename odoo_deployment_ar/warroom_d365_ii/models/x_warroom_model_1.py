from odoo import api, fields, models

class X_warroom_model_1(models.Model):
    _name = 'x_warroom_model_1'
    _description = 'X_warroom_model_1'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    state = fields.Selection([('draft', 'Draft'), ('under_review', 'Under Review'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected'), ('pending_validation', 'Pending Validation'), ('approved_for_build', 'Approved For Build')], default='draft', tracking=True)
    name = fields.Char(string='Name', required=True)
    x_source_ref = fields.Char(string='X Source Ref')
    x_validation_status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='X Validation Status', required=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='State')

    @api.constrains('name')
    def _check_name_placeholder(self):
        # TODO: refine constraints from validated business rules.
        return True

    def action_set_under_review(self):
        for rec in self:
            rec.state = 'under_review'
        return True
    def action_set_confirmed(self):
        for rec in self:
            rec.state = 'confirmed'
        return True
    def action_set_rejected(self):
        for rec in self:
            rec.state = 'rejected'
        return True
    def action_set_pending_validation(self):
        for rec in self:
            rec.state = 'pending_validation'
        return True
    def action_set_approved_for_build(self):
        for rec in self:
            rec.state = 'approved_for_build'
        return True

# Traceability: req=KY process=KY confidence=0.87 status=pending
