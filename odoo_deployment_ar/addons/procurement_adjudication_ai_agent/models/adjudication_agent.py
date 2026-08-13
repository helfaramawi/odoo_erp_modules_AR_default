# -*- coding: utf-8 -*-
import base64
import re

from markupsafe import Markup

from odoo import api, fields, models, _


class ProcurementAdjudicationAgent(models.Model):
    _inherit = 'procurement.adjudication'

    agent_technical_minutes = fields.Html(string='مسودة محضر البت الفني من الوكيل', readonly=True, copy=False)
    agent_financial_minutes = fields.Html(string='مسودة محضر البت المالي من الوكيل', readonly=True, copy=False)
    agent_award_notification = fields.Html(string='مسودة إخطار الترسية من الوكيل', readonly=True, copy=False)
    agent_last_analysis_date = fields.Datetime(string='آخر تحليل بواسطة الوكيل', readonly=True, copy=False)

    agent_log_ids = fields.One2many(
        'procurement.adjudication.agent.log',
        'adjudication_id',
        string='سجل تحليلات الوكيل',
        readonly=True,
    )

    def action_open_technical(self):
        res = super().action_open_technical()
        for rec in self:
            rec._agent_analyze_technical()
        return res

    def action_open_financial(self):
        res = super().action_open_financial()
        for rec in self:
            rec._agent_rank_financial()
        return res

    def action_agent_run_technical_now(self):
        for rec in self:
            rec._agent_analyze_technical()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('وكيل تحليل العروض'),
                'message': _('تم تنفيذ التحليل الفني وإعداد مسودة محضر البت الفني.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_agent_run_financial_now(self):
        for rec in self:
            rec._agent_rank_financial()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('وكيل تحليل العروض'),
                'message': _('تم تنفيذ التحليل المالي وإعداد مسودة المقارنة المالية.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _agent_is_enabled(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'procurement_adjudication_ai_agent.enabled', 'True'
        ) == 'True'

    def _agent_analyze_technical(self):
        if not self._agent_is_enabled():
            return True

        min_score = float(self.env['ir.config_parameter'].sudo().get_param(
            'procurement_adjudication_ai_agent.min_technical_score', '70'
        ) or 70)

        for rec in self:
            logs_html = []
            specs_text = rec._agent_get_specs_text()
            for supplier in rec.supplier_line_ids:
                result = rec._agent_compare_supplier_to_specs(supplier, specs_text, min_score=min_score)

                supplier.write({
                    'agent_technical_score': result['score'],
                    'agent_technical_pass': result['pass'],
                    'agent_technical_notes': result['summary'],
                    'agent_strengths': result['strengths'],
                    'agent_weaknesses': result['weaknesses'],
                })

                rec.env['procurement.adjudication.agent.log'].sudo().create({
                    'adjudication_id': rec.id,
                    'supplier_line_id': supplier.id,
                    'partner_id': supplier.partner_id.id if 'partner_id' in supplier._fields and supplier.partner_id else False,
                    'analysis_type': 'technical',
                    'technical_score': result['score'],
                    'technical_pass': result['pass'],
                    'result_summary': result['summary'],
                    'strengths': result['strengths'],
                    'weaknesses': result['weaknesses'],
                    'recommendation': result['recommendation'],
                    'technical_details': result['technical_details'],
                })

                rec._agent_optionally_update_existing_technical_fields(supplier, result)
                logs_html.append(rec._agent_supplier_technical_html(supplier, result))

            minutes = rec._agent_prepare_technical_minutes_html(logs_html)
            rec.write({
                'agent_technical_minutes': minutes,
                'agent_last_analysis_date': fields.Datetime.now(),
            })
            rec.message_post(body=Markup(_('تم تنفيذ تحليل الوكيل للمظاريف الفنية وإعداد مسودة محضر البت الفني.')))
        return True

    def _agent_rank_financial(self):
        if not self._agent_is_enabled():
            return True

        dumping_threshold = float(self.env['ir.config_parameter'].sudo().get_param(
            'procurement_adjudication_ai_agent.dumping_threshold', '-15'
        ) or -15)

        for rec in self:
            qualified = rec.supplier_line_ids.filtered(lambda l: rec._agent_is_supplier_technically_qualified(l))
            ranked = qualified.sorted(lambda l: rec._agent_get_financial_bid(l) or 0.0)

            rows = []
            for idx, supplier in enumerate(ranked, start=1):
                bid = rec._agent_get_financial_bid(supplier)
                deviation = rec._agent_calc_deviation_pct(bid)
                dumping = deviation <= dumping_threshold if rec.estimated_value else False
                notes = rec._agent_prepare_financial_notes(supplier, idx, bid, deviation, dumping)

                supplier.write({
                    'agent_financial_rank': idx,
                    'agent_deviation_pct': deviation,
                    'agent_dumping_warning': dumping,
                    'agent_financial_notes': notes,
                })

                rec.env['procurement.adjudication.agent.log'].sudo().create({
                    'adjudication_id': rec.id,
                    'supplier_line_id': supplier.id,
                    'partner_id': supplier.partner_id.id if 'partner_id' in supplier._fields and supplier.partner_id else False,
                    'analysis_type': 'financial',
                    'financial_rank': idx,
                    'financial_bid': bid,
                    'deviation_pct': deviation,
                    'dumping_warning': dumping,
                    'result_summary': notes,
                    'recommendation': 'يوصى بعرض النتيجة على اللجنة المختصة لاتخاذ القرار وفقاً للإجراءات المعتمدة.',
                })

                rows.append(rec._agent_supplier_financial_html(supplier, idx, bid, deviation, dumping))

            minutes = rec._agent_prepare_financial_minutes_html(rows)
            award = rec._agent_prepare_award_notification_html(ranked[:1] if ranked else rec.env['adjudication.supplier.line'])
            rec.write({
                'agent_financial_minutes': minutes,
                'agent_award_notification': award,
                'agent_last_analysis_date': fields.Datetime.now(),
            })
            rec.message_post(body=Markup(_('تم تنفيذ تحليل الوكيل للمظاريف المالية وإعداد مسودة المقارنة المالية وإخطار الترسية.')))
        return True

    def _agent_get_specs_text(self):
        self.ensure_one()
        parts = []

        for field_name in ['specs_document', 'specification_document', 'terms_document', 'tender_specs', 'description', 'notes']:
            if field_name in self._fields and self[field_name]:
                value = self[field_name]
                if hasattr(value, 'datas'):
                    parts.append(self._agent_extract_attachment_text(value))
                else:
                    parts.append(str(value))

        attachments = self._agent_get_record_attachments(self)
        for att in attachments:
            txt = self._agent_extract_attachment_text(att)
            if txt:
                parts.append(txt)

        if 'dossier_id' in self._fields and self.dossier_id:
            for att in self._agent_get_record_attachments(self.dossier_id):
                txt = self._agent_extract_attachment_text(att)
                if txt:
                    parts.append(txt)

        return '\\n'.join([p for p in parts if p]).strip()

    def _agent_compare_supplier_to_specs(self, supplier, specs_text, min_score=70.0):
        offer_text = self._agent_get_supplier_offer_text(supplier)
        score = 0.0
        strengths = []
        weaknesses = []

        if offer_text:
            score += 35
            strengths.append('تم العثور على مستندات/نصوص فنية للعرض.')
        else:
            weaknesses.append('لم يتم العثور على مستندات فنية قابلة للقراءة للعرض.')

        if specs_text:
            score += 25
            strengths.append('تم العثور على كراسة شروط/مواصفات قابلة للمقارنة.')
        else:
            weaknesses.append('لم يتم العثور على كراسة شروط أو مواصفات قابلة للقراءة آلياً.')

        overlap = self._agent_keyword_overlap(specs_text, offer_text)
        score += min(40, overlap * 4)

        if overlap >= 8:
            strengths.append('يوجد تقارب جيد بين مفردات العرض والمواصفات.')
        elif overlap >= 3:
            strengths.append('يوجد تقارب جزئي بين العرض والمواصفات.')
            weaknesses.append('يلزم استكمال مراجعة اللجنة لأن التطابق الآلي جزئي.')
        else:
            weaknesses.append('لم يتم رصد تطابق كافٍ بين نص العرض ونص المواصفات.')

        score = min(100.0, score)
        passed = score >= min_score

        summary = (
            'نسبة المطابقة الفنية المقدرة آلياً: %.2f%%. النتيجة المقترحة: %s. '
            'هذا التحليل استرشادي ولا يغني عن قرار اللجنة المختصة.'
        ) % (score, 'مستوفٍ فنياً' if passed else 'غير مستوفٍ فنياً')

        recommendation = 'إدراج المورد ضمن قائمة المستوفين فنياً للعرض على اللجنة.' if passed else 'إدراج المورد ضمن قائمة غير المستوفين فنياً مع مراجعة اللجنة للأسباب.'

        return {
            'score': score,
            'pass': passed,
            'summary': summary,
            'strengths': '\\n'.join(strengths),
            'weaknesses': '\\n'.join(weaknesses),
            'recommendation': recommendation,
            'technical_details': 'Keyword overlap count: %s. This is an on-prem rule-based analysis hook.' % overlap,
        }

    def _agent_get_supplier_offer_text(self, supplier):
        parts = []
        for field_name in ['technical_notes', 'notes', 'description', 'offer_description']:
            if field_name in supplier._fields and supplier[field_name]:
                parts.append(str(supplier[field_name]))

        for field_name in ['attachment_ids', 'technical_attachment_ids', 'document_ids']:
            if field_name in supplier._fields and supplier[field_name]:
                for att in supplier[field_name]:
                    txt = self._agent_extract_attachment_text(att)
                    if txt:
                        parts.append(txt)

        for att in self._agent_get_record_attachments(supplier):
            txt = self._agent_extract_attachment_text(att)
            if txt:
                parts.append(txt)

        return '\\n'.join([p for p in parts if p]).strip()

    def _agent_get_record_attachments(self, record):
        return self.env['ir.attachment'].sudo().search([
            ('res_model', '=', record._name),
            ('res_id', '=', record.id),
        ])

    def _agent_extract_attachment_text(self, attachment):
        try:
            raw = base64.b64decode(attachment.datas or b'')
        except Exception:
            return ''

        mimetype = attachment.mimetype or ''
        name = (attachment.name or '').lower()

        if mimetype.startswith('text/') or name.endswith(('.txt', '.csv', '.xml', '.html', '.htm')):
            return self._agent_decode_bytes(raw)

        if mimetype == 'application/pdf' or name.endswith('.pdf'):
            try:
                from pdfminer.high_level import extract_text
                import io
                return extract_text(io.BytesIO(raw)) or ''
            except Exception:
                return ''

        return self._agent_decode_bytes(raw)

    def _agent_decode_bytes(self, raw):
        for enc in ['utf-8', 'windows-1256', 'cp1256', 'latin-1']:
            try:
                return raw.decode(enc, errors='ignore')
            except Exception:
                pass
        return ''

    def _agent_normalize_text(self, text):
        text = str(text or '').lower()
        text = re.sub(r'[\\s\\u0640]+', ' ', text)
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        return text.strip()

    def _agent_keyword_overlap(self, specs_text, offer_text):
        specs = self._agent_normalize_text(specs_text)
        offer = self._agent_normalize_text(offer_text)
        if not specs or not offer:
            return 0

        words = [w for w in re.split(r'\\W+', specs) if len(w) >= 4]
        common = set(words[:300])
        hits = [w for w in common if w in offer]
        return len(hits)

    def _agent_optionally_update_existing_technical_fields(self, supplier, result):
        auto_write = self.env['ir.config_parameter'].sudo().get_param(
            'procurement_adjudication_ai_agent.auto_write_pass', 'False'
        ) == 'True'
        if not auto_write:
            return

        vals = {}
        if 'technical_score' in supplier._fields:
            vals['technical_score'] = result['score']
        if 'technical_notes' in supplier._fields:
            vals['technical_notes'] = result['summary']
        if 'technical_pass' in supplier._fields:
            vals['technical_pass'] = result['pass']
        if 'technical_result' in supplier._fields:
            vals['technical_result'] = 'pass' if result['pass'] else 'fail'
        if vals:
            supplier.write(vals)

    def _agent_is_supplier_technically_qualified(self, supplier):
        if 'technical_pass' in supplier._fields:
            return bool(supplier.technical_pass)
        if 'technical_result' in supplier._fields and supplier.technical_result:
            return supplier.technical_result in ['pass', 'accepted', 'qualified', 'مطابق', 'مستوفي']
        return bool(supplier.agent_technical_pass)

    def _agent_get_financial_bid(self, supplier):
        for field_name in ['financial_bid', 'bid_amount', 'amount', 'total_amount', 'price_total']:
            if field_name in supplier._fields and supplier[field_name]:
                try:
                    return float(supplier[field_name])
                except Exception:
                    return 0.0
        return 0.0

    def _agent_calc_deviation_pct(self, bid):
        self.ensure_one()
        est = self.estimated_value or 0.0
        if not est:
            return 0.0
        return ((bid - est) / est) * 100.0

    def _agent_prepare_financial_notes(self, supplier, rank, bid, deviation, dumping):
        msg = 'الترتيب المالي: %s. قيمة العرض: %.2f. نسبة الانحراف عن القيمة التقديرية: %.2f%%.' % (rank, bid, deviation)
        if dumping:
            msg += ' يوجد تحذير: العرض أقل من القيمة التقديرية بنسبة تتجاوز حد التحذير، ويوصى بمراجعة اللجنة لاحتمال انخفاض مبالغ فيه.'
        return msg

    def _agent_supplier_technical_html(self, supplier, result):
        name = supplier.partner_id.display_name if 'partner_id' in supplier._fields and supplier.partner_id else supplier.display_name
        status = 'مستوفٍ' if result['pass'] else 'غير مستوفٍ'
        return '''
        <tr>
            <td>%s</td>
            <td>%.2f%%</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
        </tr>
        ''' % (name, result['score'], status, result['strengths'].replace('\\n', '<br/>'), result['weaknesses'].replace('\\n', '<br/>'))

    def _agent_supplier_financial_html(self, supplier, rank, bid, deviation, dumping):
        name = supplier.partner_id.display_name if 'partner_id' in supplier._fields and supplier.partner_id else supplier.display_name
        warning = 'نعم' if dumping else 'لا'
        return '''
        <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%.2f</td>
            <td>%.2f%%</td>
            <td>%s</td>
        </tr>
        ''' % (rank, name, bid, deviation, warning)

    def _agent_prepare_technical_minutes_html(self, rows):
        rows_html = ''.join(rows) if rows else '<tr><td colspan="5">لا توجد عروض لتحليلها.</td></tr>'
        return '''
        <div dir="rtl" style="text-align:right;font-family:Arial,Tahoma;">
            <h3>مسودة محضر البت الفني</h3>
            <p>بناءً على فتح المظاريف الفنية، قام وكيل التحليل بإعداد مقارنة استرشادية للعروض الفنية تمهيداً لعرضها على اللجنة المختصة.</p>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse;width:100%;">
                <tr>
                    <th>المورد</th>
                    <th>نسبة المطابقة</th>
                    <th>النتيجة المقترحة</th>
                    <th>نقاط القوة</th>
                    <th>نقاط الضعف</th>
                </tr>
                %s
            </table>
            <p><b>تنويه:</b> هذه المسودة استرشادية ولا تُعد قراراً نهائياً إلا بعد مراجعة واعتماد اللجنة المختصة.</p>
        </div>
        ''' % rows_html

    def _agent_prepare_financial_minutes_html(self, rows):
        rows_html = ''.join(rows) if rows else '<tr><td colspan="5">لا توجد عروض مستوفية فنياً للمقارنة المالية.</td></tr>'
        return '''
        <div dir="rtl" style="text-align:right;font-family:Arial,Tahoma;">
            <h3>مسودة مقارنة العروض المالية</h3>
            <p>بناءً على فتح المظاريف المالية، تم ترتيب الموردين المستوفين فنياً تصاعدياً حسب قيمة العرض المالي.</p>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse;width:100%;">
                <tr>
                    <th>الترتيب</th>
                    <th>المورد</th>
                    <th>قيمة العرض</th>
                    <th>نسبة الانحراف</th>
                    <th>تحذير انخفاض مبالغ فيه</th>
                </tr>
                %s
            </table>
            <p><b>تنويه:</b> هذه المقارنة لا تغني عن قرار اللجنة المختصة والإجراءات القانونية الواجبة.</p>
        </div>
        ''' % rows_html

    def _agent_prepare_award_notification_html(self, winner_lines):
        if not winner_lines:
            return '<div dir="rtl"><p>لا يوجد مورد مرشح للترسية لعدم وجود عروض مالية مستوفية.</p></div>'

        w = winner_lines[0]
        name = w.partner_id.display_name if 'partner_id' in w._fields and w.partner_id else w.display_name
        bid = self._agent_get_financial_bid(w)
        return '''
        <div dir="rtl" style="text-align:right;font-family:Arial,Tahoma;">
            <h3>مسودة إخطار الترسية</h3>
            <p>السادة / %s</p>
            <p>نحيطكم علماً بأنه بعد انتهاء أعمال الفحص الفني والمقارنة المالية، فقد تبين أن عرضكم هو الأقل سعراً بين العروض المستوفية فنياً بقيمة %.2f، وذلك تمهيداً لاستكمال إجراءات الترسية وفقاً للقواعد والإجراءات القانونية المعتمدة.</p>
            <p>وتفضلوا بقبول فائق الاحترام.</p>
        </div>
        ''' % (name, bid)


class AdjudicationSupplierLineAgent(models.Model):
    _inherit = 'adjudication.supplier.line'

    agent_technical_score = fields.Float(string='نسبة المطابقة الفنية بواسطة الوكيل %', digits=(16, 2), readonly=True, copy=False)
    agent_technical_pass = fields.Boolean(string='مستوفٍ فنياً حسب الوكيل', readonly=True, copy=False)
    agent_technical_notes = fields.Text(string='ملاحظات التحليل الفني بواسطة الوكيل', readonly=True, copy=False)
    agent_strengths = fields.Text(string='نقاط القوة بواسطة الوكيل', readonly=True, copy=False)
    agent_weaknesses = fields.Text(string='نقاط الضعف بواسطة الوكيل', readonly=True, copy=False)

    agent_financial_rank = fields.Integer(string='الترتيب المالي بواسطة الوكيل', readonly=True, copy=False)
    agent_deviation_pct = fields.Float(string='نسبة الانحراف بواسطة الوكيل %', digits=(16, 2), readonly=True, copy=False)
    agent_dumping_warning = fields.Boolean(string='تحذير انخفاض مبالغ فيه بواسطة الوكيل', readonly=True, copy=False)
    agent_financial_notes = fields.Text(string='ملاحظات التحليل المالي بواسطة الوكيل', readonly=True, copy=False)
