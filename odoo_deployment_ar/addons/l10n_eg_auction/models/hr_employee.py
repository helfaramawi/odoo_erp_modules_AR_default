from odoo import api, fields, models, _


class AuctionRequestHR(models.Model):
    """Add HR session officer to auction request."""
    _inherit = 'auction.request'

    session_officer_id = fields.Many2one(
        'hr.employee',
        string='مسؤول إدارة الجلسة',
        tracking=True,
        help='موظف HR المسؤول عن إدارة جلسة المزاد',
    )
    session_officer_job = fields.Char(
        string='مسمى مسؤول الجلسة',
        related='session_officer_id.job_title',
        store=True,
    )
    session_officer_phone = fields.Char(
        string='هاتف مسؤول الجلسة',
        related='session_officer_id.work_phone',
        store=True,
    )

    @api.onchange('session_officer_id')
    def _onchange_session_officer(self):
        if not self.session_officer_id and self.env.user.employee_id:
            self.session_officer_id = self.env.user.employee_id


class AuctionLeaseContractHR(models.Model):
    """Add HR contract officer to lease contracts."""
    _inherit = 'auction.lease.contract'

    contract_officer_id = fields.Many2one(
        'hr.employee',
        string='مسؤول العقد',
        tracking=True,
    )
    contract_officer_job = fields.Char(
        string='مسمى مسؤول العقد',
        related='contract_officer_id.job_title',
        store=True,
    )
