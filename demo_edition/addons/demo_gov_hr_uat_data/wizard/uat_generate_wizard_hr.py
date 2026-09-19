# -*- coding: utf-8 -*-
"""
امتداد غير هدّام لمعالج توليد بيانات الاختبار (demo_gov_uat_tools) —
يضيف خيارات الموارد البشرية والرواتب من غير ما يعدّل الملف الأصلي.
نعيد بناء action_generate كاملاً (بدل استدعاء super) لأن قاموس الخيارات
المُرسَل لـ generate_all لازم يتضمن مفاتيحنا الجديدة في نفس الاستدعاء
الواحد، حتى ما ينفصلش توليد الموارد البشرية عن سجل الدفعة نفسه.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class UATGenerateWizardHR(models.TransientModel):
    _inherit = 'arabic.government.uat.generate.wizard'

    generate_hr_leave_cases = fields.Boolean('توليد بيانات الإجازات', default=True)
    generate_hr_training_cases = fields.Boolean('توليد بيانات التدريب', default=True)
    generate_hr_recruitment_cases = fields.Boolean('توليد بيانات التوظيف', default=True)
    generate_hr_performance_cases = fields.Boolean(
        'توليد بيانات تقييم الأداء والتظلمات', default=True)
    generate_hr_transfer_cases = fields.Boolean(
        'توليد بيانات النقل والندب والإعارة والترقيات', default=True)
    generate_hr_payroll_cases = fields.Boolean('توليد بيانات الرواتب', default=True)
    generate_hr_takaful_cases = fields.Boolean('توليد بيانات صندوق التكافل', default=True)
    generate_hr_pension_cases = fields.Boolean('توليد بيانات المعاشات', default=True)
    generate_hr_disclosure_cases = fields.Boolean('توليد بيانات الإفصاح المالي', default=True)
    generate_hr_positions_cases = fields.Boolean('توليد بيانات موازنة الوظائف', default=True)

    def action_generate(self):
        self.ensure_one()
        self._check_demo_environment()

        if not self.batch_reference:
            raise UserError(_('يجب إدخال مرجع الدفعة'))

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
            'generate_hr_leave_cases': self.generate_hr_leave_cases,
            'generate_hr_training_cases': self.generate_hr_training_cases,
            'generate_hr_recruitment_cases': self.generate_hr_recruitment_cases,
            'generate_hr_performance_cases': self.generate_hr_performance_cases,
            'generate_hr_transfer_cases': self.generate_hr_transfer_cases,
            'generate_hr_payroll_cases': self.generate_hr_payroll_cases,
            'generate_hr_takaful_cases': self.generate_hr_takaful_cases,
            'generate_hr_pension_cases': self.generate_hr_pension_cases,
            'generate_hr_disclosure_cases': self.generate_hr_disclosure_cases,
            'generate_hr_positions_cases': self.generate_hr_positions_cases,
        }

        # generate_all() uses savepoints for every generator — it never raises.
        self.env['arabic.government.uat.generator'].generate_all(options, log)

        return {'type': 'ir.actions.act_window_close'}
