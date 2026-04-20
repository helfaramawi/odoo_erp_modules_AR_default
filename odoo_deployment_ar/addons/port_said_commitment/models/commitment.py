from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BudgetCommitment(models.Model):
    """
    نموذج الارتباط — دفتر الارتباطات
    Workflow: draft → submitted → approved → reserved → cleared → paid → cancelled
    لا يعتمد على account_budget — يستخدم رصيد الموازنة من الإدخال المباشر
    """
    _name = 'port_said.commitment'
    _description = 'نموذج الارتباط (دفتر الارتباطات)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'commitment_number desc'
    _rec_name = 'commitment_number'

    commitment_number  = fields.Char(string='رقم الارتباط', readonly=True, copy=False, index=True)
    fiscal_year        = fields.Integer(string='السنة المالية', required=True,
                                        default=lambda s: fields.Date.today().year)
    date_requested     = fields.Date(string='تاريخ الطلب', default=fields.Date.today, required=True)
    department_id      = fields.Many2one('res.partner', string='الإدارة الطالبة', required=True)
    description        = fields.Text(string='وصف الاحتياج', required=True)

    # بيانات الموازنة (بدون account_budget)
    budget_line_code   = fields.Char(string='رمز البند (باب/بند/نوع)', required=True)
    budget_approved    = fields.Monetary(string='الاعتماد المالي المُقرَّر',
                                         currency_field='currency_id',
                                         help='إجمالي الاعتماد المالي للبند من الموازنة المعتمدة')
    budget_consumed    = fields.Monetary(string='المُنصرَف حتى الآن',
                                         compute='_compute_consumed', store=True,
                                         currency_field='currency_id')
    available_balance  = fields.Monetary(string='الرصيد المتاح',
                                          compute='_compute_consumed', store=True,
                                          currency_field='currency_id')
    amount_requested   = fields.Monetary(string='المبلغ المطلوب', required=True,
                                          currency_field='currency_id')
    currency_id        = fields.Many2one('res.currency',
                                          default=lambda s: s.env.company.currency_id)

    state = fields.Selection([
        ('draft',     'مسودة'),
        ('submitted', 'مُقدَّم'),
        ('approved',  'ارتباط معتمد'),
        ('reserved',  'تجنيب — محجوز'),
        ('cleared',   'تسميح — مُسمَّح'),
        ('paid',      'صُرف'),
        ('cancelled', 'ملغي'),
    ], string='حالة الارتباط', default='draft', tracking=True)

    approved_by   = fields.Many2one('res.users', string='اعتمد بواسطة', readonly=True)
    approved_date = fields.Date(string='تاريخ الاعتماد', readonly=True)
    cleared_by    = fields.Many2one('res.users', string='سمَّح بواسطة', readonly=True)
    cleared_date  = fields.Date(string='تاريخ التسميح', readonly=True)

    # daftar55_ids removed — search daftar55 by commitment_ref instead
    company_id    = fields.Many2one('res.company', default=lambda s: s.env.company)
    notes         = fields.Text(string='ملاحظات')

    @api.depends('budget_approved')
    def _compute_consumed(self):
        """Compute consumed budget by searching daftar55 records linked via commitment_ref."""
        for rec in self:
            if rec.commitment_number:
                D55 = self.env['port_said.daftar55']
                posted = D55.search([
                    ('commitment_ref', '=', rec.commitment_number),
                    ('state', 'in', ('posted', 'archived')),
                ])
                consumed = sum(posted.mapped('amount_gross'))
            else:
                consumed = 0.0
            rec.budget_consumed   = consumed
            rec.available_balance = rec.budget_approved - consumed

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('commitment_number'):
                vals['commitment_number'] = (
                    self.env['ir.sequence'].next_by_code('port_said.commitment') or '/')
        return super().create(vals_list)

    def _check_budget(self):
        for rec in self:
            if rec.budget_approved > 0 and rec.amount_requested > rec.available_balance:
                raise ValidationError(_(
                    'تعذّر الارتباط: المبلغ المطلوب (%(req)s) يتجاوز الرصيد المتاح (%(avail)s) '
                    'في البند %(line)s.',
                    req=rec.amount_requested,
                    avail=rec.available_balance,
                    line=rec.budget_line_code,
                ))

    def action_submit(self):
        self._check_budget()
        self.write({'state': 'submitted'})

    def action_approve(self):
        self._check_budget()
        self.write({
            'state':        'approved',
            'approved_by':  self.env.uid,
            'approved_date': fields.Date.today(),
        })
        self.message_post(body=_('✅ ارتباط معتمد — %s') % self.env.user.name)

    def action_reserve(self):
        if self.state != 'approved':
            raise UserError(_('يجب اعتماد الارتباط أولاً قبل التجنيب.'))
        self.write({'state': 'reserved'})
        self.message_post(body=_('🔒 تجنيب — تم حجز المبلغ على البند'))

    def action_clear(self):
        if self.state != 'reserved':
            raise UserError(_('يجب إتمام التجنيب أولاً قبل التسميح.'))
        self.write({
            'state':       'cleared',
            'cleared_by':  self.env.uid,
            'cleared_date': fields.Date.today(),
        })
        self.message_post(body=_('✅ تسميح البند — يمكن إصدار أمر الدفع'))

    def action_mark_paid(self):
        if self.state != 'cleared':
            raise UserError(_('يجب التسميح أولاً قبل تسجيل الصرف.'))
        self.write({'state': 'paid'})

    def action_cancel(self):
        if self.state == 'paid':
            raise UserError(_('لا يمكن إلغاء ارتباط مصروف.'))
        self.write({'state': 'cancelled'})

    def action_print_commitment(self):
        return self.env.ref('port_said_commitment.action_report_commitment').report_action(self)
