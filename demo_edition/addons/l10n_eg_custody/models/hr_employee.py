from odoo import api, fields, models, _


class HrEmployeeCustody(models.Model):
    """
    Extend hr.employee — show custody summary on employee form.
    Auto-syncs national_id to Form 193 when employee SSN changes.
    """
    _inherit = 'hr.employee'

    custody_count = fields.Integer(
        string='عدد العهد النشطة',
        compute='_compute_custody_stats',
    )
    custody_value_total = fields.Float(
        string='إجمالي قيمة العهد',
        compute='_compute_custody_stats',
        digits='Account',
    )
    has_overdue_custody = fields.Boolean(
        string='عهد متأخرة',
        compute='_compute_custody_stats',
    )

    def _compute_custody_stats(self):
        today = fields.Date.context_today(self)
        for emp in self:
            active = self.env['custody.assignment'].search([
                ('employee_id', '=', emp.id),
                ('state', 'in', ['active', 'transferred']),
            ])
            emp.custody_count = len(active)
            emp.custody_value_total = sum(active.mapped('estimated_value'))
            emp.has_overdue_custody = any(
                r.expected_return_date and r.expected_return_date < today
                for r in active
            )

    def action_view_custody(self):
        self.ensure_one()
        return {
            'name': _('عهد الموظف: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.assignment',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'default_national_id': self.ssnid or '',
            },
        }

    def action_view_custody_transfers(self):
        self.ensure_one()
        return {
            'name': _('تحويلات العهدة: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.transfer',
            'view_mode': 'tree,form',
            'domain': [
                '|',
                ('from_employee_id', '=', self.id),
                ('to_employee_id', '=', self.id),
            ],
        }

    def write(self, vals):
        """
        When employee's ssnid changes, sync to all active custody assignments.
        GAFI requirement: Form 193 must always show current national ID.
        """
        result = super().write(vals)
        if 'ssnid' in vals and vals['ssnid']:
            for emp in self:
                outdated = self.env['custody.assignment'].search([
                    ('employee_id', '=', emp.id),
                    ('state', 'in', ['draft', 'active', 'transferred']),
                    ('national_id', '!=', vals['ssnid']),
                ])
                if outdated:
                    outdated.write({'national_id': vals['ssnid']})
                    outdated.message_post(
                        body=_('🔄 تحديث تلقائي للرقم القومي من بيانات الموظف: %s')
                        % vals['ssnid']
                    )
        return result
