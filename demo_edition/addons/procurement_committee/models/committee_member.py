from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CommitteeMember(models.Model):
    """عضو اللجنة — Committee Member"""
    _name = 'committee.member'
    _description = 'عضو لجنة - Committee Member'
    _order = 'role, sequence'

    committee_id = fields.Many2one(
        'procurement.committee', string='اللجنة',
        required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(string='الترتيب', default=10)
    employee_id = fields.Many2one(
        'hr.employee', string='الموظف', required=True,
    )
    name = fields.Char(related='employee_id.name', store=True)
    job_title = fields.Char(related='employee_id.job_title', store=True, string='المسمى الوظيفي')
    department_id = fields.Many2one(related='employee_id.department_id', store=True, string='الإدارة')

    role = fields.Selection([
        ('chairman', 'رئيس لجنة'),
        ('member',   'عضو'),
        ('secretary','أمين سر'),
        ('expert',   'خبير / مستشار'),
    ], string='الدور في اللجنة', required=True, default='member')

    is_chairman = fields.Boolean(
        string='رئيس', compute='_compute_is_chairman', store=True,
    )
    notes = fields.Char(string='ملاحظات')

    _sql_constraints = [
        ('employee_committee_uniq', 'unique(committee_id, employee_id)',
         'لا يمكن إضافة نفس الموظف مرتين في اللجنة'),
    ]

    @api.depends('role')
    def _compute_is_chairman(self):
        for rec in self:
            rec.is_chairman = (rec.role == 'chairman')
