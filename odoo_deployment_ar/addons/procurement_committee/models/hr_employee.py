from odoo import api, fields, models, _


class HrEmployeeCommittee(models.Model):
    """Extend hr.employee — show committees they belong to."""
    _inherit = 'hr.employee'

    committee_count = fields.Integer(
        string='عدد اللجان',
        compute='_compute_committee_stats',
    )
    is_committee_chairman = fields.Boolean(
        string='رئيس لجنة',
        compute='_compute_committee_stats',
    )

    def _compute_committee_stats(self):
        for emp in self:
            members = self.env['committee.member'].search([
                ('employee_id', '=', emp.id)
            ])
            emp.committee_count = len(members.mapped('committee_id'))
            emp.is_committee_chairman = any(m.role == 'chairman' for m in members)

    def action_view_committees(self):
        self.ensure_one()
        members = self.env['committee.member'].search([('employee_id', '=', self.id)])
        committee_ids = members.mapped('committee_id').ids
        return {
            'name': _('لجان الموظف: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'procurement.committee',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', committee_ids)],
        }


class CommitteeMemberHR(models.Model):
    """Enrich committee.member with live HR fields."""
    _inherit = 'committee.member'

    work_phone = fields.Char(
        string='هاتف العمل',
        related='employee_id.work_phone',
        store=True,
    )
    work_email = fields.Char(
        string='البريد الإلكتروني',
        related='employee_id.work_email',
        store=True,
    )
    employee_active = fields.Boolean(
        related='employee_id.active',
        store=True,
        string='نشط',
    )

    @api.constrains('employee_id')
    def _check_employee_active(self):
        for rec in self:
            if rec.employee_id and not rec.employee_id.active:
                from odoo.exceptions import ValidationError
                raise ValidationError(_(
                    'لا يمكن إضافة موظف غير نشط إلى اللجنة: %s'
                ) % rec.employee_id.name)
