# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployeeDocument(models.Model):
    _inherit = 'demo_gov.hr.employee.document'

    document_type = fields.Selection(
        selection_add=[('form_105', 'نموذج 105 - مستفيدو منحة الوفاة')],
        ondelete={'form_105': 'cascade'},
    )
