from odoo import fields, models


class WorkflowReviewWizard(models.TransientModel):
    _name = 'workflow.review.wizard'
    _description = 'Workflow Review Wizard'

    review_notes = fields.Text(string='Review Notes')
    reviewer = fields.Char(string='Reviewer')
    review_date = fields.Datetime(string='Review Date', default=fields.Datetime.now)
