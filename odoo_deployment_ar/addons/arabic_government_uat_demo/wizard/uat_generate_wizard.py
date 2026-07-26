# -*- coding: utf-8 -*-
"""
معالج توليد بيانات الاختبار الحكومي العربي
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class UATGenerateWizard(models.TransientModel):
    _name = 'arabic.government.uat.generate.wizard'
    _description = 'معالج توليد بيانات الاختبار'

    batch_reference = fields.Char(
        'مرجع الدفعة', default='UAT-AR-GOV-2026', required=True
    )
    generate_budget_cases = fields.Boolean('توليد بيانات الموازنة', default=True)
    generate_commitment_cases = fields.Boolean('توليد بيانات الارتباطات', default=True)
    generate_procurement_cases = fields.Boolean('توليد بيانات المشتريات', default=True)
    generate_dossier_cases = fields.Boolean('توليد بيانات الاضبارة', default=True)
    generate_disbursement_cases = fields.Boolean('توليد بيانات الصرف (دفتر 55)', default=True)
    generate_accounting_cases = fields.Boolean('توليد بيانات المحاسبة', default=True)
    generate_project_cases = fields.Boolean('توليد بيانات المشروعات', default=True)
    generate_inventory_cases = fields.Boolean('توليد بيانات المخازن', default=True)
    generate_hr_cases = fields.Boolean('توليد بيانات الموارد البشرية والسلف', default=True)
    generate_custody_cases = fields.Boolean('توليد بيانات العهد', default=True)
    generate_auction_cases = fields.Boolean('توليد بيانات المزادات', default=True)
    generate_cheque_cases = fields.Boolean('توليد بيانات الشيكات', default=True)
    generate_penalty_cases = fields.Boolean('توليد بيانات الجزاءات', default=True)
    generate_stocktaking_cases = fields.Boolean('توليد بيانات الجرد الحكومي', default=True)
    generate_fixed_asset_cases = fields.Boolean('توليد بيانات الأصول الثابتة', default=True)
    generate_ai_agent_cases = fields.Boolean('توليد سيناريوهات الذكاء الاصطناعي', default=True)
    generate_report_cases = fields.Boolean('توليد سيناريوهات التقارير', default=True)
    reset_existing_uat_data = fields.Boolean(
        'إعادة تعيين بيانات UAT السابقة',
        default=False,
        help='إذا كان مفعلاً، سيتم حذف سيناريوهات الاختبار القديمة وإعادة توليدها',
    )
    notes = fields.Text('ملاحظات')

    def action_generate(self):
        self.ensure_one()

        if not self.batch_reference:
            raise UserError('يجب إدخال مرجع الدفعة')

        # Optionally reset existing UAT scenario records only (not transactions)
        if self.reset_existing_uat_data:
            self.env['arabic.government.uat.scenario'].search([
                ('batch_reference', '=', self.batch_reference)
            ]).unlink()

        log = self.env['arabic.government.uat.generation.log'].create({
            'batch_reference': self.batch_reference,
            'notes': self.notes or '',
        })

        options = {
            'generate_budget_cases': self.generate_budget_cases,
            'generate_commitment_cases': self.generate_commitment_cases,
            'generate_procurement_cases': self.generate_procurement_cases,
            'generate_dossier_cases': self.generate_dossier_cases,
            'generate_disbursement_cases': self.generate_disbursement_cases,
            'generate_accounting_cases': self.generate_accounting_cases,
            'generate_project_cases': self.generate_project_cases,
            'generate_inventory_cases': self.generate_inventory_cases,
            'generate_hr_cases': self.generate_hr_cases,
            'generate_custody_cases': self.generate_custody_cases,
            'generate_auction_cases': self.generate_auction_cases,
            'generate_cheque_cases': self.generate_cheque_cases,
            'generate_penalty_cases': self.generate_penalty_cases,
            'generate_stocktaking_cases': self.generate_stocktaking_cases,
            'generate_fixed_asset_cases': self.generate_fixed_asset_cases,
            'generate_ai_agent_cases': self.generate_ai_agent_cases,
            'generate_report_cases': self.generate_report_cases,
        }

        # generate_all() uses savepoints for every generator — it never raises.
        # Do NOT call cr.rollback() here; that would destroy the log record.
        self.env['arabic.government.uat.generator'].generate_all(options, log)

        return {'type': 'ir.actions.act_window_close'}
