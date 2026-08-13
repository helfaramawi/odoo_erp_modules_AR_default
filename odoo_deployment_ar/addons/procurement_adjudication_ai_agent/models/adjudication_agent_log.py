# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProcurementAdjudicationAgentLog(models.Model):
    _name = 'procurement.adjudication.agent.log'
    _description = 'سجل وكيل تحليل العروض الفنية والمالية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'analysis_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='رقم التحليل', required=True, copy=False, default='جديد', tracking=True)
    analysis_date = fields.Datetime(string='تاريخ التحليل', default=fields.Datetime.now, required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='المستخدم', default=lambda self: self.env.user, tracking=True)

    adjudication_id = fields.Many2one('procurement.adjudication', string='عملية البت', index=True, ondelete='cascade')
    supplier_line_id = fields.Many2one('adjudication.supplier.line', string='عرض المورد', index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='المورد', index=True)

    analysis_type = fields.Selection([
        ('technical', 'تحليل فني'),
        ('financial', 'تحليل مالي'),
        ('minutes', 'مسودة محضر'),
    ], string='نوع التحليل', required=True, index=True)

    technical_score = fields.Float(string='نسبة المطابقة الفنية %')
    technical_pass = fields.Boolean(string='مستوفٍ فنياً')
    financial_rank = fields.Integer(string='الترتيب المالي')
    financial_bid = fields.Float(string='قيمة العرض المالي')
    deviation_pct = fields.Float(string='نسبة الانحراف عن القيمة التقديرية %')
    dumping_warning = fields.Boolean(string='تحذير انخفاض مبالغ فيه')

    result_summary = fields.Text(string='ملخص النتيجة')
    strengths = fields.Text(string='نقاط القوة')
    weaknesses = fields.Text(string='نقاط الضعف')
    recommendation = fields.Text(string='التوصية')
    technical_details = fields.Text(string='تفاصيل تقنية')

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', 'جديد') == 'جديد':
                vals['name'] = seq.next_by_code('procurement.adjudication.agent.log') or 'جديد'
        return super().create(vals_list)

    def action_open_adjudication(self):
        self.ensure_one()
        if not self.adjudication_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('عملية البت'),
            'res_model': 'procurement.adjudication',
            'res_id': self.adjudication_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
