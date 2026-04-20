# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BulkPenaltyWizard(models.TransientModel):
    _name = 'port_said.penalty.bulk.wizard'
    _description = 'ساحر تسجيل جزاءات جماعية'

    subject_type = fields.Selection([
        ('employee', 'موظف'),
        ('vendor',   'مورد / مقاول'),
    ], string='نوع الجهة', required=True, default='employee')

    employee_ids = fields.Many2many('hr.employee', string='الموظفون')
    vendor_ids = fields.Many2many('res.partner', string='الموردون',
        domain="[('supplier_rank', '>', 0)]")

    violation_type_id = fields.Many2one('port_said.penalty.violation_type',
        string='نوع المخالفة', required=True,
        domain="[('subject_type', '=', subject_type)]")
    penalty_type_option_id = fields.Many2one('port_said.penalty.type_option',
        string='نوع الجزاء', required=True)

    incident_date = fields.Date(string='تاريخ الواقعة', required=True,
        default=fields.Date.context_today)
    incident_description = fields.Text(string='وصف الواقعة', required=True)

    amount = fields.Monetary(string='قيمة الغرامة',
        currency_field='currency_id')
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    def action_create_penalties(self):
        self.ensure_one()
        subjects = (self.employee_ids if self.subject_type == 'employee'
                   else self.vendor_ids)
        if not subjects:
            raise UserError(_('يجب اختيار جهة واحدة على الأقل.'))

        Penalty = self.env['port_said.penalty']
        created = []
        for subj in subjects:
            vals = {
                'subject_type': self.subject_type,
                'violation_type_id': self.violation_type_id.id,
                'penalty_type_option_id': self.penalty_type_option_id.id,
                'incident_date': self.incident_date,
                'incident_description': self.incident_description,
                'amount': self.amount,
            }
            if self.subject_type == 'employee':
                vals['employee_id'] = subj.id
            else:
                vals['vendor_id'] = subj.id
            created.append(Penalty.create(vals).id)

        return {
            'type': 'ir.actions.act_window',
            'name': _('الجزاءات المُنشأة'),
            'res_model': 'port_said.penalty',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created)],
        }
