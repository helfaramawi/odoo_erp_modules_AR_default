from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


# ── Hijri date conversion (inline) ───────────────────────────────────────────
_HIJRI_MONTHS = [
    '', 'محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر',
    'جمادى الأولى', 'جمادى الآخرة', 'رجب', 'شعبان',
    'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة',
]

def hijri_display(gdate):
    if not gdate:
        return ''
    try:
        d, m, y = gdate.day, gdate.month, gdate.year
        if m < 3:
            y -= 1
            m += 12
        A  = int(y / 100)
        B  = 2 - A + int(A / 4)
        JD = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524
        L  = JD - 1948440 + 10632
        N  = int((L - 1) / 10631)
        L  = L - 10631 * N + 354
        J  = (int((10985 - L) / 5316) * int(50 * L / 17719) +
              int(L / 5670) * int(43 * L / 15238))
        L  = (L - int((30 - J) / 15) * int(17719 * J / 50) -
              int(J / 16) * int(15238 * J / 43) + 29)
        Hm = int(24 * L / 709)
        Hd = L - int(709 * Hm / 24)
        Hy = 30 * N + J - 30
        mn = _HIJRI_MONTHS[Hm] if 1 <= Hm <= 12 else ''
        return f'{Hd} {mn} {Hy} هـ'
    except Exception:
        return ''


class Form69DailyReckoning(models.Model):
    """
    استمارة 69 ع.ح — الحسبة اليومية
    تسحب البيانات من دفتر 224 (C-FM-02) وتتقاطع مع دفتر 55 (C-FM-01).
    تُغذّي استمارة 75 الشهرية (C-FM-04).
    """
    _name = 'port_said.form69'
    _description = 'استمارة 69 ع.ح - الحسبة اليومية'
    _order = 'reckoning_date desc'
    _rec_name = 'reckoning_date'

    reckoning_date       = fields.Date(string='تاريخ الحسبة', required=True, index=True)
    reckoning_date_hijri = fields.Char(string='التاريخ الهجري', compute='_compute_hijri', store=True)
    fiscal_year          = fields.Integer(string='السنة المالية', required=True)
    fiscal_month         = fields.Integer(string='الشهر المالي', required=True)

    opening_balance  = fields.Monetary(string='الرصيد الافتتاحي', currency_field='currency_id')
    sarfiyat_total   = fields.Monetary(string='إجمالي الصرفيات', currency_field='currency_id')
    taswiyat_total   = fields.Monetary(string='إجمالي التسويات', currency_field='currency_id')
    closing_balance  = fields.Monetary(
        string='الرصيد الختامي', compute='_compute_closing', store=True,
        currency_field='currency_id')
    is_balanced      = fields.Boolean(string='متوازن', compute='_compute_closing', store=True)

    daftar55_count   = fields.Integer(string='عدد معاملات دفتر 55 ع.ح')
    daftar55_total   = fields.Monetary(string='إجمالي دفتر 55 ع.ح', currency_field='currency_id')
    match_ok         = fields.Boolean(string='تطابق مع دفتر 55 ع.ح', compute='_compute_match', store=True)

    signed_by        = fields.Many2one('res.users', string='اعتمد من')
    sign_date        = fields.Datetime(string='تاريخ الاعتماد')
    state            = fields.Selection([
        ('draft',  'مسودة'),
        ('done',   'مكتمل'),
        ('signed', 'معتمد'),
    ], default='draft', string='الحالة', tracking=True)

    currency_id  = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    company_id   = fields.Many2one('res.company', default=lambda s: s.env.company)
    notes        = fields.Text(string='ملاحظات')

    _sql_constraints = [
        ('unique_date', 'UNIQUE(reckoning_date, company_id)',
         'توجد حسبة يومية مسجلة لهذا التاريخ بالفعل.'),
    ]

    @api.depends('reckoning_date')
    def _compute_hijri(self):
        for rec in self:
            rec.reckoning_date_hijri = hijri_display(rec.reckoning_date)

    @api.depends('opening_balance', 'sarfiyat_total', 'taswiyat_total')
    def _compute_closing(self):
        for rec in self:
            rec.closing_balance = rec.opening_balance + rec.sarfiyat_total - rec.taswiyat_total
            rec.is_balanced = True

    @api.depends('sarfiyat_total', 'daftar55_total')
    def _compute_match(self):
        for rec in self:
            rec.match_ok = abs(rec.sarfiyat_total - rec.daftar55_total) < 0.01

    @api.model
    def generate_daily_reckoning(self, date=None):
        """يُنشئ الحسبة اليومية من دفتر 224 — يُستدعى من cron أو يدوياً."""
        date = date or fields.Date.today()
        existing = self.search([('reckoning_date', '=', date)])
        if existing:
            return existing

        D224 = self.env['port_said.daftar224']
        totals = D224.get_daily_totals(date)

        # دفتر 55 ع.ح = سجل مدفوعات الموردين — هو المرجع الصح للحسبة اليومية المالية
        # الحسبة اليومية (استمارة 69) تتطابق مع إجمالي الصرفيات في دفتر 55
        D55 = self.env['port_said.daftar55']
        d55_recs  = D55.search([('date_received', '=', date)])
        d55_total = sum(d55_recs.mapped('amount_gross'))

        prev = self.search([('reckoning_date', '<', date)], order='reckoning_date desc', limit=1)
        opening = prev.closing_balance if prev else 0.0

        rec = self.create({
            'reckoning_date':  date,
            'fiscal_year':     date.year,
            'fiscal_month':    date.month,
            'opening_balance': opening,
            'sarfiyat_total':  totals['sarfiyat_total'],
            'taswiyat_total':  totals['taswiyat_total'],
            'daftar55_count':  len(d55_recs),
            'daftar55_total':  d55_total,
            'state':           'done',
        })
        return rec

    def action_sign(self):
        self.write({'state': 'signed', 'signed_by': self.env.uid, 'sign_date': fields.Datetime.now()})

    def action_print(self):
        return self.env.ref('port_said_form69.action_report_form69').report_action(self)
