# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

GOV_EMPLOYMENT_TYPES = [
    ('permanent', 'دائم'),
    ('temporary', 'مؤقت'),
    ('seconded', 'منتدب'),
    ('loaned', 'معار'),
    ('contracted', 'متعاقد'),
]

GOV_ENTITIES = [
    ('diwan_general', 'الديوان العام'),
    ('districts', 'الأحياء'),
    ('port_fouad', 'مدينة بورفؤاد'),
]

# المستندات المطلوبة عند التعيين — إجراء رقم 13 (فتح ملف لموظف) من الـ FRD
REQUIRED_DOCUMENT_TYPES = [
    ('appointment_decision', 'قرار التعيين'),
    ('national_id_copy', 'صورة بطاقة الرقم القومي'),
    ('criminal_record', 'صحيفة الحالة الجنائية'),
    ('form_103', 'استمارة 103 ع.ح'),
    ('qualification_certificate', 'المؤهل الدراسي / الشهادة'),
    ('medical_fitness', 'شهادة اللياقة الصحية'),
]


class HrEmployeeDocument(models.Model):
    _name = 'demo_gov.hr.employee.document'
    _description = 'مستند من ملف الموظف الحكومي'

    employee_id = fields.Many2one('hr.employee', string='الموظف', required=True,
                                   ondelete='cascade', index=True)
    document_type = fields.Selection(REQUIRED_DOCUMENT_TYPES, string='نوع المستند', required=True)
    attachment_id = fields.Many2one('ir.attachment', string='الملف', required=True)
    submitted_date = fields.Date(string='تاريخ التقديم', default=fields.Date.today)
    notes = fields.Char(string='ملاحظة')

    _sql_constraints = [
        ('unique_doc_per_employee', 'unique(employee_id, document_type)',
         'هذا المستند مسجَّل بالفعل لهذا الموظف.'),
    ]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ── بيانات هوية حكومية ───────────────────────────────────────────────
    national_id = fields.Char(string='الرقم القومي', size=14, copy=False, tracking=True)
    permanent_employee_number = fields.Char(string='الرقم الوظيفي الثابت', readonly=True,
                                             copy=False, index=True, tracking=True)

    # ── التصنيف الوظيفي الحكومي ──────────────────────────────────────────
    gov_employment_type = fields.Selection(GOV_EMPLOYMENT_TYPES, string='نوع التعيين',
                                            default='permanent', tracking=True)
    gov_entity = fields.Selection(GOV_ENTITIES, string='الجهة التابع لها',
                                   default='diwan_general', tracking=True)
    civil_service_grade = fields.Char(string='الدرجة الوظيفية')

    # ── قرار التعيين ──────────────────────────────────────────────────────
    appointment_decision_number = fields.Char(string='رقم قرار التعيين')
    appointment_decision_date = fields.Date(string='تاريخ قرار التعيين')

    # ── مستندات الملف ─────────────────────────────────────────────────────
    document_ids = fields.One2many('demo_gov.hr.employee.document', 'employee_id',
                                    string='مستندات الملف')
    missing_documents = fields.Char(string='المستندات الناقصة', compute='_compute_missing_documents')
    documents_complete = fields.Boolean(string='الملف مكتمل المستندات',
                                         compute='_compute_missing_documents')

    @api.depends('document_ids.document_type')
    def _compute_missing_documents(self):
        required = {k for k, _ in REQUIRED_DOCUMENT_TYPES}
        labels = dict(REQUIRED_DOCUMENT_TYPES)
        for rec in self:
            present = set(rec.document_ids.mapped('document_type'))
            missing = required - present
            rec.missing_documents = '، '.join(labels[m] for m in missing) if missing else ''
            rec.documents_complete = not missing

    @api.constrains('national_id')
    def _check_national_id(self):
        for rec in self:
            if rec.national_id and not re.fullmatch(r'\d{14}', rec.national_id):
                raise ValidationError(_('الرقم القومي يجب أن يتكون من 14 رقماً بالضبط.'))

    _sql_constraints = [
        ('unique_national_id', 'unique(national_id)',
         'هذا الرقم القومي مسجَّل بالفعل لموظف آخر.'),
        ('unique_permanent_employee_number', 'unique(permanent_employee_number)',
         'هذا الرقم الوظيفي الثابت مستخدم بالفعل.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('permanent_employee_number'):
                vals['permanent_employee_number'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.employee') or '/'
        return super().create(vals_list)

    def write(self, vals):
        if 'permanent_employee_number' in vals:
            for rec in self:
                if rec.permanent_employee_number and rec.permanent_employee_number != vals['permanent_employee_number']:
                    raise ValidationError(_('لا يمكن تعديل الرقم الوظيفي الثابت بعد تعيينه.'))
        return super().write(vals)
