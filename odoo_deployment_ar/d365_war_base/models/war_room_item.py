from odoo import api, fields, models


class WarRoomItem(models.Model):
    _name = 'war.room.item'
    _description = 'War Room Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, due_date asc, id desc'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Char(default='New', copy=False, readonly=True)
    item_type = fields.Selection(
        [
            ('assumption', 'Assumption'),
            ('gap', 'Gap'),
            ('risk', 'Risk'),
            ('decision', 'Decision'),
            ('open_question', 'Open Question'),
        ],
        required=True,
        default='gap',
        tracking=True,
    )
    status = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('blocked', 'Blocked'), ('closed', 'Closed')],
        default='draft',
        tracking=True,
    )
    priority = fields.Selection(
        [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='medium',
        tracking=True,
    )
    description = fields.Text()
    due_date = fields.Date(tracking=True)
    owner_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user)
    related_requirement_id = fields.Char(string='Related Requirement ID', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('sequence', 'New') == 'New':
                vals['sequence'] = seq.next_by_code('war.room.item') or 'New'
        return super().create(vals_list)
