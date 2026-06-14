# -*- coding: utf-8 -*-
"""
نموذج سيناريوهات اختبار القبول
يسجل كل سيناريو اختبار تم توليده
"""
from odoo import models, fields, api


class UATScenario(models.Model):
    _name = 'arabic.government.uat.scenario'
    _description = 'سيناريو اختبار القبول'
    _order = 'module, sequence'
    _inherit = ['mail.thread']

    name = fields.Char('اسم السيناريو', required=True)
    test_case_id = fields.Char('رقم حالة الاختبار', required=True)
    batch_reference = fields.Char('مرجع الدفعة', default='UAT-AR-GOV-2026', index=True)
    module = fields.Char('الوحدة')
    arabic_module_name = fields.Char('اسم الوحدة بالعربية')
    sequence = fields.Integer(default=10)
    precondition = fields.Text('الشرط المسبق')
    steps = fields.Text('خطوات الاختبار')
    expected_result = fields.Text('النتيجة المتوقعة')
    record_ref = fields.Char('مرجع السجل')
    user_role = fields.Char('دور المستخدم')
    status = fields.Selection([
        ('pending', 'معلق'),
        ('pass', 'ناجح'),
        ('fail', 'فاشل'),
        ('blocked', 'محجوب'),
    ], default='pending', string='الحالة', tracking=True)
    notes = fields.Text('ملاحظات')
    category = fields.Selection([
        ('budget', 'الموازنة'),
        ('commitment', 'الارتباطات'),
        ('procurement', 'المشتريات'),
        ('dossier', 'الاضبارة'),
        ('disbursement', 'الصرف'),
        ('accounting', 'المحاسبة'),
        ('project', 'المشروعات'),
        ('inventory', 'المخازن'),
        ('hr', 'الموارد البشرية'),
        ('ai', 'الذكاء الاصطناعي'),
        ('security', 'الأمان'),
        ('report', 'التقارير'),
    ], string='التصنيف')


class UATGenerationLog(models.Model):
    _name = 'arabic.government.uat.generation.log'
    _description = 'سجل توليد بيانات الاختبار'
    _order = 'create_date desc'
    _inherit = ['mail.thread']

    name = fields.Char('المرجع', required=True, default='/')
    batch_reference = fields.Char('مرجع الدفعة', default='UAT-AR-GOV-2026')
    state = fields.Selection([
        ('draft', 'جديد'),
        ('done', 'مكتمل'),
        ('failed', 'فشل'),
    ], default='draft', string='الحالة', tracking=True)
    result_summary = fields.Text('ملخص النتائج', readonly=True)
    error_message = fields.Text('رسالة الخطأ', readonly=True)
    total_created = fields.Integer('إجمالي السجلات المنشأة', readonly=True)
    notes = fields.Text('ملاحظات')
    line_ids = fields.One2many('arabic.government.uat.generation.log.line', 'log_id', 'التفاصيل')
    create_date = fields.Datetime('تاريخ التوليد', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('uat.generation.log') or '/'
        return super().create(vals_list)


class UATGenerationLogLine(models.Model):
    _name = 'arabic.government.uat.generation.log.line'
    _description = 'تفصيل سجل التوليد'
    _order = 'sequence'

    log_id = fields.Many2one('arabic.government.uat.generation.log', ondelete='cascade')
    sequence = fields.Integer(default=10)
    category = fields.Char('التصنيف')
    description = fields.Char('الوصف')
    record_count = fields.Integer('عدد السجلات')
    status = fields.Selection([
        ('ok', 'تم'),
        ('skipped', 'تخطى'),
        ('error', 'خطأ'),
    ], default='ok')
    message = fields.Char('رسالة')
