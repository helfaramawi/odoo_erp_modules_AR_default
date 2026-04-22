from odoo import api, fields, models, _


class HrEmployeeAdditionPermit(models.Model):
    """Extend hr.employee — show addition permits and inspections handled."""
    _inherit = 'hr.employee'

    addition_permit_count = fields.Integer(
        string='أذونات الإضافة',
        compute='_compute_permit_stats',
    )
    inspection_report_count = fields.Integer(
        string='محاضر الفحص',
        compute='_compute_permit_stats',
    )

    def _compute_permit_stats(self):
        for emp in self:
            emp.addition_permit_count = self.env['stock.addition.permit'].search_count([
                ('storekeeper_id', '=', emp.id),
            ])
            emp.inspection_report_count = self.env['stock.inspection.report'].search_count([
                ('inspector_id', '=', emp.id),
            ])

    def action_view_addition_permits(self):
        self.ensure_one()
        return {
            'name': _('أذونات الإضافة: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.addition.permit',
            'view_mode': 'tree,form',
            'domain': [('storekeeper_id', '=', self.id)],
        }

    def action_view_inspections(self):
        self.ensure_one()
        return {
            'name': _('محاضر الفحص: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.inspection.report',
            'view_mode': 'tree,form',
            'domain': [('inspector_id', '=', self.id)],
        }


class StockAdditionPermitHR(models.Model):
    """Add HR-sourced fields to stock.addition.permit."""
    _inherit = 'stock.addition.permit'

    storekeeper_job = fields.Char(
        string='مسمى أمين المخزن',
        related='storekeeper_id.job_title',
        store=True,
    )
    storekeeper_dept = fields.Many2one(
        'hr.department',
        string='إدارة أمين المخزن',
        related='storekeeper_id.department_id',
        store=True,
    )

    @api.onchange('storekeeper_id')
    def _onchange_storekeeper(self):
        if not self.storekeeper_id and self.env.user.employee_id:
            self.storekeeper_id = self.env.user.employee_id


class StockInspectionReportHR(models.Model):
    """Add HR-sourced fields to stock.inspection.report."""
    _inherit = 'stock.inspection.report'

    inspector_job = fields.Char(
        string='مسمى المفتش',
        related='inspector_id.job_title',
        store=True,
    )
    inspector_dept = fields.Many2one(
        'hr.department',
        string='إدارة المفتش',
        related='inspector_id.department_id',
        store=True,
    )

    @api.onchange('inspector_id')
    def _onchange_inspector(self):
        if not self.inspector_id and self.env.user.employee_id:
            self.inspector_id = self.env.user.employee_id
