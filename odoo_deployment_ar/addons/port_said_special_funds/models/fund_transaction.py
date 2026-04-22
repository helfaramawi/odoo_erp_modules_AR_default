from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FundTransaction(models.Model):
    """معاملة صندوق — إيراد أو مصروف"""
    _name = 'port_said.fund_transaction'
    _description = 'معاملة صندوق خاص'
    _inherit = ['mail.thread']
    _order = 'date desc'

    fund_id          = fields.Many2one('port_said.special_fund', string='الصندوق', required=True, ondelete='restrict')
    transaction_type = fields.Selection([
        ('revenue', 'إيراد'),
        ('expense', 'مصروف'),
        ('transfer_in',  'تحويل وارد'),
        ('transfer_out', 'تحويل صادر'),
    ], string='نوع المعاملة', required=True)
    date             = fields.Date(string='التاريخ', required=True, default=fields.Date.today)
    amount           = fields.Monetary(string='المبلغ', required=True, currency_field='currency_id')
    currency_id      = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    description      = fields.Char(string='البيان', required=True)
    source_ref       = fields.Char(string='المرجع (أمر دفع / إيصال)')
    partner_id       = fields.Many2one('res.partner', string='الجهة')

    # Inter-fund transfer — requires DUAL approval
    target_fund_id   = fields.Many2one(
        'port_said.special_fund',
        string='الصندوق الوجهة (للتحويل)',
        domain="[('id', '!=', fund_id)]",
    )
    transfer_approved_by1 = fields.Many2one('res.users', string='موافقة أولى')
    transfer_approved_by2 = fields.Many2one('res.users', string='موافقة ثانية')
    transfer_reason       = fields.Text(string='سبب التحويل')

    state = fields.Selection([
        ('draft',    'مسودة'),
        ('posted',   'مرحّل'),
        ('reversed', 'مُعاد'),
    ], default='draft', string='الحالة', tracking=True)

    move_id = fields.Many2one('account.move', string='قيد محاسبي')

    @api.constrains('transaction_type', 'target_fund_id', 'transfer_approved_by1', 'transfer_approved_by2')
    def _check_transfer_approvals(self):
        for rec in self:
            if rec.transaction_type in ('transfer_in', 'transfer_out'):
                if not rec.target_fund_id:
                    raise ValidationError(_('يجب تحديد الصندوق الوجهة للتحويل.'))
                if rec.state == 'posted':
                    if not rec.transfer_approved_by1 or not rec.transfer_approved_by2:
                        raise ValidationError(_(
                            'التحويل بين الصناديق يتطلب موافقتين منفصلتين.\n'
                            'خلط أرصدة الصناديق بدون موافقة مزدوجة مخالفة مالية.'
                        ))


    def action_post(self):
        for rec in self:
            if rec.transaction_type == "expense":
                rec.fund_id.check_disbursement_allowed(rec.amount)
                # تكامل مع C-FM-06: التحقق من الارتباط إذا وُجد
                if rec.commitment_id:
                    if rec.commitment_id.state not in ("cleared", "approved", "reserved"):
                        raise UserError(_(
                            "لا يمكن الصرف من الصندوق قبل تسميح البند.\n"
                            "حالة الارتباط: %s") % rec.commitment_id.state)
            rec.write({"state": "posted"})
            rec.message_post(body=_("✅ مرحّل — %s") % rec.description)

