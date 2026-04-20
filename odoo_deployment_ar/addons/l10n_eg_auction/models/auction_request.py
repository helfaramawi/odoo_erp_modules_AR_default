from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class AuctionRequest(models.Model):
    """
    طلب المزاد — Auction Request (FR-P9)
    Supports two paths:
    - Path A (Sale/بيع): Movables, Property, Other → auto sale.order
    - Path B (Lease/إيجار-حق انتفاع): → auction.lease.contract with annual % increase
    """
    _name = 'auction.request'
    _description = 'طلب مزاد - Auction Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'auction_date desc, name desc'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='رقم المزاد',
        required=True, copy=False, readonly=True, default='/',
        tracking=True,
    )
    description = fields.Text(string='وصف المزاد', tracking=True)

    # ── Auction Type ──────────────────────────────────────────────────────────
    auction_type = fields.Selection([
        ('sale', 'بيع - Sale'),
        ('lease', 'إيجار / حق انتفاع - Lease / Usufruct'),
    ], string='نوع المزاد', required=True, default='sale', tracking=True)

    sale_type = fields.Selection([
        ('movables', 'منقولات - Movables'),
        ('property', 'عقارات - Real Property'),
        ('other', 'أخرى - Other'),
    ], string='نوع البيع', tracking=True,
       invisible="auction_type != 'sale'")

    tender_method = fields.Selection([
        ('public', 'مزايدة عامة - Public Auction'),
        ('local', 'مزايدة محلية - Local Auction'),
        ('direct', 'اتفاق مباشر - Direct Agreement'),
    ], string='طريقة الطرح', required=True, default='public', tracking=True)

    # ── Items / Assets ────────────────────────────────────────────────────────
    product_id = fields.Many2one(
        'product.product',
        string='الصنف / المنقول',
        tracking=True,
        invisible="sale_type == 'property' or auction_type == 'lease'",
    )
    qty = fields.Float(
        string='الكمية', default=1.0, digits='Product Unit of Measure',
        invisible="sale_type == 'property' or auction_type == 'lease'",
    )
    uom_id = fields.Many2one(
        'uom.uom', string='الوحدة',
        related='product_id.uom_id', store=True,
    )
    asset_description = fields.Char(
        string='وصف الأصل / العقار',
        tracking=True,
        invisible="sale_type == 'movables'",
    )
    estimated_value = fields.Float(
        string='القيمة التقديرية', digits='Account', tracking=True,
    )

    # ── Session ────────────────────────────────────────────────────────────────
    auction_date = fields.Datetime(
        string='تاريخ ووقت جلسة المزاد', required=True,
        default=fields.Datetime.now, tracking=True,
    )
    venue = fields.Char(string='مكان انعقاد الجلسة', tracking=True)
    initial_deposit = fields.Float(
        string='التأمين الابتدائي', digits='Account', tracking=True,
        help='Initial deposit required from bidders',
    )
    deposit_received = fields.Boolean(
        string='تم استلام التأمين', default=False, tracking=True,
    )

    # ── Committee ─────────────────────────────────────────────────────────────
    has_committee = fields.Boolean(
        string='تشكيل لجنة', default=True, tracking=True,
        help='FR-P7: Sovereign entities do NOT require committee',
    )
    committee_formation_ref = fields.Char(
        string='رقم قرار تشكيل اللجنة', tracking=True,
    )
    committee_notes = fields.Text(string='ملاحظات اللجنة')

    # ── Bidders ───────────────────────────────────────────────────────────────
    bid_ids = fields.One2many(
        'auction.bid', 'auction_request_id', string='العروض / المزايدات',
    )
    bid_count = fields.Integer(compute='_compute_bid_stats', string='عدد العروض')
    highest_bid = fields.Float(compute='_compute_bid_stats', string='أعلى عرض', digits='Account')
    awarded_bid_id = fields.Many2one(
        'auction.bid', string='العرض الفائز', tracking=True, readonly=True,
    )
    awarded_partner_id = fields.Many2one(
        'res.partner', string='الفائز بالمزاد', tracking=True, readonly=True,
    )
    awarded_amount = fields.Float(
        string='مبلغ الترسية', digits='Account', tracking=True, readonly=True,
    )

    # ── Output Documents ──────────────────────────────────────────────────────
    sale_order_id = fields.Many2one(
        'sale.order', string='أمر البيع', readonly=True, copy=False,
    )
    lease_contract_id = fields.Many2one(
        'auction.lease.contract', string='عقد الإيجار', readonly=True, copy=False,
    )
    award_notification_date = fields.Date(
        string='تاريخ إخطار الترسية', tracking=True,
    )

    # ── State Machine ─────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',        'مسودة'),
        ('confirmed',    'معتمد'),
        ('session_open', 'الجلسة مفتوحة'),
        ('bidding',      'تسجيل العروض'),
        ('awarded',      'تم الترسية'),
        ('done',         'منتهي'),
        ('cancelled',    'ملغي'),
    ], default='draft', required=True, tracking=True, index=True)

    # ── Computed ──────────────────────────────────────────────────────────────
    @api.depends('bid_ids', 'bid_ids.amount', 'bid_ids.state')
    def _compute_bid_stats(self):
        for rec in self:
            valid_bids = rec.bid_ids.filtered(lambda b: b.state != 'rejected')
            rec.bid_count = len(valid_bids)
            rec.highest_bid = max(valid_bids.mapped('amount'), default=0.0)

    # ── SQL Constraints ───────────────────────────────────────────────────────
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'رقم المزاد يجب أن يكون فريداً'),
        ('estimated_value_pos', 'CHECK(estimated_value >= 0)', 'القيمة التقديرية يجب أن تكون موجبة'),
        ('initial_deposit_pos', 'CHECK(initial_deposit >= 0)', 'التأمين الابتدائي يجب أن يكون موجباً'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('auction.request') or '/'
        return super().create(vals_list)

    @api.onchange('auction_type')
    def _onchange_auction_type(self):
        if self.auction_type == 'lease':
            self.sale_type = False
            self.has_committee = True

    # ── State Transition Actions ──────────────────────────────────────────────
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('يمكن تأكيد المزادات في مرحلة المسودة فقط'))
            rec.write({'state': 'confirmed'})
            rec.message_post(body=_('✅ تم تأكيد طلب المزاد'))

    def action_open_session(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_('يجب تأكيد المزاد أولاً'))
            rec.write({'state': 'session_open'})
            rec.message_post(body=_('📢 تم فتح جلسة المزاد في %s') % rec.venue)

    def action_start_bidding(self):
        for rec in self:
            if rec.state != 'session_open':
                raise UserError(_('يجب فتح الجلسة أولاً'))
            rec.write({'state': 'bidding'})

    def action_award(self):
        """Award the auction — dispatch to sale or lease path."""
        for rec in self:
            if rec.state != 'bidding':
                raise UserError(_('يجب أن يكون المزاد في مرحلة تسجيل العروض'))
            accepted = rec.bid_ids.filtered(lambda b: b.state == 'accepted')
            if not accepted:
                raise UserError(_('يجب قبول عرض واحد على الأقل قبل الترسية'))
            if len(accepted) > 1:
                raise UserError(_('يجب أن يكون هناك عرض مقبول واحد فقط عند الترسية'))
            winning_bid = accepted[0]
            rec.write({
                'state': 'awarded',
                'awarded_bid_id': winning_bid.id,
                'awarded_partner_id': winning_bid.partner_id.id,
                'awarded_amount': winning_bid.amount,
                'award_notification_date': fields.Date.context_today(self),
            })
            rec.message_post(
                body=_('🏆 تم الترسية على: %s بمبلغ %.2f جنيه') % (
                    winning_bid.partner_id.name, winning_bid.amount
                )
            )
            # Dispatch to correct path
            if rec.auction_type == 'sale':
                rec._create_sale_order()
            else:
                rec._create_lease_contract()

    def _create_sale_order(self):
        """Path A: Sale → create confirmed sale.order."""
        self.ensure_one()
        if not self.product_id:
            raise UserError(_('يجب تحديد الصنف لإنشاء أمر البيع'))
        so_vals = {
            'partner_id': self.awarded_partner_id.id,
            'origin': self.name,
            'note': _('مزاد رقم: %s — %s') % (self.name, self.description or ''),
            'order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty': self.qty,
                'price_unit': self.awarded_amount,
                'name': self.product_id.name,
            })],
        }
        sale_order = self.env['sale.order'].create(so_vals)
        sale_order.action_confirm()
        self.sale_order_id = sale_order
        self.message_post(
            body=_('📋 تم إنشاء أمر البيع: %s') % sale_order.name
        )

    def _create_lease_contract(self):
        """Path B: Lease → create auction.lease.contract."""
        self.ensure_one()
        lease = self.env['auction.lease.contract'].create({
            'auction_request_id': self.id,
            'partner_id': self.awarded_partner_id.id,
            'contract_value': self.awarded_amount,
            'asset_description': self.asset_description or self.description,
            'start_date': fields.Date.context_today(self),
        })
        self.lease_contract_id = lease
        self.message_post(
            body=_('📄 تم إنشاء عقد الإيجار: %s') % lease.name
        )

    def action_done(self):
        for rec in self:
            if rec.state != 'awarded':
                raise UserError(_('يجب أن يكون المزاد في مرحلة الترسية'))
            rec.write({'state': 'done'})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('لا يمكن إلغاء مزاد منتهي'))
            rec.write({'state': 'cancelled'})

    def action_print_award(self):
        return self.env.ref('l10n_eg_auction.action_report_auction_award').report_action(self)
