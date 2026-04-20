from odoo import api, fields, models, _


class HrEmployeeAdjudication(models.Model):
    """Extend hr.employee — show adjudication files their committee was involved in."""
    _inherit = 'hr.employee'

    adjudication_count = fields.Integer(
        string='ملفات البت',
        compute='_compute_adjudication_count',
    )

    def _compute_adjudication_count(self):
        for emp in self:
            members = self.env['committee.member'].search([('employee_id', '=', emp.id)])
            committee_ids = members.mapped('committee_id').ids
            emp.adjudication_count = self.env['procurement.adjudication'].search_count([
                '|', '|',
                ('technical_committee_id', 'in', committee_ids),
                ('financial_committee_id', 'in', committee_ids),
                ('opening_committee_id', 'in', committee_ids),
            ]) if committee_ids else 0

    def action_view_adjudications(self):
        self.ensure_one()
        members = self.env['committee.member'].search([('employee_id', '=', self.id)])
        committee_ids = members.mapped('committee_id').ids
        return {
            'name': _('ملفات البت: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'procurement.adjudication',
            'view_mode': 'tree,form',
            'domain': [
                '|', '|',
                ('technical_committee_id', 'in', committee_ids),
                ('financial_committee_id', 'in', committee_ids),
                ('opening_committee_id', 'in', committee_ids),
            ],
        }


class ProcurementAdjudicationHR(models.Model):
    """Show committee chairman names and member count from HR on adjudication form."""
    _inherit = 'procurement.adjudication'

    technical_chairman_name = fields.Char(
        string='رئيس اللجنة الفنية',
        related='technical_committee_id.chairman_id.name',
        store=True,
    )
    financial_chairman_name = fields.Char(
        string='رئيس اللجنة المالية',
        related='financial_committee_id.chairman_id.name',
        store=True,
    )
    technical_member_count = fields.Integer(
        string='أعضاء اللجنة الفنية',
        related='technical_committee_id.member_count',
        store=True,
    )

    @api.onchange('technical_committee_id')
    def _onchange_technical_committee(self):
        if self.technical_committee_id and not self.technical_committee_id.member_ids:
            return {'warning': {
                'title': _('تحذير'),
                'message': _('اللجنة الفنية لا تحتوي على أعضاء — يرجى إضافة الأعضاء أولاً.'),
            }}

    @api.onchange('financial_committee_id')
    def _onchange_financial_committee(self):
        if self.financial_committee_id and not self.financial_committee_id.member_ids:
            return {'warning': {
                'title': _('تحذير'),
                'message': _('لجنة البت المالي لا تحتوي على أعضاء — يرجى إضافة الأعضاء أولاً.'),
            }}
