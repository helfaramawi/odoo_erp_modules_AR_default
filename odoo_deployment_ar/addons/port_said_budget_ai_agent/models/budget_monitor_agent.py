# -*- coding: utf-8 -*-
from datetime import timedelta
from markupsafe import Markup

from odoo import api, fields, models, _


class PortSaidBudgetPlanAgent(models.Model):
    _inherit = 'port_said.budget.plan'

    @api.model
    def action_run_budget_monitor_now(self):
        """Manual server action: run the budget monitor immediately."""
        self._cron_budget_monitor()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('وكيل مراقبة الموازنة'),
                'message': _('تم تشغيل فحص الموازنة الآن. راجع قائمة تنبيهات الموازنة للاطلاع على النتائج.'),
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def action_open_budget_alerts(self):
        """Open generated budget alerts from the manual action area."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('تنبيهات مراقبة الموازنة'),
            'res_model': 'port_said.budget.alert',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': {'search_default_open': 1},
        }

    @api.model
    def _cron_budget_monitor(self):
        """Daily cron job: monitor active budget plans and generate budget alerts."""
        today = fields.Date.today()
        plans = self.search([
            ('state', '=', 'active'),
            ('fiscal_year', '=', today.year),
        ])

        # Some implementations may use approved instead of active.
        if not plans:
            plans = self.search([
                ('state', '=', 'approved'),
                ('fiscal_year', '=', today.year),
            ])

        for plan in plans:
            plan._run_budget_monitor_for_plan(today=today)

    @api.model
    def _cron_budget_weekly_report(self):
        """Weekly report: create and post an Arabic summary of current budget risks."""
        today = fields.Date.today()
        plans = self.search([
            ('fiscal_year', '=', today.year),
            ('state', 'in', ['active', 'approved']),
        ])
        for plan in plans:
            html = plan._prepare_weekly_budget_report_html(today=today)
            if html:
                plan.message_post(body=Markup(html), subject=_('Weekly Budget Monitoring Report'))

    def _run_budget_monitor_for_plan(self, today=None):
        self.ensure_one()
        today = today or fields.Date.today()

        for line in self.line_ids:
            metrics = self._calculate_budget_line_metrics(line, today=today)
            risk_level = self._get_budget_risk_level(metrics)

            if not risk_level:
                continue

            # Avoid duplicate open alerts for the same budget line and same risk level on the same day.
            existing = self.env['port_said.budget.alert'].search_count([
                ('line_id', '=', line.id),
                ('risk_level', '=', risk_level),
                ('state', 'in', ['draft', 'sent', 'reviewed']),
                ('alert_date', '>=', fields.Datetime.to_string(fields.Datetime.now().replace(hour=0, minute=0, second=0))),
            ])
            if existing:
                continue

            surplus_lines = self._get_surplus_candidate_lines(excluded_line=line)
            alert = self._create_budget_monitor_alert(
                line=line,
                metrics=metrics,
                risk_level=risk_level,
                surplus_lines=surplus_lines,
                today=today,
            )
            alert.action_send_notification()

    def _calculate_budget_line_metrics(self, line, today=None):
        today = today or fields.Date.today()
        approved = line.amount_approved or 0.0
        actual = line.amount_actual or 0.0
        committed = line.amount_committed or 0.0
        available = line.amount_available or 0.0

        actual_execution_rate = (actual / approved * 100.0) if approved else 0.0
        commitment_rate = (committed / approved * 100.0) if approved else 0.0
        exposure_rate = ((actual + committed) / approved * 100.0) if approved else 0.0

        daily_burn_rate = self._calc_daily_burn_from_daftar55(line, days=60)
        days_to_exhaust = 0.0
        expected_exhaustion_date = False

        if daily_burn_rate > 0 and available > 0:
            days_to_exhaust = available / daily_burn_rate
            expected_exhaustion_date = today + timedelta(days=int(days_to_exhaust))

        return {
            'approved': approved,
            'actual': actual,
            'committed': committed,
            'available': available,
            'actual_execution_rate': actual_execution_rate,
            'commitment_rate': commitment_rate,
            'exposure_rate': exposure_rate,
            'daily_burn_rate': daily_burn_rate,
            'days_to_exhaust': days_to_exhaust,
            'expected_exhaustion_date': expected_exhaustion_date,
        }

    def _get_budget_risk_level(self, metrics):
        approved = metrics.get('approved') or 0.0
        available = metrics.get('available') or 0.0
        actual_execution_rate = metrics.get('actual_execution_rate') or 0.0
        exposure_rate = metrics.get('exposure_rate') or 0.0
        days_to_exhaust = metrics.get('days_to_exhaust') or 0.0

        if approved <= 0:
            return False

        if available <= 0 or actual_execution_rate >= 95.0 or exposure_rate >= 95.0:
            return 'critical'

        if actual_execution_rate >= 80.0 or exposure_rate >= 90.0:
            return 'high'

        if days_to_exhaust and days_to_exhaust <= 30.0:
            return 'high'

        if actual_execution_rate >= 65.0 or exposure_rate >= 75.0:
            return 'medium'

        return False

    def _calc_daily_burn_from_daftar55(self, line, days=60):
        """
        Calculate daily burn from port_said.daftar55.
        This uses the structure visible in the existing budget code:
        fiscal_year, budget_line, amount_gross.
        """
        date_from = fields.Date.today() - timedelta(days=days)
        domain = [
            ('fiscal_year', '=', str(line.plan_id.fiscal_year)),
            ('budget_line', '=', line.full_code),
        ]

        # Add date/state filters only if fields exist to avoid breaking different implementations.
        daftar_model = self.env['port_said.daftar55']
        if 'date' in daftar_model._fields:
            domain.append(('date', '>=', date_from))
        elif 'date_requested' in daftar_model._fields:
            domain.append(('date_requested', '>=', date_from))

        if 'state' in daftar_model._fields:
            domain.append(('state', 'in', ['posted', 'done', 'approved']))

        lines = daftar_model.search(domain)
        total_spent = sum(lines.mapped('amount_gross')) if 'amount_gross' in daftar_model._fields else 0.0
        return total_spent / float(days) if total_spent > 0 else 0.0

    def _get_surplus_candidate_lines(self, excluded_line):
        self.ensure_one()
        candidates = self.line_ids.filtered(lambda l: (
            l.id != excluded_line.id
            and (l.amount_approved or 0.0) > 0
            and (l.amount_available or 0.0) > 0
            and (((l.amount_actual or 0.0) / (l.amount_approved or 1.0)) * 100.0) < 30.0
        ))
        return candidates.sorted(lambda l: l.amount_available or 0.0, reverse=True)[:5]

    def _create_budget_monitor_alert(self, line, metrics, risk_level, surplus_lines, today=None):
        self.ensure_one()
        today = today or fields.Date.today()
        responsible = self.responsible_id or self.create_uid
        recommendation = self._prepare_budget_recommendation_text(line, metrics, risk_level, surplus_lines)
        body_html = self._prepare_budget_alert_body_html(line, metrics, risk_level, surplus_lines, recommendation)

        return self.env['port_said.budget.alert'].create({
            'fiscal_year': self.fiscal_year,
            'plan_id': self.id,
            'line_id': line.id,
            'responsible_id': responsible.id if responsible else False,
            'risk_level': risk_level,
            'amount_approved': metrics['approved'],
            'amount_actual': metrics['actual'],
            'amount_committed': metrics['committed'],
            'amount_available': metrics['available'],
            'actual_execution_rate': metrics['actual_execution_rate'],
            'commitment_rate': metrics['commitment_rate'],
            'exposure_rate': metrics['exposure_rate'],
            'daily_burn_rate': metrics['daily_burn_rate'],
            'days_to_exhaust': metrics['days_to_exhaust'],
            'expected_exhaustion_date': metrics['expected_exhaustion_date'],
            'surplus_line_ids': [(6, 0, surplus_lines.ids)],
            'recommendation': recommendation,
            'body_html': body_html,
        })

    def _prepare_budget_recommendation_text(self, line, metrics, risk_level, surplus_lines):
        level_ar = {
            'medium': 'متوسط',
            'high': 'مرتفع',
            'critical': 'حرج',
        }.get(risk_level, risk_level)

        if surplus_lines:
            surplus_names = '، '.join(surplus_lines.mapped('display_name')[:5])
            surplus_sentence = 'كما يُقترح مراجعة البنود منخفضة الصرف التالية كمصادر محتملة للدراسة: %s.' % surplus_names
        else:
            surplus_sentence = 'ولم يتم رصد بنود منخفضة الصرف مناسبة للمراجعة في الوقت الحالي.'

        return (
            'يوصى بمراجعة موقف بند الموازنة المذكور نظراً لأن مستوى الخطورة الحالي هو: %s. '
            'يرجى دراسة الرصيد المتاح والارتباطات القائمة ومعدل الصرف قبل إصدار أي موافقات جديدة على نفس البند. '
            '%s '
            'تنويه: هذه التوصية استرشادية ولا تمثل قراراً مالياً نهائياً، وأي مناقلة أو تعزيز اعتماد يخضع للوائح والسلطة المختصة.'
        ) % (level_ar, surplus_sentence)

    def _prepare_budget_alert_body_html(self, line, metrics, risk_level, surplus_lines, recommendation):
        level_ar = {
            'medium': 'متوسط',
            'high': 'مرتفع',
            'critical': 'حرج',
        }.get(risk_level, risk_level)

        expected_date = metrics.get('expected_exhaustion_date') or 'غير متاح'
        days = metrics.get('days_to_exhaust') or 0.0
        days_text = 'غير متاح' if not days else '%.0f يوم' % days

        surplus_html = '<p>لم يتم تحديد بنود منخفضة الصرف مناسبة للمراجعة.</p>'
        if surplus_lines:
            items = []
            for s in surplus_lines[:5]:
                items.append('<li>%s — المتاح: %.2f — المنصرف: %.2f — الاعتماد: %.2f</li>' % (
                    s.display_name,
                    s.amount_available or 0.0,
                    s.amount_actual or 0.0,
                    s.amount_approved or 0.0,
                ))
            surplus_html = '<ul>%s</ul>' % ''.join(items)

        return Markup('''
        <div dir="rtl" style="text-align:right;font-family:Arial,Tahoma,sans-serif;line-height:1.8;">
            <p>السيد / مسؤول الموازنة،</p>
            <p>
                نحيط سيادتكم علماً بأنه تم رصد مؤشر رقابي على بند الموازنة:
                <strong>{line_name}</strong>
                ضمن خطة الموازنة:
                <strong>{plan_name}</strong>.
            </p>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;">
                <tr><td><strong>مستوى الخطورة</strong></td><td>{risk_level}</td></tr>
                <tr><td><strong>الاعتماد المعتمد</strong></td><td>{approved:.2f}</td></tr>
                <tr><td><strong>المنصرف الفعلي</strong></td><td>{actual:.2f}</td></tr>
                <tr><td><strong>إجمالي الارتباطات</strong></td><td>{committed:.2f}</td></tr>
                <tr><td><strong>الرصيد المتاح</strong></td><td>{available:.2f}</td></tr>
                <tr><td><strong>نسبة التنفيذ الفعلي</strong></td><td>{actual_rate:.2f}%</td></tr>
                <tr><td><strong>نسبة التعرض المالي</strong></td><td>{exposure_rate:.2f}%</td></tr>
                <tr><td><strong>معدل الصرف اليومي</strong></td><td>{burn:.2f}</td></tr>
                <tr><td><strong>الأيام المتوقعة للاستنفاد</strong></td><td>{days_text}</td></tr>
                <tr><td><strong>تاريخ الاستنفاد المتوقع</strong></td><td>{expected_date}</td></tr>
            </table>
            <p><strong>التوصية المقترحة:</strong></p>
            <p>{recommendation}</p>
            <p><strong>بنود منخفضة الصرف مقترحة للمراجعة:</strong></p>
            {surplus_html}
            <p>
                هذا التنبيه صادر آلياً من نظام مراقبة الموازنة، ويهدف إلى دعم المراجعة المبكرة قبل تجاوز الاعتمادات أو استنفادها.
            </p>
        </div>
        ''').format(
            line_name=line.display_name,
            plan_name=self.display_name,
            risk_level=level_ar,
            approved=metrics.get('approved') or 0.0,
            actual=metrics.get('actual') or 0.0,
            committed=metrics.get('committed') or 0.0,
            available=metrics.get('available') or 0.0,
            actual_rate=metrics.get('actual_execution_rate') or 0.0,
            exposure_rate=metrics.get('exposure_rate') or 0.0,
            burn=metrics.get('daily_burn_rate') or 0.0,
            days_text=days_text,
            expected_date=expected_date,
            recommendation=recommendation,
            surplus_html=Markup(surplus_html),
        )

    def _prepare_weekly_budget_report_html(self, today=None):
        self.ensure_one()
        today = today or fields.Date.today()
        risky_rows = []

        for line in self.line_ids:
            metrics = self._calculate_budget_line_metrics(line, today=today)
            risk = self._get_budget_risk_level(metrics)
            if risk:
                risky_rows.append((line, metrics, risk))

        if not risky_rows:
            return False

        rows_html = ''
        risk_ar = {'medium': 'متوسط', 'high': 'مرتفع', 'critical': 'حرج'}
        for line, metrics, risk in risky_rows:
            rows_html += '''
                <tr>
                    <td>{code}</td>
                    <td>{desc}</td>
                    <td>{risk}</td>
                    <td>{approved:.2f}</td>
                    <td>{actual:.2f}</td>
                    <td>{committed:.2f}</td>
                    <td>{available:.2f}</td>
                    <td>{actual_rate:.2f}%</td>
                    <td>{exposure_rate:.2f}%</td>
                    <td>{days}</td>
                </tr>
            '''.format(
                code=line.full_code or '',
                desc=line.display_name,
                risk=risk_ar.get(risk, risk),
                approved=metrics['approved'],
                actual=metrics['actual'],
                committed=metrics['committed'],
                available=metrics['available'],
                actual_rate=metrics['actual_execution_rate'],
                exposure_rate=metrics['exposure_rate'],
                days='غير متاح' if not metrics['days_to_exhaust'] else '%.0f' % metrics['days_to_exhaust'],
            )

        return '''
        <div dir="rtl" style="text-align:right;font-family:Arial,Tahoma,sans-serif;line-height:1.8;">
            <h3>تقرير أسبوعي لحالة مراقبة الموازنة</h3>
            <p><strong>خطة الموازنة:</strong> {plan}</p>
            <p><strong>السنة المالية:</strong> {year}</p>
            <p><strong>تاريخ التقرير:</strong> {date}</p>
            <p>
                يعرض هذا التقرير البنود التي ظهرت عليها مؤشرات رقابية تتطلب المراجعة،
                سواء بسبب ارتفاع نسبة التنفيذ أو زيادة التعرض المالي الناتج عن المنصرف الفعلي والارتباطات.
            </p>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:13px;">
                <thead>
                    <tr>
                        <th>الكود</th>
                        <th>البند</th>
                        <th>المخاطر</th>
                        <th>الاعتماد</th>
                        <th>المنصرف</th>
                        <th>الارتباطات</th>
                        <th>المتاح</th>
                        <th>تنفيذ فعلي</th>
                        <th>تعرض مالي</th>
                        <th>أيام متبقية</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <p>
                التوصية العامة: يرجى مراجعة البنود عالية وحرجة المخاطر قبل اعتماد ارتباطات جديدة،
                ودراسة المناقلات أو التعزيزات وفقاً للوائح وبموافقة السلطة المختصة.
            </p>
        </div>
        '''.format(plan=self.display_name, year=self.fiscal_year, date=today, rows=rows_html)
