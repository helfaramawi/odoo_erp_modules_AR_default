# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidDaftar55AccountReconcileAlert(models.Model):
    _name = 'port_said.daftar55.account.reconcile.alert'
    _description = 'تنبيه عدم مطابقة دفتر 55 مع القيود المحاسبية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='رقم التنبيه', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    daftar55_id = fields.Many2one('port_said.daftar55', string='سجل دفتر 55', required=True, index=True, ondelete='cascade', tracking=True)
    daftar55_number = fields.Char(string='رقم دفتر 55', tracking=True)
    daftar55_date = fields.Date(string='تاريخ دفتر 55')
    budget_line = fields.Char(string='بند الموازنة')
    beneficiary_name = fields.Char(string='المستفيد')
    amount_gross = fields.Monetary(string='قيمة دفتر 55', currency_field='currency_id', tracking=True)

    move_ids = fields.Many2many('account.move', 'daftar55_reconcile_alert_move_rel', 'alert_id', 'move_id', string='القيود المحاسبية المرتبطة')
    move_count = fields.Integer(string='عدد القيود المرتبطة')
    move_total_debit = fields.Monetary(string='إجمالي مدين القيود', currency_field='currency_id')
    move_total_credit = fields.Monetary(string='إجمالي دائن القيود', currency_field='currency_id')
    difference_amount = fields.Monetary(string='قيمة الفرق', currency_field='currency_id', tracking=True)

    alert_type = fields.Selection([
        ('missing_move', 'سجل دفتر 55 مرحل بدون قيد محاسبي'),
        ('amount_mismatch', 'فرق قيمة بين دفتر 55 والقيد'),
        ('date_mismatch', 'فرق تاريخ غير مبرر'),
        ('budget_line_mismatch', 'حساب/بند غير مطابق لبند الموازنة'),
        ('duplicate_moves', 'تكرار قيد لنفس سجل الصرف'),
    ], string='نوع عدم المطابقة', required=True, tracking=True)

    risk_level = fields.Selection([
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'مرتفعة'),
        ('critical', 'حرجة'),
    ], string='مستوى الخطورة', tracking=True)

    reason = fields.Text(string='سبب التنبيه', readonly=True)
    recommendation = fields.Text(string='التوصية بالإجراء', readonly=True)
    currency_id = fields.Many2one('res.currency', string='العملة', default=lambda self: self.env.company.currency_id.id)

    state = fields.Selection([
        ('new', 'جديد'),
        ('under_review', 'تحت المراجعة'),
        ('corrected', 'تم التصحيح'),
        ('justified', 'مبرر'),
        ('escalated', 'تم التصعيد'),
        ('closed', 'مغلق'),
        ('cancelled', 'ملغي'),
    ], string='الحالة', default='new', tracking=True)

    reviewed_by = fields.Many2one('res.users', string='تمت المراجعة بواسطة', readonly=True)
    reviewed_date = fields.Datetime(string='تاريخ المراجعة', readonly=True)
    review_notes = fields.Text(string='ملاحظات المراجعة')

    _sql_constraints = [
        ('unique_daftar55_reconcile_alert', 'unique(daftar55_id, alert_type)', 'يوجد تنبيه سابق لنفس سجل دفتر 55 ونفس نوع عدم المطابقة.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = seq.next_by_code('port_said.daftar55.account.reconcile.alert') or _('New')
        return super().create(vals_list)

    def action_open_daftar55(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'دفتر 55', 'res_model': 'port_said.daftar55', 'res_id': self.daftar55_id.id, 'view_mode': 'form', 'target': 'current'}

    def action_review(self):
        self.write({'state': 'under_review', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_corrected(self):
        self.write({'state': 'corrected', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_justify(self):
        self.write({'state': 'justified', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_escalate(self):
        self.write({'state': 'escalated', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})

    def action_close(self):
        self.write({'state': 'closed', 'reviewed_by': self.env.user.id, 'reviewed_date': fields.Datetime.now()})
