from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ProcurementAdjudication(models.Model):
    """
    ملف المناقصة — Procurement Adjudication File (FR-P2, P3, P8)
    Dual-envelope state machine per Law 182/2018.
    States: draft → technical_open → financial_open → adjudicated → awarded → po_created
    """
    _name = 'procurement.adjudication'
    _description = 'البت الفني والمالي - Procurement Adjudication'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    # ── Identity ──────────────────────────────────────────────────────────────
    name = fields.Char(
        string='رقم ملف المناقصة', required=True, copy=False,
        readonly=True, default='/', tracking=True,
    )
    rfq_id = fields.Many2one(
        'purchase.order', string='طلب عروض الأسعار',
        domain="[('state','in',['draft','sent'])]",
        tracking=True, copy=False,
    )
    tender_type = fields.Selection([
        ('public',      'مناقصة عامة'),
        ('local',       'مناقصة محلية'),
        ('limited',     'مناقصة محدودة'),
        ('negotiation', 'ممارسة'),
    ], string='نوع المناقصة', required=True, default='public', tracking=True)
    date = fields.Date(
        string='تاريخ فتح الملف', required=True,
        default=fields.Date.context_today, tracking=True,
    )
    estimated_value = fields.Float(
        string='القيمة التقديرية للصفقة', digits='Account',
        tracking=True,
        help='Used in financial adjudication to compare against winning bid',
    )

    # ── Committee ─────────────────────────────────────────────────────────────
    technical_committee_id = fields.Many2one(
        'procurement.committee', string='لجنة البت الفني',
        domain="[('committee_type','=','technical')]", tracking=True,
    )
    financial_committee_id = fields.Many2one(
        'procurement.committee', string='لجنة البت المالي',
        domain="[('committee_type','=','financial')]", tracking=True,
    )
    opening_committee_id = fields.Many2one(
        'procurement.committee', string='لجنة فض المظاريف',
        domain="[('committee_type','=','opening')]", tracking=True,
    )

    # ── Supplier Lines ────────────────────────────────────────────────────────
    supplier_line_ids = fields.One2many(
        'adjudication.supplier.line', 'adjudication_id',
        string='الموردون المشاركون',
    )
    supplier_count = fields.Integer(
        compute='_compute_supplier_count', string='عدد الموردين',
    )

    # ── Technical Adjudication ────────────────────────────────────────────────
    technical_open_date = fields.Date(
        string='تاريخ فتح المظاريف الفنية', tracking=True,
    )
    technical_session_venue = fields.Char(
        string='مكان جلسة البت الفني', tracking=True,
    )
    technical_notes = fields.Text(
        string='نتيجة البت الفني العام', tracking=True,
    )

    # ── Financial Adjudication ────────────────────────────────────────────────
    financial_open_date = fields.Date(
        string='تاريخ فتح المظاريف المالية', tracking=True,
    )
    financial_session_venue = fields.Char(
        string='مكان جلسة البت المالي', tracking=True,
    )
    financial_notes = fields.Text(
        string='نتيجة البت المالي العام', tracking=True,
    )

    # ── Award ─────────────────────────────────────────────────────────────────
    awarded_supplier_id = fields.Many2one(
        'res.partner', string='المورد الفائز بالترسية',
        tracking=True, readonly=True,
    )
    awarded_amount = fields.Float(
        string='مبلغ الترسية', digits='Account',
        tracking=True, readonly=True,
    )
    award_notification_date = fields.Date(
        string='تاريخ إخطار الترسية', tracking=True,
    )
    purchase_order_id = fields.Many2one(
        'purchase.order', string='أمر الشراء الناتج',
        readonly=True, copy=False,
    )

    # ── State Machine ─────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',          'مسودة'),
        ('technical_open', 'فتح المظاريف الفنية'),
        ('financial_open', 'فتح المظاريف المالية'),
        ('adjudicated',    'تمت المقارنة المالية'),
        ('awarded',        'إخطار الترسية'),
        ('po_created',     'أمر شراء صادر'),
        ('cancelled',      'ملغي'),
    ], default='draft', required=True, tracking=True, index=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'رقم ملف المناقصة يجب أن يكون فريداً'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('procurement.adjudication') or '/'
        return super().create(vals_list)

    @api.depends('supplier_line_ids')
    def _compute_supplier_count(self):
        for rec in self:
            rec.supplier_count = len(rec.supplier_line_ids)

    # ── State Transitions ─────────────────────────────────────────────────────
    def action_open_technical(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('يجب أن يكون الملف في مرحلة المسودة'))
            if not rec.supplier_line_ids:
                raise UserError(_('يجب إضافة الموردين المشاركين أولاً'))
            rec.write({
                'state': 'technical_open',
                'technical_open_date': fields.Date.context_today(self),
            })
            rec.message_post(body=_('📂 تم فتح المظاريف الفنية في %s') % rec.technical_open_date)

    def action_open_financial(self):
        for rec in self:
            if rec.state != 'technical_open':
                raise UserError(_('يجب فتح المظاريف الفنية أولاً'))
            # At least one supplier must pass technical evaluation
            passed = rec.supplier_line_ids.filtered(
                lambda l: l.technical_result in ('pass', 'conditional')
            )
            if not passed:
                raise UserError(_('يجب أن يجتاز مورد واحد على الأقل تقييم البت الفني'))
            rec.write({
                'state': 'financial_open',
                'financial_open_date': fields.Date.context_today(self),
            })
            rec.message_post(body=_('💰 تم فتح المظاريف المالية في %s') % rec.financial_open_date)

    def action_adjudicate(self):
        """Compare financial offers and select winner."""
        for rec in self:
            if rec.state != 'financial_open':
                raise UserError(_('يجب فتح المظاريف المالية أولاً'))
            eligible = rec.supplier_line_ids.filtered(
                lambda l: l.technical_result in ('pass', 'conditional')
                and l.financial_bid > 0
            )
            if not eligible:
                raise UserError(_('لا توجد عروض مالية صالحة للمقارنة'))
            # Auto-select lowest bid as winner
            winner = min(eligible, key=lambda l: l.financial_bid)
            winner.write({'financial_result': 'accepted'})
            rec.write({
                'state': 'adjudicated',
                'awarded_supplier_id': winner.partner_id.id,
                'awarded_amount': winner.financial_bid,
            })
            rec.message_post(
                body=_('🏆 أقل عرض: %s بمبلغ %.2f جنيه (القيمة التقديرية: %.2f)') % (
                    winner.partner_id.name, winner.financial_bid, rec.estimated_value
                )
            )

    def action_award(self):
        if not self.env.user.has_group(
                'procurement_adjudication.group_adjudication_director'):
            from odoo.exceptions import AccessError
            raise AccessError('هذا الإجراء متاح لمدير التعاقدات فقط')
        for rec in self:
            if rec.state != 'adjudicated':
                raise UserError(_('يجب إتمام المقارنة المالية أولاً'))
            rec.write({
                'state': 'awarded',
                'award_notification_date': fields.Date.context_today(self),
            })
            rec.message_post(
                body=_('📬 تم إخطار الترسية: %s — مبلغ %.2f جنيه') % (
                    rec.awarded_supplier_id.name, rec.awarded_amount
                )
            )

    def action_create_po(self):
        """Convert adjudication to purchase.order."""
        for rec in self:
            if rec.state != 'awarded':
                raise UserError(_('يجب الانتهاء من إخطار الترسية أولاً'))
            po = self.env['purchase.order'].create({
                'partner_id': rec.awarded_supplier_id.id,
                'origin': rec.name,
                'notes': _('أمر توريد ناتج عن مناقصة رقم: %s') % rec.name,
            })
            rec.write({'state': 'po_created', 'purchase_order_id': po.id})
            rec.message_post(body=_('📋 تم إنشاء أمر التوريد: %s') % po.name)

    def action_cancel(self):
        for rec in self:
            if rec.state == 'po_created':
                raise UserError(_('لا يمكن إلغاء مناقصة صدر عنها أمر توريد'))
            rec.write({'state': 'cancelled'})



    def action_print_commitment_form(self):
        return self.env.ref('procurement_adjudication.action_report_commitment_form').report_action(self)

    def action_print_social_insurance(self):
        return self.env.ref('procurement_adjudication.action_report_social_insurance').report_action(self)

    def action_print_labor_office(self):
        return self.env.ref('procurement_adjudication.action_report_labor_office').report_action(self)

    def action_view_suppliers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('موردو المناقصة: %s') % self.name,
            'res_model': 'adjudication.supplier.line',
            'view_mode': 'tree',
            'domain': [('adjudication_id', '=', self.id)],
        }

    def action_view_po(self):
        self.ensure_one()
        if not self.purchase_order_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
        }

    def action_print_tender_ad(self):
        return self.env.ref('procurement_adjudication.action_report_tender_ad').report_action(self)

    def action_print_vendors_list(self):
        return self.env.ref('procurement_adjudication.action_report_vendors_list').report_action(self)

    def action_print_technical_minutes(self):
        return self.env.ref('procurement_adjudication.action_report_technical_minutes').report_action(self)

    def action_print_financial_minutes(self):
        return self.env.ref('procurement_adjudication.action_report_financial_minutes').report_action(self)

    def action_print_award_notification(self):
        return self.env.ref('procurement_adjudication.action_report_award_notification').report_action(self)


class AdjudicationSupplierLine(models.Model):
    """سطر المورد في ملف المناقصة"""
    _name = 'adjudication.supplier.line'
    _description = 'مورد في ملف المناقصة'
    _order = 'financial_bid asc'

    adjudication_id = fields.Many2one(
        'procurement.adjudication', string='ملف المناقصة',
        required=True, ondelete='cascade', index=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='المورد', required=True,
    )
    # Technical Evaluation
    technical_result = fields.Selection([
        ('pending',     'قيد التقييم'),
        ('pass',        'مطابق للشروط ✓'),
        ('conditional', 'مطابق مع تحفظ'),
        ('fail',        'غير مطابق ✗'),
    ], string='نتيجة البت الفني', default='pending', tracking=True)
    technical_notes = fields.Text(string='ملاحظات البت الفني')
    compliance_form = fields.Boolean(
        string='نموذج استيفاء الشروط',
        help='نموذج إستيفاء الشروط والمواصفات',
    )
    # Financial Evaluation
    financial_bid = fields.Float(
        string='العرض المالي (جنيه)', digits='Account',
    )
    financial_result = fields.Selection([
        ('pending',  'قيد المقارنة'),
        ('accepted', 'فائز بالترسية ✓'),
        ('rejected', 'مرفوض'),
    ], string='نتيجة البت المالي', default='pending', tracking=True)
    financial_notes = fields.Text(string='ملاحظات البت المالي')

    bid_vs_estimate = fields.Float(
        string='نسبة العرض من التقديري (%)',
        compute='_compute_bid_ratio', store=True,
    )

    _sql_constraints = [
        ('partner_adj_uniq', 'unique(adjudication_id, partner_id)',
         'لا يمكن إضافة نفس المورد مرتين في ملف المناقصة'),
        ('bid_positive', 'CHECK(financial_bid >= 0)', 'العرض المالي يجب أن يكون موجباً'),
    ]

    @api.depends('financial_bid', 'adjudication_id.estimated_value')
    def _compute_bid_ratio(self):
        for line in self:
            est = line.adjudication_id.estimated_value
            line.bid_vs_estimate = (line.financial_bid / est * 100.0) if est > 0 else 0.0
