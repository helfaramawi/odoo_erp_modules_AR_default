# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _


class PortSaidExecutiveBriefingEngine(models.TransientModel):
    _name = 'port_said.executive.briefing.engine'
    _description = 'محرك الملخص التنفيذي اليومي'

    @api.model
    def cron_generate_and_send_daily_briefing(self):
        briefing = self.generate_daily_briefing()
        send_auto = self.env['ir.config_parameter'].sudo().get_param('port_said_executive_briefing.auto_send', '1')
        if str(send_auto).lower() in ['1', 'true', 'yes']:
            briefing._send_internal_mail()
        return True

    @api.model
    def action_generate_now(self):
        briefing = self.generate_daily_briefing()
        return {
            'type': 'ir.actions.act_window',
            'name': 'الملخص التنفيذي اليومي',
            'res_model': 'port_said.executive.briefing',
            'res_id': briefing.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def generate_daily_briefing(self):
        today = fields.Date.today()
        Briefing = self.env['port_said.executive.briefing'].sudo()

        briefing = Briefing.search([('briefing_date', '=', today)], limit=1)
        if not briefing:
            briefing = Briefing.create({'briefing_date': today})

        briefing.line_ids.unlink()

        lines = []
        lines += self._get_budget_risks()
        lines += self._get_late_cheques()
        lines += self._get_eta_failed()
        lines += self._get_new_penalties()
        lines += self._get_pending_procurement()
        lines += self._get_payment_delays()
        lines += self._get_dead_stock()

        for vals in lines:
            vals['briefing_id'] = briefing.id
            self.env['port_said.executive.briefing.line'].sudo().create(vals)

        counts = self._section_counts(lines)
        risk_score, risk_level = self._overall_risk(lines)

        summary_text = self._write_summary_text(lines, counts, risk_score, risk_level)
        summary_html = self._write_summary_html(lines, counts, risk_score, risk_level)
        actions = self._write_action_items(lines)
        management_message = self._write_management_message(summary_html, actions)

        briefing.write({
            'risk_score': risk_score,
            'risk_level': risk_level,
            'summary_text': summary_text,
            'summary_html': summary_html,
            'action_items': actions,
            'management_message': management_message,
            'budget_risk_count': counts.get('budget_risks', 0),
            'late_cheque_count': counts.get('late_cheques', 0),
            'eta_failed_count': counts.get('eta_failed', 0),
            'penalty_count': counts.get('new_penalties', 0),
            'pending_procurement_count': counts.get('pending_procurement', 0),
            'payment_delay_count': counts.get('payment_delays', 0),
            'dead_stock_count': counts.get('dead_stock', 0),
            'total_exception_count': len(lines),
            'state': 'generated',
        })

        return briefing

    def _section_counts(self, lines):
        counts = {}
        for line in lines:
            counts[line['section']] = counts.get(line['section'], 0) + 1
        return counts

    def _overall_risk(self, lines):
        weights = {'low': 5, 'medium': 15, 'high': 30, 'critical': 45}
        score = sum(weights.get(l.get('severity'), 10) for l in lines)
        score = min(100.0, float(score))
        if score >= 80:
            return score, 'critical'
        if score >= 50:
            return score, 'high'
        if score >= 25:
            return score, 'medium'
        return score, 'low'

    def _today_start(self):
        return fields.Datetime.to_datetime(fields.Date.today())

    def _amount(self, rec, names):
        for fname in names:
            if fname in rec._fields:
                try:
                    return float(rec[fname] or 0.0)
                except Exception:
                    return 0.0
        return 0.0

    def _char(self, rec, names):
        for fname in names:
            if fname in rec._fields and rec[fname]:
                val = rec[fname]
                return val.display_name if hasattr(val, 'display_name') else str(val)
        return ''

    def _date(self, rec, names):
        for fname in names:
            if fname in rec._fields and rec[fname]:
                return fields.Date.to_date(rec[fname])
        return False

    def _line(self, section, title, description, action, severity, rec=False, amount=0.0, metric_1='', metric_2='', record_date=False):
        return {
            'section': section,
            'title': title,
            'description': description,
            'recommended_action': action,
            'severity': severity,
            'amount': amount or 0.0,
            'source_model': rec._name if rec else '',
            'source_res_id': rec.id if rec else 0,
            'source_display_name': rec.display_name if rec else '',
            'metric_1': metric_1 or '',
            'metric_2': metric_2 or '',
            'record_date': record_date or False,
        }

    # 1) Budget risks
    def _get_budget_risks(self):
        lines = []

        # Prefer previous budget forecast/reallocation/dead budget agents if installed.
        if 'port_said.budget.forecast.line' in self.env:
            Model = self.env['port_said.budget.forecast.line'].sudo()
            domain = []
            for fname in ['expected_variance', 'projected_variance', 'variance', 'forecast_variance']:
                if fname in Model._fields:
                    domain = [(fname, '<', 0)]
                    break
            if domain:
                for rec in Model.search(domain, limit=5):
                    variance = abs(self._amount(rec, ['expected_variance', 'projected_variance', 'variance', 'forecast_variance']))
                    title = 'عجز متوقع في بند موازنة'
                    desc = 'تم رصد عجز متوقع بقيمة %.2f في أحد بنود الموازنة.' % variance
                    lines.append(self._line('budget_risks', title, desc, 'مراجعة البند وتحديد مصدر تمويل أو توصية إعادة توزيع اعتماد.', 'high', rec, variance))
                if lines:
                    return lines[:5]

        if 'port_said.budget.plan' in self.env:
            Plan = self.env['port_said.budget.plan'].sudo()
            plans = Plan.search([('state', 'in', ['active', 'approved', 'open'])] if 'state' in Plan._fields else [], limit=5)
            for plan in plans:
                plan_lines = plan.line_ids if 'line_ids' in plan._fields else self.env['port_said.budget.line'].sudo().search([], limit=500)
                for line in plan_lines:
                    approved = self._amount(line, ['amount_approved', 'approved_amount', 'budget_amount'])
                    actual = self._amount(line, ['amount_actual', 'actual_amount'])
                    committed = self._amount(line, ['amount_committed', 'committed_amount'])
                    if approved and (actual + committed) / approved >= 0.90:
                        ratio = ((actual + committed) / approved) * 100
                        amount = actual + committed
                        severity = 'critical' if ratio >= 100 else 'high'
                        title = 'بند موازنة تجاوز حد الإنذار'
                        desc = 'البند %s وصل إلى %.2f%% من الاعتماد.' % (self._char(line, ['full_code', 'code', 'description', 'name']), ratio)
                        lines.append(self._line('budget_risks', title, desc, 'إيقاف أي ارتباطات جديدة على البند لحين مراجعة الاعتماد المتاح.', severity, line, amount, 'نسبة التنفيذ %.2f%%' % ratio))
        return lines[:5]

    # 2) Late cheques
    def _get_late_cheques(self):
        lines = []
        if 'port_said.cheque' not in self.env:
            return lines

        Cheque = self.env['port_said.cheque'].sudo()
        date_limit = fields.Date.today() - timedelta(days=7)
        domain = []
        for fname in ['issue_date', 'date_issue', 'date']:
            if fname in Cheque._fields:
                domain.append((fname, '<=', date_limit))
                break
        if 'state' in Cheque._fields:
            domain.append(('state', 'not in', ['delivered', 'paid', 'done', 'closed', 'cancelled']))

        for rec in Cheque.search(domain, limit=10):
            issue_date = self._date(rec, ['issue_date', 'date_issue', 'date'])
            days = (fields.Date.today() - issue_date).days if issue_date else 0
            amount = self._amount(rec, ['amount', 'amount_total', 'cheque_amount'])
            title = 'شيك صدر ولم يسلم'
            desc = 'الشيك %s لم يتم تسليمه منذ %s يوم.' % (rec.display_name, days)
            lines.append(self._line('late_cheques', title, desc, 'متابعة الخزينة وتوثيق التسليم أو سبب التأخير اليوم.', 'high' if days >= 14 else 'medium', rec, amount, 'تأخير %s يوم' % days, record_date=issue_date))
        return lines[:5]

    # 3) ETA failed
    def _get_eta_failed(self):
        lines = []
        candidate_models = ['eta.invoice', 'l10n_eg.eta.invoice']
        for model_name in candidate_models:
            if model_name not in self.env:
                continue
            Model = self.env[model_name].sudo()
            domain = []
            if 'state' in Model._fields:
                domain.append(('state', 'in', ['failed', 'invalid', 'needs_correction', 'rejected']))
            for rec in Model.search(domain, limit=5):
                amount = self._amount(rec, ['amount_total', 'total_amount', 'amount'])
                err = self._char(rec, ['eta_error_message', 'error_message', 'message'])
                title = 'فاتورة ETA مرفوضة أو تحتاج تصحيح'
                desc = 'الفاتورة %s حالتها غير سليمة. %s' % (rec.display_name, err)
                lines.append(self._line('eta_failed', title, desc, 'تصحيح خطأ ETA وإعادة الإرسال قبل نهاية اليوم.', 'high', rec, amount))
            break
        return lines[:5]

    # 4) New penalties
    def _get_new_penalties(self):
        lines = []
        today_start = self._today_start()
        candidate_models = ['port_said.vendor.penalty', 'port_said.penalty', 'port_said.penalties', 'penalties.said.port']
        for model_name in candidate_models:
            if model_name not in self.env:
                continue
            Model = self.env[model_name].sudo()
            domain = [('create_date', '>=', today_start)] if 'create_date' in Model._fields else []
            for rec in Model.search(domain, limit=5):
                amount = self._amount(rec, ['amount', 'penalty_amount', 'total_amount'])
                vendor = self._char(rec, ['partner_id', 'vendor_id', 'supplier_id'])
                title = 'جزاء جديد على مورد'
                desc = 'تم تسجيل جزاء جديد %s على المورد %s.' % (rec.display_name, vendor or '')
                lines.append(self._line('new_penalties', title, desc, 'مراجعة أثر الجزاء على تقييم المورد وقرارات الترسية القادمة.', 'medium', rec, amount))
            if lines:
                break
        return lines[:5]

    # 5) Pending procurement
    def _get_pending_procurement(self):
        lines = []
        if 'procurement.adjudication' in self.env:
            Model = self.env['procurement.adjudication'].sudo()
            domain = []
            if 'state' in Model._fields:
                domain = [('state', 'not in', ['done', 'cancelled', 'awarded', 'approved'])]
            for rec in Model.search(domain, limit=5):
                amount = self._amount(rec, ['amount_total', 'total_amount', 'estimated_amount'])
                title = 'عملية مشتريات تحتاج اعتماد أو قرار'
                desc = 'عملية الترسية/البت %s ما زالت مفتوحة وتحتاج متابعة.' % rec.display_name
                lines.append(self._line('pending_procurement', title, desc, 'تحديد مسؤول القرار وتاريخ مستهدف للإغلاق.', 'medium', rec, amount))
        return lines[:5]

    # 6) Payment delays from Agent 16 if installed, otherwise Daftar55 aging
    def _get_payment_delays(self):
        lines = []
        if 'port_said.payment.cycle.delay' in self.env:
            Model = self.env['port_said.payment.cycle.delay'].sudo()
            domain = [('state', 'not in', ['resolved', 'justified', 'cancelled'])]
            for rec in Model.search(domain, order='delay_days desc', limit=5):
                amount = self._amount(rec, ['amount'])
                title = 'تأخير إداري في دورة الصرف'
                desc = '%s - تأخير %s يوم في مرحلة %s.' % (rec.source_display_name or rec.display_name, rec.delay_days, rec.stage)
                severity = rec.risk_level if rec.risk_level in ['low', 'medium', 'high', 'critical'] else 'medium'
                lines.append(self._line('payment_delays', title, desc, 'تصعيد المعاملة للمرحلة المسؤولة وإغلاق سبب التعطل.', severity, rec, amount, 'تأخير %s يوم' % rec.delay_days))
            return lines[:5]

        if 'port_said.daftar55' in self.env:
            Model = self.env['port_said.daftar55'].sudo()
            date_limit = fields.Date.today() - timedelta(days=7)
            domain = []
            if 'state' in Model._fields:
                domain.append(('state', 'not in', ['posted', 'archived', 'cancelled']))
            for fname in ['date_received', 'date', 'create_date']:
                if fname in Model._fields:
                    domain.append((fname, '<=', date_limit))
                    break
            for rec in Model.search(domain, limit=5):
                amount = self._amount(rec, ['amount_gross', 'amount_total', 'amount'])
                title = 'دفتر 55 متأخر'
                desc = 'سجل دفتر 55 %s لم يصل إلى الترحيل/الأرشفة خلال الفترة المتوقعة.' % rec.display_name
                lines.append(self._line('payment_delays', title, desc, 'متابعة حالة السجل وتحديد سبب التعطل.', 'medium', rec, amount))
        return lines[:5]

    # 7) Dead stock from Agent 14 if installed
    def _get_dead_stock(self):
        lines = []
        if 'port_said.dead.stock.alert' not in self.env:
            return lines
        Model = self.env['port_said.dead.stock.alert'].sudo()
        domain = [('state', 'not in', ['resolved', 'ignored', 'cancelled'])]
        for rec in Model.search(domain, order='stock_value desc', limit=5):
            amount = self._amount(rec, ['stock_value'])
            severity = rec.risk_level if rec.risk_level in ['low', 'medium', 'high', 'critical'] else 'medium'
            title = 'مخزون راكد أو عالي القيمة'
            desc = 'الصنف %s يمثل قيمة مجمدة %.2f.' % (rec.product_id.display_name if rec.product_id else rec.display_name, amount)
            lines.append(self._line('dead_stock', title, desc, 'مراجعة إعادة توزيع أو تصرف أو وقف شراء الصنف.', severity, rec, amount))
        return lines[:5]

    def _top_lines(self, lines, limit=5):
        weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        return sorted(lines, key=lambda x: (weights.get(x.get('severity'), 0), x.get('amount') or 0), reverse=True)[:limit]

    def _write_summary_text(self, lines, counts, risk_score, risk_level):
        top = self._top_lines(lines, 5)
        risk_label = dict(self.env['port_said.executive.briefing']._fields['risk_level'].selection).get(risk_level, risk_level)
        text = []
        text.append('الملخص التنفيذي اليومي')
        text.append('درجة الخطورة العامة: %.2f من 100 - %s' % (risk_score, risk_label))
        text.append('إجمالي الاستثناءات المهمة: %s' % len(lines))
        text.append('')
        text.append('أهم 5 مخاطر اليوم:')
        if not top:
            text.append('- لا توجد استثناءات حرجة مسجلة اليوم وفق قواعد الفحص الحالية.')
        for i, item in enumerate(top, 1):
            text.append('%s. %s: %s' % (i, item.get('title'), item.get('description')))
        return '\\n'.join(text)

    def _write_action_items(self, lines):
        top = self._top_lines(lines, 10)
        if not top:
            return 'لا توجد إجراءات عاجلة مطلوبة اليوم.'
        actions = []
        for i, item in enumerate(top, 1):
            actions.append('%s. %s' % (i, item.get('recommended_action') or item.get('title')))
        return '\\n'.join(actions)

    def _write_summary_html(self, lines, counts, risk_score, risk_level):
        top = self._top_lines(lines, 5)
        risk_label = dict(self.env['port_said.executive.briefing']._fields['risk_level'].selection).get(risk_level, risk_level)

        rows = ''
        if not top:
            rows = '<tr><td colspan="4">لا توجد استثناءات حرجة مسجلة اليوم وفق قواعد الفحص الحالية.</td></tr>'
        for item in top:
            rows += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%.2f</td></tr>' % (
                item.get('title') or '',
                item.get('description') or '',
                item.get('severity') or '',
                item.get('amount') or 0.0,
            )

        return """
        <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.8;">
            <h2>الملخص التنفيذي اليومي للقيادة العليا</h2>
            <p><strong>التاريخ:</strong> %s</p>
            <p><strong>درجة الخطورة العامة:</strong> %.2f من 100 - <strong>%s</strong></p>

            <h3>لوحة الاستثناءات</h3>
            <ul>
                <li>مخاطر الموازنة: %s</li>
                <li>شيكات متأخرة: %s</li>
                <li>فواتير ETA مرفوضة: %s</li>
                <li>جزاءات جديدة: %s</li>
                <li>مشتريات تحتاج اعتماد: %s</li>
                <li>تأخيرات إدارية: %s</li>
                <li>مخزون راكد: %s</li>
            </ul>

            <h3>أهم 5 مخاطر مالية وتشغيلية اليوم</h3>
            <table class="table table-sm table-bordered">
                <thead>
                    <tr>
                        <th>الخطر</th>
                        <th>الوصف</th>
                        <th>الخطورة</th>
                        <th>القيمة</th>
                    </tr>
                </thead>
                <tbody>%s</tbody>
            </table>

            <p><strong>الخلاصة الإدارية:</strong> يوصى بمتابعة البنود عالية الخطورة أولًا، وإغلاق الاستثناءات التي تؤثر مباشرة على الموازنة والصرف والمشتريات خلال نفس يوم العمل.</p>
        </div>
        """ % (
            fields.Date.today(),
            risk_score,
            risk_label,
            counts.get('budget_risks', 0),
            counts.get('late_cheques', 0),
            counts.get('eta_failed', 0),
            counts.get('new_penalties', 0),
            counts.get('pending_procurement', 0),
            counts.get('payment_delays', 0),
            counts.get('dead_stock', 0),
            rows,
        )

    def _write_management_message(self, summary_html, actions):
        return """
        <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.8;">
            %s
            <h3>الإجراءات المطلوبة اليوم</h3>
            <pre style="white-space: pre-wrap;">%s</pre>
        </div>
        """ % (summary_html, actions)
