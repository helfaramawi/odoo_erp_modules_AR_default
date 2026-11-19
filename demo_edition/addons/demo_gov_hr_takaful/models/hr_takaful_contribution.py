# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrTakafulContribution(models.Model):
    _name = 'demo_gov.hr.takaful.contribution'
    _description = 'اشتراك شهري في صندوق التكافل'
    _order = 'trans_date desc'

    name = fields.Char(string='رقم الاشتراك', readonly=True, copy=False)
    member_id = fields.Many2one('demo_gov.hr.takaful.member', string='العضو', required=True,
                                 ondelete='cascade')
    amount = fields.Float(string='المبلغ', required=True)
    trans_date = fields.Date(string='التاريخ', default=fields.Date.today, required=True)
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('posted', 'مرحَّل'),
    ], default='draft', string='الحالة')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo_gov.hr.takaful.contribution') or '/'
        return super().create(vals_list)

    def action_post(self):
        # ملحوظة: هذا الإصدار التجريبي يحدّث إجمالي اشتراكات العضو فقط ولا
        # يُنشئ قيد يومية محاسبي فعلي — حقول الحسابات في إعدادات الصندوق
        # للتوثيق تمهيداً لتفعيل الترحيل الفعلي عند الحاجة.
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_('الاشتراك مرحَّل بالفعل.'))
            rec.member_id.total_contributions += rec.amount
        self.write({'state': 'posted'})
