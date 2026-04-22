from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Form75Closing(models.Model):
    """
    استمارة 75 ع.ح - الحسابات الشهرية / الربع سنوية / الختامية
    CRITICAL: 3-stage SEQUENTIAL approval — لائحة المالية المصرية
      Stage 1: مراقب الحسابات  (Account Auditor)
      Stage 2: مدير الحسابات   (Accounts Manager) — blocked until stage 1
      Stage 3: رئيس المصلحة   (Department Head)   — blocked until stage 2
    """
    _name = 'port_said.form75'
    _description = 'استمارة 75 ع.ح - الحسابات الشهرية والختامية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fiscal_year desc, fiscal_period desc'
    _rec_name = 'display_name'

    display_name = fields.Char(compute='_compute_display_name', store=True)

    period_type  = fields.Selection([
        ('monthly',   'شهرية'),
        ('quarterly', 'ربع سنوية'),
        ('annual',    'ختامية سنوية'),
    ], string='نوع الفترة', required=True, default='monthly')
    fiscal_year   = fields.Integer(string='السنة المالية', required=True, default=lambda s: fields.Date.today().year)
    fiscal_period = fields.Integer(string='الشهر / الربع', required=True)

    opening_balance  = fields.Monetary(string='الرصيد الافتتاحي للفترة', currency_field='currency_id')
    total_sarfiyat   = fields.Monetary(string='إجمالي الصرفيات', currency_field='currency_id')
    total_taswiyat   = fields.Monetary(string='إجمالي التسويات', currency_field='currency_id')
    closing_balance  = fields.Monetary(
        string='الرصيد الختامي',
        compute='_compute_closing', store=True,
        currency_field='currency_id',
    )
    currency_id      = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    company_id       = fields.Many2one('res.company', default=lambda s: s.env.company)
    form69_ids       = fields.Many2many('port_said.form69', string='الحسبة اليومية المُدرجة')
    notes            = fields.Text(string='ملاحظات')

    # ── 3-STAGE SEQUENTIAL APPROVAL ───────────────────────────────────────
    state = fields.Selection([
        ('draft',             'مسودة'),
        ('submitted',         'مُقدَّم للاعتماد'),
        ('stage1_approved',   'اعتمد: مراقب الحسابات'),
        ('stage2_approved',   'اعتمد: مدير الحسابات'),
        ('approved',          'مُعتمد نهائياً'),
        ('rejected',          'مرفوض'),
    ], string='حالة الاعتماد', default='draft', tracking=True)

    # Stage 1 — مراقب الحسابات
    stage1_user_id   = fields.Many2one('res.users', string='مراقب الحسابات')
    stage1_date      = fields.Datetime(string='تاريخ توقيع المراقب', readonly=True)
    stage1_note      = fields.Text(string='ملاحظة المراقب')

    # Stage 2 — مدير الحسابات
    stage2_user_id   = fields.Many2one('res.users', string='مدير الحسابات')
    stage2_date      = fields.Datetime(string='تاريخ توقيع المدير', readonly=True)
    stage2_note      = fields.Text(string='ملاحظة مدير الحسابات')

    # Stage 3 — رئيس المصلحة
    stage3_user_id   = fields.Many2one('res.users', string='رئيس المصلحة')
    stage3_date      = fields.Datetime(string='تاريخ توقيع الرئيس', readonly=True)
    stage3_note      = fields.Text(string='ملاحظة رئيس المصلحة')

    rejection_reason = fields.Text(string='سبب الرفض')

    @api.depends('fiscal_year', 'fiscal_period', 'period_type')
    def _compute_display_name(self):
        labels = {'monthly': 'شهرية', 'quarterly': 'ربع سنوية', 'annual': 'ختامية'}
        for rec in self:
            rec.display_name = f"75/{rec.fiscal_year}/{rec.fiscal_period} ({labels.get(rec.period_type,'')})"

    @api.depends('opening_balance', 'total_sarfiyat', 'total_taswiyat')
    def _compute_closing(self):
        for rec in self:
            rec.closing_balance = rec.opening_balance + rec.total_sarfiyat - rec.total_taswiyat

    # ── Workflow actions ───────────────────────────────────────────────────
    def action_submit(self):
        self.write({'state': 'submitted'})
        self.message_post(body=_('تم تقديم الاستمارة للاعتماد'))

    def action_approve_stage1(self):
        """مراقب الحسابات approval — Stage 1."""
        if self.state != 'submitted':
            raise UserError(_('يجب تقديم الاستمارة أولاً قبل اعتماد المرحلة الأولى.'))
        self.write({
            'state': 'stage1_approved',
            'stage1_user_id': self.env.uid,
            'stage1_date': fields.Datetime.now(),
        })
        self.message_post(body=_('✅ المرحلة الأولى: اعتمد مراقب الحسابات - %s') % self.env.user.name)

    def action_approve_stage2(self):
        """مدير الحسابات approval — Stage 2. BLOCKED until Stage 1."""
        if self.state != 'stage1_approved':
            raise UserError(_(
                'لا يمكن اعتماد المرحلة الثانية قبل اعتماد مراقب الحسابات. '
                'هذا شرط قانوني بموجب لائحة المالية.'
            ))
        self.write({
            'state': 'stage2_approved',
            'stage2_user_id': self.env.uid,
            'stage2_date': fields.Datetime.now(),
        })
        self.message_post(body=_('✅ المرحلة الثانية: اعتمد مدير الحسابات - %s') % self.env.user.name)

    def action_approve_stage3(self):
        """رئيس المصلحة approval — Stage 3. BLOCKED until Stage 2."""
        if self.state != 'stage2_approved':
            raise UserError(_(
                'لا يمكن اعتماد المرحلة الثالثة قبل اعتماد مدير الحسابات. '
                'هذا شرط قانوني بموجب لائحة المالية.'
            ))
        self.write({
            'state': 'approved',
            'stage3_user_id': self.env.uid,
            'stage3_date': fields.Datetime.now(),
        })
        self.message_post(body=_('✅ مُعتمد نهائياً — رئيس المصلحة: %s') % self.env.user.name)

    def action_reject(self):
        if not self.rejection_reason:
            raise UserError(_('يجب إدخال سبب الرفض.'))
        # Rejection sends back to previous stage
        prev_states = {
            'submitted': 'draft',
            'stage1_approved': 'submitted',
            'stage2_approved': 'stage1_approved',
        }
        prev = prev_states.get(self.state, 'draft')
        self.write({'state': prev})
        self.message_post(body=_('❌ مرفوض — السبب: %s') % self.rejection_reason)

    def action_print(self):
        return self.env.ref('port_said_form75.action_report_form75').report_action(self)

    @api.model
    def build_from_form69(self, fiscal_year, fiscal_period, period_type='monthly'):
        """Auto-build Form 75 by aggregating Form 69 records for the period."""
        domain = [('fiscal_year', '=', fiscal_year), ('fiscal_month', '=', fiscal_period)]
        f69_recs = self.env['port_said.form69'].search(domain)
        if not f69_recs:
            raise UserError(_('لا توجد حسبة يومية للفترة المحددة.'))
        prev = self.search([
            ('fiscal_year', '=', fiscal_year),
            ('fiscal_period', '<', fiscal_period),
            ('state', '=', 'approved'),
        ], order='fiscal_period desc', limit=1)
        return self.create({
            'period_type':     period_type,
            'fiscal_year':     fiscal_year,
            'fiscal_period':   fiscal_period,
            'opening_balance': prev.closing_balance if prev else 0.0,
            'total_sarfiyat':  sum(f69_recs.mapped('sarfiyat_total')),
            'total_taswiyat':  sum(f69_recs.mapped('taswiyat_total')),
            'form69_ids':      [(6, 0, f69_recs.ids)],
        })
