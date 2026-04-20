from odoo import api, fields, models, _


class StockMove(models.Model):
    """Extend stock.move to auto-create custody assignment for durable items."""
    _inherit = 'stock.move'

    item_type = fields.Selection([
        ('durable', 'مستديم - Durable'),
        ('consumable', 'مستهلك - Consumable'),
    ], string='نوع الصنف', default='consumable',
       help='Durable items (مستديم) automatically create custody records')

    custody_type = fields.Selection([
        ('sub', 'عهدة فرعية - Sub-custody'),
        ('location', 'عهدة مكانية - Location-based'),
        ('personal', 'عهدة شخصية - Personal'),
    ], string='نوع العهدة')

    custody_employee_id = fields.Many2one(
        'hr.employee',
        string='الموظف المستلم (للعهدة)',
        help='Required when issuing durable items — will create custody record',
    )
    custody_assignment_id = fields.Many2one(
        'custody.assignment',
        string='سجل العهدة',
        readonly=True,
        copy=False,
    )

    def _action_done(self, cancel_backorder=False):
        result = super()._action_done(cancel_backorder=cancel_backorder)
        # Auto-create custody for دurable items on issue moves
        issue_moves = self.filtered(
            lambda m: m.item_type == 'durable'
            and m.custody_employee_id
            and not m.custody_assignment_id
            and m.picking_id
            and m.picking_id.picking_type_code == 'outgoing'
        )
        for move in issue_moves:
            move._create_custody_assignment()
        return result

    def _create_custody_assignment(self):
        self.ensure_one()
        if not self.custody_employee_id:
            return
        wh = self.picking_id.picking_type_id.warehouse_id
        custody = self.env['custody.assignment'].create({
            'employee_id': self.custody_employee_id.id,
            'national_id': self.custody_employee_id.ssnid or '',
            'product_id': self.product_id.id,
            'qty': self.quantity,
            'custody_type': self.custody_type or 'personal',
            'warehouse_id': wh.id if wh else False,
            'location_id': self.location_dest_id.id,
            'issue_date': fields.Date.context_today(self),
            'storekeeper_id': self.env.user.employee_id.id if self.env.user.employee_id else False,
            'dept_manager_id': self.custody_employee_id.parent_id.id if self.custody_employee_id.parent_id else False,
            'stock_move_id': self.id,
            'issue_permit_ref': self.picking_id.name,
        })
        custody.action_confirm()
        self.custody_assignment_id = custody
        return custody


class StockPicking(models.Model):
    """Add custody summary to picking."""
    _inherit = 'stock.picking'

    custody_count = fields.Integer(
        string='عدد العهد',
        compute='_compute_custody_count',
    )

    def _compute_custody_count(self):
        for picking in self:
            picking.custody_count = self.env['custody.assignment'].search_count(
                [('issue_permit_ref', '=', picking.name)]
            )

    def action_view_custody(self):
        return {
            'name': _('العهد المرتبطة'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.assignment',
            'view_mode': 'tree,form',
            'domain': [('issue_permit_ref', '=', self.name)],
        }
