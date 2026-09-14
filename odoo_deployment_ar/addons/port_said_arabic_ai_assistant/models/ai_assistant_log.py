# -*- coding: utf-8 -*-
from odoo import fields, models


class PortSaidArabicAIAssistantLog(models.Model):
    _name = 'port_said.ai.assistant.log'
    _description = 'سجل المساعد اللغوي العربي'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'question'

    question = fields.Text(string='السؤال', required=True)
    normalized_question = fields.Text(string='السؤال بعد التحليل')
    answer_summary = fields.Text(string='ملخص الإجابة')
    model_name = fields.Char(string='الموديل')
    model_description = fields.Char(string='وصف الموديل')
    query_type = fields.Selection([
        ('search_read', 'قراءة سجلات'),
        ('read_group', 'تجميع / إحصاء'),
        ('count', 'عدد'),
        ('unknown', 'غير معروف'),
    ], string='نوع الاستعلام', default='unknown')
    domain_text = fields.Text(string='Domain')
    fields_text = fields.Text(string='Fields')
    result_count = fields.Integer(string='عدد النتائج')
    success = fields.Boolean(string='نجح')
    error_message = fields.Text(string='رسالة الخطأ')
    confidence = fields.Float(string='درجة الثقة')
    used_ollama = fields.Boolean(string='استخدم Ollama')
    ollama_raw = fields.Text(string='رد Ollama الخام')
    user_id = fields.Many2one('res.users', string='المستخدم', default=lambda s: s.env.user, index=True)
    company_id = fields.Many2one('res.company', string='الشركة', default=lambda s: s.env.company)
