# -*- coding: utf-8 -*-
"""
تعريف الدفتر المساعد (Book Definition)
======================================

سجل واحد لكل دفتر قانوني من الدفاتر الثمانية. يحدد:
- التصنيف (جارية/نظامية)
- الجانب (مدين/دائن)
- النطاق (مفردات/إجمالي)
- النموذج (29/39/71/78 وما إلى ذلك)
- قواعد الفلترة على account.move.line
- قالب الطباعة المستخدم
- التسلسل القانوني
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SubsidiaryBookDefinition(models.Model):
    _name = 'port_said.subsidiary.book'
    _description = 'تعريف دفتر مساعد حكومي'
    _order = 'sequence, code'
    _inherit = ['mail.thread']

    # ── المعرفات القانونية ────────────────────────────────────────────────────
    name = fields.Char(string='اسم الدفتر', required=True, translate=False,
                       help='الاسم الرسمي حسب وزارة المالية، مثلاً: '
                            'دفتر مفردات الحسابات الجارية المدينة')
    code = fields.Char(string='الكود الفني', required=True, index=True,
                       help='كود فريد للدفتر، مثلاً: SUB_CUR_DR_DETAIL')
    form_number = fields.Char(string='رقم النموذج', required=True,
                              help='رقم الاستمارة الرسمية، مثلاً: 39 ع.ح، 71 مكرر ع.ح')
    sequence = fields.Integer(string='ترتيب العرض', default=10)

    # ── أبعاد التصنيف الثلاثة ─────────────────────────────────────────────────
    account_class = fields.Selection([
        ('current', 'حسابات جارية (Current)'),
        ('memo',    'حسابات نظامية (Memorandum / Off-Balance)'),
        ('personal', 'حسابات شخصية (Personal — Form 29)'),
    ], string='تصنيف الحساب', required=True, index=True)

    side = fields.Selection([
        ('debit',  'مدينة (Debit)'),
        ('credit', 'دائنة (Credit)'),
        ('both',   'ذو الخانتين (Two-sided)'),
    ], string='الجانب', required=True, index=True)

    scope = fields.Selection([
        ('detail',  'مفردات (Detail – per partner/account)'),
        ('totals',  'إجمالي (Totals – per account)'),
        ('personal','الشخصية ذو الخانتين (Personal Two-sided Folio)'),
    ], string='النطاق', required=True, index=True)

    # ── قواعد الفلترة على account.move.line ──────────────────────────────────
    account_classification_ids = fields.Many2many(
        'port_said.subsidiary.account.classification',
        'sub_book_classif_rel',
        string='تصنيفات الحسابات المؤهلة',
        help='التصنيفات التي تنتمي إليها الحسابات الظاهرة في هذا الدفتر. '
             'يستخدم لفلترة account.move.line.account_id حسب '
             'حقل x_subsidiary_classification_id على account.account.')

    journal_ids = fields.Many2many(
        'account.journal', string='اليوميات المؤهلة',
        help='اختياري: قصر القراءة على يوميات بعينها. '
             'الافتراضي: كل اليوميات المرحّلة.')

    include_unposted = fields.Boolean(
        string='شمل غير المرحّل', default=False,
        help='عادةً = False: الدفاتر القانونية تقرأ فقط من state=posted. '
             'فعّل عند تجارب التحقق فقط.')

    grouping_key = fields.Selection([
        ('partner', 'شريك (مورد/عميل/موظف/مستفيد)'),
        ('account', 'حساب (account.account)'),
        ('partner_account', 'شريك + حساب'),
    ], string='مفتاح التجميع', required=True, default='partner',
       help='يحدد كيف ينقسم الدفتر إلى فوليوهات. '
            'الشخصية = partner، الإجمالي = account، التفصيلي = partner_account')

    # ── الطباعة ──────────────────────────────────────────────────────────────
    print_template = fields.Selection([
        ('detail',   'قالب التفصيلي (مفردات)'),
        ('totals',   'قالب الإجمالي (Trial-balance like)'),
        ('personal', 'قالب الشخصية ذو الخانتين (وجهان متقابلان)'),
    ], string='قالب الطباعة', required=True, default='detail')

    columns_layout = fields.Selection([
        ('single_amount',     'عمود مبلغ واحد'),
        ('debit_credit',      'عمودان: مدين / دائن'),
        ('multi_deduction',   'متعدد الأعمدة (تحليل الاستقطاعات: ضرائب/إيجار/أتعاب…)'),
    ], string='تخطيط الأعمدة', required=True, default='single_amount')

    # ── التسلسل القانوني ─────────────────────────────────────────────────────
    sequence_id = fields.Many2one(
        'ir.sequence', string='التسلسل القانوني',
        help='تسلسل خاص بالدفتر يعيد التشغيل في 1 يوليو من كل سنة مالية. '
             'يُولَّد تلقائياً عند الإنشاء إذا تُرك فارغاً.')

    folio_size = fields.Integer(
        string='عدد السطور بالفولية', default=25,
        help='عدد سطور الترحيل في كل صفحة قانونية. '
             'القيمة الافتراضية = 25 (مطابقة للنموذج الورقي).')

    # ── الحالة والتفعيل ──────────────────────────────────────────────────────
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    notes = fields.Text(string='ملاحظات قانونية')

    # ── إحصائيات للمراقبة ────────────────────────────────────────────────────
    folio_count = fields.Integer(string='عدد الفوليوهات المُولَّدة',
                                  compute='_compute_folio_count')

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code, company_id)',
         'كود الدفتر يجب أن يكون فريداً داخل الشركة الواحدة.'),
    ]

    @api.constrains('account_class', 'side', 'scope')
    def _check_consistent_combination(self):
        """قواعد الاتساق بين الأبعاد الثلاثة."""
        for rec in self:
            # الشخصية يجب أن تكون دائماً ذو خانتين
            if rec.account_class == 'personal' and rec.side != 'both':
                raise ValidationError(_(
                    'دفتر الحسابات الشخصية (Form 29) يجب أن يكون "ذو الخانتين". '
                    'لا يجوز أن يكون مديناً فقط أو دائناً فقط.'))
            if rec.account_class == 'personal' and rec.scope != 'personal':
                raise ValidationError(_(
                    'دفتر الحسابات الشخصية يجب أن يكون نطاقه = personal.'))
            # الإجمالي يكون دائماً جانباً واحداً (لا "both")
            if rec.scope == 'totals' and rec.side == 'both':
                raise ValidationError(_(
                    'دفتر الإجمالي لا يمكن أن يكون ذو الخانتين. '
                    'حدد جانباً واحداً (مدين أو دائن).'))

    def _compute_folio_count(self):
        Folio = self.env['port_said.subsidiary.folio']
        for rec in self:
            rec.folio_count = Folio.search_count([('book_id', '=', rec.id)])

    # ── إجراءات ──────────────────────────────────────────────────────────────
    def action_open_folios(self):
        """فتح كل الفوليوهات المنتمية لهذا الدفتر."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('فوليوهات: %s') % self.name,
            'res_model': 'port_said.subsidiary.folio',
            'view_mode': 'list,form',
            'domain': [('book_id', '=', self.id)],
            'context': {'default_book_id': self.id},
        }

    def action_print_book(self):
        """فتح ساحر الطباعة لهذا الدفتر."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('طباعة: %s') % self.name,
            'res_model': 'port_said.subsidiary.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_book_id': self.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        """إنشاء تسلسل قانوني تلقائي لكل دفتر جديد."""
        recs = super().create(vals_list)
        for rec in recs:
            if not rec.sequence_id:
                rec.sequence_id = self.env['ir.sequence'].create({
                    'name': _('تسلسل %s') % rec.name,
                    'code': 'port_said.subsidiary.book.%s' % rec.code.lower(),
                    'prefix': '%s/%%(year)s/' % rec.form_number.split()[0],
                    'padding': 4,
                    'use_date_range': True,
                    'company_id': rec.company_id.id,
                }).id
                # إنشاء نطاق للسنة المالية الجارية (1 يوليو – 30 يونيو)
                rec._create_fy_range_for_sequence()
        return recs

    def _create_fy_range_for_sequence(self):
        """يُنشئ نطاق ir.sequence.date_range للسنة المالية الجارية."""
        self.ensure_one()
        from datetime import date
        today = fields.Date.today()
        if today.month >= 7:
            fy_start = date(today.year, 7, 1)
            fy_end = date(today.year + 1, 6, 30)
        else:
            fy_start = date(today.year - 1, 7, 1)
            fy_end = date(today.year, 6, 30)
        self.env['ir.sequence.date_range'].create({
            'sequence_id': self.sequence_id.id,
            'date_from': fy_start,
            'date_to': fy_end,
            'number_next': 1,
        })

    def name_get(self):
        return [(rec.id, '%s — %s' % (rec.form_number, rec.name)) for rec in self]
