from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Daftar224(models.Model):
    """
    دفتر 224 ع.ح — السجل اليومي المزدوج
    ينشئ قيدَين من نفس المعاملة:
      - صرفيات: القيد الإجمالي (from ح/البند → to ح/دائنة + ح/أوامر الدفع)
      - تسويات: القيود التفصيلية الإفرادية لكل استقطاع على حدة
    المصدر: وثيقة إجراءات استمارة 50 ص.4-5
    """
    _name = 'port_said.daftar224'
    _description = 'دفتر 224 ع.ح — السجل اليومي المزدوج'
    _order = 'entry_date desc, register_type, sequence_in_day'
    _rec_name = 'display_name'

    display_name    = fields.Char(compute='_compute_display_name', store=True)
    entry_date      = fields.Date(string='تاريخ القيد', required=True, default=fields.Date.today, index=True)
    register_type   = fields.Selection([
        ('sarfiyat',  'صرفيات — قيد إجمالي'),
        ('taswiyat',  'تسويات — قيود إفرادية'),
    ], string='نوع السجل', required=True)
    sequence_in_day = fields.Integer(string='تسلسل اليوم', default=1)

    daftar55_id = fields.Many2one('port_said.daftar55', string='مرجع دفتر 55', ondelete='restrict', index=True)
    form50_ref  = fields.Char(string='رقم استمارة 50', related='daftar55_id.form50_ref', store=True)
    vendor_id   = fields.Many2one('res.partner', string='صاحب الحق', related='daftar55_id.vendor_id', store=True)
    budget_line = fields.Char(string='البند', related='daftar55_id.budget_line', store=True)

    # حسابات دفتر الأستاذ
    account_debit_id   = fields.Many2one('account.account', string='حـ/ مدين (البند)')
    account_credit1_id = fields.Many2one('account.account', string='حـ/ دائن 1 (حسابات جارية دائنة)')
    account_credit2_id = fields.Many2one('account.account', string='حـ/ دائن 2 (أوامر الدفع)')

    # المبالغ (من دفتر 55)
    amount_gross      = fields.Monetary(related='daftar55_id.amount_gross', store=True, currency_field='currency_id')
    amount_deductions = fields.Monetary(related='daftar55_id.total_deductions', store=True, currency_field='currency_id')
    amount_net        = fields.Monetary(related='daftar55_id.amount_net', store=True, currency_field='currency_id')

    # قيود إفرادية التفصيلية (للتسويات فقط)
    detail_stamp_normal       = fields.Monetary(string='ح/ الدمغة العادية', related='daftar55_id.deductions_stamp_normal', store=True, currency_field='currency_id')
    detail_stamp_extra        = fields.Monetary(string='ح/ الدمغة الإضافية', related='daftar55_id.deductions_stamp_extra', store=True, currency_field='currency_id')
    detail_stamp_proportional = fields.Monetary(string='ح/ الدمغة النسبية', related='daftar55_id.deductions_stamp_proportional', store=True, currency_field='currency_id')
    detail_commercial_tax     = fields.Monetary(string='ح/ ضريبة الأرباح التجارية', related='daftar55_id.deductions_commercial_tax', store=True, currency_field='currency_id')

    # توقيع الشطب
    crossout_signed    = fields.Boolean(string='وُقِّع موظفو الشطب')
    crossout_signed_by = fields.Char(string='موظف الشطب')

    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    notes       = fields.Text(string='ملاحظات')
    move_id     = fields.Many2one('account.move', string='قيد دفتر الأستاذ')
    company_id  = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.depends('entry_date', 'register_type', 'sequence_in_day')
    def _compute_display_name(self):
        labels = {'sarfiyat': 'صرفيات', 'taswiyat': 'تسويات'}
        for rec in self:
            rec.display_name = f"224/{rec.entry_date}/{labels.get(rec.register_type,'')}/{rec.sequence_in_day}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            date  = vals.get('entry_date', fields.Date.today())
            rtype = vals.get('register_type', 'sarfiyat')
            count = self.search_count([('entry_date', '=', date), ('register_type', '=', rtype)])
            vals['sequence_in_day'] = count + 1
        return super().create(vals_list)

    def unlink(self):
        raise UserError(_('لا يمكن حذف سجلات دفتر 224 ع.ح بعد الإنشاء.'))

    @api.model
    def get_daily_totals(self, date):
        sarfiyat = self.search([('entry_date', '=', date), ('register_type', '=', 'sarfiyat')])
        taswiyat = self.search([('entry_date', '=', date), ('register_type', '=', 'taswiyat')])
        return {
            'date': date,
            'sarfiyat_total': sum(sarfiyat.mapped('amount_gross')),
            'taswiyat_total': sum(taswiyat.mapped('amount_net')),
            'sarfiyat_count': len(sarfiyat),
            'taswiyat_count': len(taswiyat),
        }

    @api.model
    def create_dual_entry_from_daftar55(self, daftar55_id):
        """
        ينشئ القيدَين (إجمالي + تفصيلي إفرادي) من معاملة دفتر 55 واحدة.
        المصدر: وثيقة إجراءات استمارة 50 ص.4-5
        الإجمالي:
          من ح/البند → إلى مذكورين
            ح/ حسابات جارية دائنة (الاستقطاعات)
            ح/ حساب أوامر الدفع (الصافي)
        التفصيلي:
          من ح/البند → إلى مذكورين
            ح/ الدمغة العادية
            ح/ الدمغة الإضافية
            ح/ الدمغة النسبية
            ح/ ضريبة الأرباح التجارية
        """
        rec55 = self.env['port_said.daftar55'].browse(daftar55_id)
        today = fields.Date.today()

        # ── القيد الإجمالي (صرفيات) ──────────────────────────────────────────
        sarfiyat_rec = self.create({
            'entry_date':    today,
            'register_type': 'sarfiyat',
            'daftar55_id':   rec55.id,
        })

        # ── القيود التفصيلية الإفرادية (تسويات) — فقط إذا وجدت استقطاعات ───
        taswiyat_rec = None
        if rec55.total_deductions > 0:
            taswiyat_rec = self.create({
                'entry_date':    today,
                'register_type': 'taswiyat',
                'daftar55_id':   rec55.id,
            })

        # ── إرسال رقم مسلسل 224 لقسم د في استمارة 50 ──────────────────────
        seq_224 = sarfiyat_rec.display_name
        update_vals = {'daftar224_sequence': seq_224}
        rec55.write(update_vals)

        return {'sarfiyat': sarfiyat_rec, 'taswiyat': taswiyat_rec}

    def action_print_daftar224(self):
        return self.env.ref('port_said_daftar224.action_report_daftar224_daily').report_action(self)
