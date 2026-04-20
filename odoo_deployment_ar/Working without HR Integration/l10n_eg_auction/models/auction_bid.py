from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AuctionBid(models.Model):
    """تسجيل العروض — Bid Recording (standalone model)"""
    _name = 'auction.bid'
    _description = 'عرض مزاد - Auction Bid'
    _inherit = ['mail.thread']
    _order = 'amount desc'

    auction_request_id = fields.Many2one(
        'auction.request', string='المزاد',
        required=True, ondelete='cascade', tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='المزايد', required=True, tracking=True,
    )
    amount = fields.Float(
        string='قيمة العرض', required=True, digits='Account', tracking=True,
    )
    deposit_paid = fields.Boolean(
        string='دفع التأمين الابتدائي', default=False, tracking=True,
    )
    deposit_receipt_ref = fields.Char(string='رقم إيصال التأمين')
    state = fields.Selection([
        ('submitted', 'مقدم'),
        ('accepted',  'مقبول'),
        ('rejected',  'مرفوض'),
    ], default='submitted', tracking=True)
    rejection_reason = fields.Text(string='سبب الرفض')
    notes = fields.Text(string='ملاحظات')

    _sql_constraints = [
        ('amount_positive', 'CHECK(amount > 0)', 'قيمة العرض يجب أن تكون أكبر من الصفر'),
    ]

    def action_accept(self):
        for rec in self:
            other = rec.auction_request_id.bid_ids.filtered(
                lambda b: b.id != rec.id and b.state == 'accepted'
            )
            other.write({'state': 'rejected', 'rejection_reason': _('تم قبول عرض آخر')})
            rec.write({'state': 'accepted'})
            rec.message_post(body=_('✅ تم قبول العرض بمبلغ %.2f') % rec.amount)

    def action_reject(self):
        self.write({'state': 'rejected'})
