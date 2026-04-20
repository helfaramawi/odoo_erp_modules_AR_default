# -*- coding: utf-8 -*-
"""
form50_pdf_builder.py
يولّد PDF استمارة 50 ع.ح مباشرة بـ ReportLab
مربوط بـ model: port_said.daftar55
"""
import io, os, logging
from odoo import models, api

_logger = logging.getLogger(__name__)

_MODULE_DIR = os.path.dirname(os.path.dirname(__file__))
_BG_IMAGE   = os.path.join(_MODULE_DIR, 'static', 'img', 'form50_bg.jpg')

POS = {
    1:  (90.0,  1.5),  2:  (90.0,  3.0),
    3:  (30.0,  7.8),  4:  (30.0,  9.6),
    5:  (30.0, 11.4),  6:  (30.0, 15.1),
    7:  ( 3.5, 17.3),  8:  (15.0, 18.8),
    9:  (15.0, 20.7),  10: (15.0, 18.8),
    11: ( 6.0, 27.8),
    12: (59.5, 14.0),  13: (64.2, 14.0),
    14: (72.4, 14.0),  15: (80.5, 14.0),
    16: (59.5, 16.0),  17: (64.2, 16.0),
    18: (72.4, 16.0),  19: (80.5, 16.0),
    20: (59.5, 18.0),  21: (64.2, 18.0),
    22: (72.4, 18.0),  23: (80.5, 18.0),
    24: (59.5, 20.0),  25: (64.2, 20.0),
    26: (72.4, 20.0),  27: (80.5, 20.0),
    28: (72.4, 28.8),  29: (80.2, 28.8),
    30: (59.0, 31.7),  31: (26.9, 31.7),
    32: (97.0, 33.2),  33: ( 7.1, 38.9),
    34: (47.1, 41.0),  35: (51.8, 41.0),
    36: (56.6, 41.0),  37: (61.3, 41.0),
    38: (66.2, 41.0),  39: (74.7, 41.0),
    40: (66.2, 46.9),  41: (74.7, 46.9),
    42: (66.2, 49.2),  43: (74.7, 49.2),
    44: (66.2, 50.4),  45: (74.7, 50.4),
    46: (66.2, 51.6),  47: (74.7, 51.6),
    48: (66.2, 52.4),  49: (74.7, 52.4),
    50: (66.3, 56.4),  51: (74.6, 56.4),
    52: (17.8, 58.4),
    53: (38.0, 61.2),  54: (89.3, 59.2),
    55: ( 8.7, 61.2),  56: ( 8.7, 63.2),
    57: (54.3, 66.8),  58: (33.6, 66.8),
    59: ( 8.4, 66.7),
    60: (97.0, 72.0),  61: (42.3, 72.5),
    62: (45.5, 74.0),  63: (61.5, 74.4),
    64: (67.0, 76.0),  65: (65.0, 77.8),
    66: (80.4, 83.6),  67: (29.5, 81.8),
    68: (45.2, 83.6),  69: ( 5.6, 83.8),
    70: (97.0, 87.0),  71: (38.3, 87.3),
    72: ( 6.6, 87.3),  73: (34.6, 91.1),
    74: (46.0, 95.0),  75: (20.0, 95.0),
}

Y_OFFSET = 2.24
Y_UP     = -1.68
X_RIGHT  =  2.38
EXTRA_Y  = {8: 1.68, 28: 1.01, 29: 1.01}


def _ar(text):
    if not text: return ''
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)

def _j(v):
    try: return f'{int(v or 0):,}'
    except: return '0'

def _q(v):
    try: return f'{int(v or 0):02d}'
    except: return '00'

def _num(v):
    s = str(v).strip() if v is not None else ''
    return s if s.isdigit() else ''

def _money(amount):
    try:
        amount = round(float(amount or 0), 2)
        p = int(amount)
        q = round((amount - p) * 100)
        return p, q
    except Exception:
        return 0, 0


class Form50PdfBuilder(models.AbstractModel):
    _name        = 'report.port_said_form50_print.form50_final_template'
    _description = 'PDF Builder — استمارة 50 ع.ح'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {'docs': self.env['port_said.daftar55'].browse(docids)}

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        try:
            from reportlab.pdfgen import canvas as rlcanvas
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            _logger.error('reportlab غير مثبت')
            return super()._render_qweb_pdf(report_ref, res_ids, data)

        fn, fb = 'Helvetica', 'Helvetica-Bold'
        for name, path in [('ArabicR', '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf'),
                            ('ArabicB', '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf')]:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    if 'R' in name: fn = name
                    else:           fb = name
                except Exception: pass

        docs = self.env['port_said.daftar55'].browse(res_ids)
        buf  = io.BytesIO()
        c    = rlcanvas.Canvas(buf, pagesize=A4)
        A4_W, A4_H = A4

        for rec in docs:
            self._draw_record(c, rec, A4_W, A4_H, fn, fb)
            c.showPage()

        c.save()
        return buf.getvalue(), 'pdf'

    def _draw_record(self, c, rec, W, H, fn, fb):
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.colors import black

        if os.path.exists(_BG_IMAGE):
            try:
                c.drawImage(ImageReader(_BG_IMAGE), 0, 0,
                            width=W, height=H, preserveAspectRatio=False)
            except Exception as e:
                _logger.warning('BG: %s', e)

        # ── استخراج البيانات من السجل ────────────────────────────────────────
        def _get(field, default=''):
            return str(getattr(rec, field, None) or default)

        gj,  gq  = _money(getattr(rec, 'amount_gross', 0))
        nj,  nq  = _money(getattr(rec, 'amount_net',   0))
        sn_j,sn_q= _money(getattr(rec, 'deductions_stamp_normal', 0))
        se_j,se_q= _money(getattr(rec, 'deductions_stamp_extra',  0))
        sp_j,sp_q= _money(getattr(rec, 'deductions_stamp_proportional', 0))
        ct_j,ct_q= _money(getattr(rec, 'deductions_commercial_tax', 0))

        bp = {}
        if hasattr(rec, '_get_budget_parts'):
            try: bp = rec._get_budget_parts() or {}
            except Exception: pass

        invs    = getattr(rec, 'invoice_line_ids', [])
        inv     = invs[0] if invs else None
        inv_ref = str(getattr(inv, 'invoice_ref',  '') or '') if inv else ''
        inv_date= str(getattr(inv, 'invoice_date', '') or '') if inv else ''
        inv_j, inv_q = _money(getattr(inv, 'amount_total', 0) if inv else 0)

        vendor   = rec.vendor_id.name if rec.vendor_id else ''
        bank     = _get('bank_name')
        writer   = _get('writer_assigned')
        auditor  = rec.auditor_id.name       if hasattr(rec,'auditor_id')       and rec.auditor_id       else ''
        acct_h   = rec.accounts_head_id.name if hasattr(rec,'accounts_head_id') and rec.accounts_head_id else ''
        sect_h   = rec.section_head_id.name  if hasattr(rec,'section_head_id')  and rec.section_head_id  else ''
        reviewer = rec.reviewer_id.name      if hasattr(rec,'reviewer_id')      and rec.reviewer_id      else ''
        acct_no  = _get('bank_account_no')
        regz     = _get('register_z_ref')
        d224     = _get('daftar224_sequence')
        crossout = _get('crossout_signed_by')
        fy       = _get('fiscal_year')
        words    = _get('amount_words')
        dept     = _get('department_name')
        div      = _get('division_name')
        ref      = _get('commitment_ref')
        addr     = rec.vendor_id.street if rec.vendor_id and rec.vendor_id.street else ''
        attach   = _get('real_attachment_count') or _get('attachment_count_declared')
        seq      = _get('sequence_number') or str(rec.id)
        date_r   = _get('date_received')
        rev_date = _get('reviewer_stamp_date') or date_r

        # ── دالة الكتابة ─────────────────────────────────────────────────────
        def put(n, text, sz=8, bold=False, align='S', move=True):
            if not text or n not in POS: return
            c.setFont(fb if bold else fn, sz)
            c.setFillColor(black)
            xp, yp = POS[n]
            if move:
                xp = xp + X_RIGHT
                yp = yp + Y_OFFSET + Y_UP + EXTRA_Y.get(n, 0)
            else:
                yp = yp + Y_OFFSET
            x = W * xp / 100
            y = H * (1 - yp / 100)
            t = _ar(str(text))
            if   align == 'S':  c.drawString(x, y, t)
            elif align == 'C':  c.drawCentredString(x, y, t)
            elif align == 'RS': c.drawRightString(x, y, t)

        # ══ قسم أ ══
        put(1,  seq,    8.5, True,  'S')
        put(2,  date_r, 8,   False, 'S')
        put(3,  dept,   10.5,False, 'S', move=False)
        put(4,  div,    8.5, False, 'S')
        put(5,  vendor, 8.5, True,  'S')
        put(6,  ref,    8,   False, 'S')
        put(7,  vendor, 8,   False, 'S')
        put(8,  bank,   10,  False, 'S')
        put(9,  vendor, 8,   False, 'S')
        put(10, vendor, 8,   False, 'S')
        put(11, addr,   8,   False, 'S')

        # ══ فاتورة واحدة ══
        put(12, inv_ref,   7.5, False, 'C')
        put(13, inv_date,  7,   False, 'C')
        put(14, _j(inv_j), 8,   True,  'C')
        put(15, _q(inv_q), 7.5, False, 'C')

        # ══ الجملة ══
        put(28, _j(gj), 9, True,  'C')
        put(29, _q(gq), 8, False, 'C')

        # ══ قسم ب ══
        put(30, writer,  8,   False, 'S')
        put(31, regz,    7.5, False, 'C')
        put(32, date_r,  7.5, False, 'S')
        put(33, attach,  8.5, True,  'C')

        # ══ ميزانية ══
        for n, v in [(34,bp.get('band','')), (35,bp.get('fasle','')),
                     (36,bp.get('noa','')),  (37,bp.get('bab',''))]:
            x = _num(v)
            if x: put(n, x, 9, True, 'C')

        put(38, _j(gj), 9,   True,  'C')
        put(39, _q(gq), 8,   False, 'C')
        put(40, _j(gj), 9.5, True,  'C')
        put(41, _q(gq), 8.5, False, 'C')

        # ══ الاستقطاعات ══
        for nj,nq,vj,vq in [(42,43,sn_j,sn_q),(44,45,se_j,se_q),
                             (46,47,sp_j,sp_q),(48,49,ct_j,ct_q)]:
            put(nj, _j(vj), 8.5, False, 'C')
            put(nq, _q(vq), 8,   False, 'C')

        put(50, _j(nj), 10,  True,  'C')
        put(51, _q(nq), 9.5, True,  'C')

        # ══ تفقيط ══
        put(52, words, 8, True, 'S')

        # ══ إقرارات ══
        put(53, fy,      8.5, False, 'C')
        put(54, date_r,  8,   False, 'S')
        put(55, auditor, 8,   False, 'S')
        put(56, acct_h,  8,   False, 'S')
        put(57, acct_no, 8,   False, 'C')
        put(58, date_r,  8,   False, 'C')
        put(59, sect_h,  8,   False, 'S')

        # ══ قسم ج ══
        put(60, date_r,   7.5, False, 'S')
        put(61, seq,      9,   True,  'C')
        put(62, fy,       8.5, False, 'C')
        put(63, rev_date, 8,   False, 'C')
        put(64, vendor,   9,   True,  'S')
        put(65, f'{_j(nj)} جنيه {_q(nq)} قرش', 9, True, 'S')
        put(66, reviewer, 8,   False, 'S')
        put(67, acct_h,   8,   False, 'S')
        put(68, fy,       8.5, False, 'C')

        # بمبلغ رقم
        xp69, yp69 = POS[69]
        c.setFont(fb, 9)
        c.setFillColor(black)
        c.drawString(
            W * (xp69 + X_RIGHT) / 100,
            H * (1 - (yp69 + Y_OFFSET + Y_UP) / 100),
            f'{_j(nj)}.{_q(nq)}'
        )

        # ══ قسم د ══
        put(70, date_r,   7.5, False, 'S')
        put(71, d224,     8.5, True,  'C')
        put(72, writer,   8,   False, 'S')
        put(73, crossout, 8,   False, 'C')
