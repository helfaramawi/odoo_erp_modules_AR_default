from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class AuctionLeaseContract(models.Model):
    _name = 'auction.lease.contract'
    _description = 'عقد إيجار مزاد - Auction Lease Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(string='رقم العقد', required=True, copy=False, readonly=True, default='/')
    auction_request_id = fields.Many2one('auction.request', string='طلب المزاد', ondelete='set null', tracking=True)
    partner_id = fields.Many2one('res.partner', string='المتعاقد', required=True, tracking=True)
    asset_description = fields.Char(string='وصف الأصل', tracking=True)
    start_date = fields.Date(string='تاريخ البداية', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string='تاريخ الانتهاء', tracking=True)
    duration_years = fields.Integer(string='مدة العقد بالسنوات', compute='_compute_dates', store=True)
    grace_period_months = fields.Integer(string='فترة السماح بالشهور', default=0)
    effective_start_date = fields.Date(string='بداية السريان الفعلية', compute='_compute_dates', store=True)

    contract_value = fields.Float(string='القيمة السنوية', required=True, digits='Account', tracking=True)
    annual_increase_pct = fields.Float(string='نسبة الزيادة السنوية', digits=(16, 2), default=10.0)
    payment_frequency = fields.Selection([
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('biannual', 'نصف سنوي'),
        ('annual', 'سنوي'),
    ], string='دورية الدفع', required=True, default='annual')
    initial_deposit = fields.Float(string='التأمين الابتدائي', digits='Account', default=0.0)
    insurance_pct = fields.Float(string='نسبة التأمين النهائي', digits=(16, 2), default=10.0)
    insurance_amount = fields.Float(string='قيمة التأمين النهائي', compute='_compute_totals', store=True, digits='Account')
    total_expected = fields.Float(string='إجمالي المستحق', compute='_compute_totals', store=True, digits='Account')
    total_collected = fields.Float(string='إجمالي المحصل', compute='_compute_totals', store=True, digits='Account')
    total_outstanding = fields.Float(string='إجمالي المتبقي', compute='_compute_totals', store=True, digits='Account')

    payment_schedule_ids = fields.One2many('payment.schedule.line', 'lease_contract_id', string='جدول الدفعات')
    notes = fields.Text(string='ملاحظات')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('active', 'ساري'),
        ('expired', 'منتهي'),
    ], string='الحالة', default='draft', tracking=True)

    _sql_constraints = [
        ('contract_value_positive', 'CHECK(contract_value >= 0)', 'قيمة العقد يجب ألا تكون سالبة'),
        ('insurance_pct_positive', 'CHECK(insurance_pct >= 0)', 'نسبة التأمين يجب ألا تكون سالبة'),
        ('grace_period_non_negative', 'CHECK(grace_period_months >= 0)', 'فترة السماح يجب ألا تكون سالبة'),
    ]

    @api.depends('start_date', 'end_date', 'grace_period_months')
    def _compute_dates(self):
        for rec in self:
            rec.effective_start_date = rec.start_date + relativedelta(months=rec.grace_period_months) if rec.start_date else False
            if rec.start_date and rec.end_date and rec.end_date >= rec.start_date:
                months = (rec.end_date.year - rec.start_date.year) * 12 + (rec.end_date.month - rec.start_date.month)
                rec.duration_years = max(1, (months + 11) // 12)
            else:
                rec.duration_years = 0

    @api.depends('contract_value', 'insurance_pct', 'payment_schedule_ids.amount', 'payment_schedule_ids.amount_paid')
    def _compute_totals(self):
        for rec in self:
            rec.insurance_amount = rec.contract_value * (rec.insurance_pct / 100.0)
            rec.total_expected = sum(rec.payment_schedule_ids.mapped('amount')) or rec.contract_value
            rec.total_collected = sum(rec.payment_schedule_ids.mapped('amount_paid'))
            rec.total_outstanding = rec.total_expected - rec.total_collected

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('auction.lease.contract') or '/'
        return super().create(vals_list)

    def _get_period_months(self):
        self.ensure_one()
        return {
            'monthly': 1,
            'quarterly': 3,
            'biannual': 6,
            'annual': 12,
        }[self.payment_frequency]

    def action_generate_schedule(self):
        for rec in self:
            if not rec.start_date:
                raise UserError(_('يجب تحديد تاريخ البداية أولاً'))
            rec.payment_schedule_ids.unlink()
            period_months = rec._get_period_months()
            effective_date = rec.effective_start_date or rec.start_date
            total_months = 12
            if rec.end_date and rec.end_date >= rec.start_date:
                total_months = max(1, (rec.end_date.year - rec.start_date.year) * 12 + (rec.end_date.month - rec.start_date.month) + 1)
            installments = max(1, (total_months + period_months - 1) // period_months)
            installment_amount = rec.contract_value / max(1, 12 // period_months) if period_months < 12 else rec.contract_value

            lines = []
            for i in range(installments):
                due_date = effective_date + relativedelta(months=period_months * i)
                year_number = i // max(1, 12 // period_months) + 1
                annual_factor = (1 + (rec.annual_increase_pct / 100.0)) ** (year_number - 1)
                lines.append((0, 0, {
                    'installment_number': i + 1,
                    'year_number': year_number,
                    'due_date': due_date,
                    'amount': installment_amount * annual_factor,
                }))
            rec.write({'payment_schedule_ids': lines})

    def action_activate(self):
        for rec in self:
            if not rec.payment_schedule_ids:
                rec.action_generate_schedule()
            rec.state = 'active'

    def action_expire(self):
        self.write({'state': 'expired'})

    def action_print_contract(self):
        return self.env.ref('l10n_eg_auction.action_report_lease_contract').report_action(self)
