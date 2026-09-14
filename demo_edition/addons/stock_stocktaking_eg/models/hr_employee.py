from odoo import api, fields, models, _


class HrEmployeeStocktaking(models.Model):
    """Extend hr.employee — show stocktaking sessions they chaired or managed."""
    _inherit = 'hr.employee'

    stocktaking_count = fields.Integer(
        string='جلسات الجرد',
        compute='_compute_stocktaking_count',
    )

    def _compute_stocktaking_count(self):
        for emp in self:
            emp.stocktaking_count = self.env['stock.stocktaking.session'].search_count([
                '|',
                ('committee_chairman_id', '=', emp.id),
                ('storekeeper_id', '=', emp.id),
            ])

    def action_view_stocktaking(self):
        self.ensure_one()
        return {
            'name': _('جلسات الجرد: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.stocktaking.session',
            'view_mode': 'tree,form',
            'domain': [
                '|',
                ('committee_chairman_id', '=', self.id),
                ('storekeeper_id', '=', self.id),
            ],
        }


class StocktakingSessionHR(models.Model):
    """
    Enrich stocktaking session with HR-derived fields.
    Adds Many2many committee members and department filter.
    """
    _inherit = 'stock.stocktaking.session'

    committee_member_ids = fields.Many2many(
        'hr.employee',
        'stocktaking_committee_emp_rel',
        'session_id',
        'employee_id',
        string='أعضاء لجنة الجرد (موظفون)',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='الإدارة / القسم',
        tracking=True,
    )
    chairman_job_title = fields.Char(
        string='مسمى رئيس اللجنة',
        related='committee_chairman_id.job_title',
        store=True,
    )
    storekeeper_job_title = fields.Char(
        string='مسمى أمين المخزن',
        related='storekeeper_id.job_title',
        store=True,
    )

    @api.onchange('storekeeper_id')
    def _onchange_storekeeper(self):
        if not self.storekeeper_id and self.env.user.employee_id:
            self.storekeeper_id = self.env.user.employee_id

    @api.onchange('committee_chairman_id')
    def _onchange_chairman(self):
        if self.committee_chairman_id:
            if self.committee_chairman_id not in self.committee_member_ids:
                self.committee_member_ids = [(4, self.committee_chairman_id.id)]
