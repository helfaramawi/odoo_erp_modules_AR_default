# -*- coding: utf-8 -*-
from datetime import date
import calendar

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PortSaidBudgetForecast(models.Model):
    _name = 'port_said.budget.forecast'
    _description = 'توقع انحرافات الموازنة السنوية'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'forecast_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='رقم التقرير', default='New', readonly=True, copy=False)
    plan_id = fields.Many2one('port_said.budget.plan', string='الموازنة', required=True, index=True)
    fiscal_year = fields.Integer(string='السنة المالية', related='plan_id.fiscal_year', store=True)
    forecast_date = fields.Date(string='تاريخ التوقع', default=fields.Date.context_today, required=True)
    forecast_month = fields.Integer(string='شهر التوقع', required=True)
    months_elapsed = fields.Integer(string='عدد الأشهر المنقضية')
    line_ids = fields.One2many('port_said.budget.forecast.line', 'forecast_id', string='بنود التوقع')

    total_approved = fields.Monetary(string='إجمالي الاعتماد', currency_field='currency_id', compute='_compute_totals', store=True)
    total_actual_to_date = fields.Monetary(string='إجمالي الفعلي حتى تاريخه', currency_field='currency_id', compute='_compute_totals', store=True)
    total_forecast_annual = fields.Monetary(string='إجمالي المتوقع لنهاية السنة', currency_field='currency_id', compute='_compute_totals', store=True)
    total_expected_variance = fields.Monetary(string='إجمالي الانحراف المتوقع', currency_field='currency_id', compute='_compute_totals', store=True)
    total_commitments = fields.Monetary(string='إجمالي الارتباطات', currency_field='currency_id', compute='_compute_totals', store=True)
    critical_count = fields.Integer(string='بنود حرجة', compute='_compute_totals', store=True)
    warning_count = fields.Integer(string='بنود تحتاج متابعة', compute='_compute_totals', store=True)

    report_text = fields.Html(string='التقرير العربي الرسمي')
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('generated', 'تم التوليد'),
        ('reviewed', 'تمت المراجعة'),
        ('approved', 'معتمد'),
    ], string='الحالة', default='draft', tracking=True)

    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.depends('line_ids.amount_approved', 'line_ids.actual_to_date', 'line_ids.forecast_annual',
                 'line_ids.expected_variance', 'line_ids.commitments_amount', 'line_ids.risk_level')
    def _compute_totals(self):
        for rec in self:
            rec.total_approved = sum(rec.line_ids.mapped('amount_approved'))
            rec.total_actual_to_date = sum(rec.line_ids.mapped('actual_to_date'))
            rec.total_forecast_annual = sum(rec.line_ids.mapped('forecast_annual'))
            rec.total_expected_variance = sum(rec.line_ids.mapped('expected_variance'))
            rec.total_commitments = sum(rec.line_ids.mapped('commitments_amount'))
            rec.critical_count = len(rec.line_ids.filtered(lambda l: l.risk_level == 'critical'))
            rec.warning_count = len(rec.line_ids.filtered(lambda l: l.risk_level == 'warning'))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = seq.next_by_code('port_said.budget.forecast') or 'New'
        return super().create(vals_list)

    @api.model
    def action_generate_now(self):
        plan = self.env['port_said.budget.plan'].search([('state', '=', 'active')], limit=1, order='fiscal_year desc, id desc')
        if not plan:
            raise UserError(_('لا توجد موازنة نشطة لتوليد توقع الانحرافات.'))
        forecast = self.create_forecast_for_plan(plan)
        return {
            'type': 'ir.actions.act_window',
            'name': _('توقع انحرافات الموازنة'),
            'res_model': 'port_said.budget.forecast',
            'res_id': forecast.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _cron_monthly_budget_forecast(self):
        plans = self.env['port_said.budget.plan'].search([('state', '=', 'active')])
        for plan in plans:
            self.create_forecast_for_plan(plan)
        return True

    @api.model
    def create_forecast_for_plan(self, plan):
        today = fields.Date.context_today(self)
        forecast_month = today.month
        months_elapsed = max(1, forecast_month)

        forecast = self.create({
            'plan_id': plan.id,
            'forecast_date': today,
            'forecast_month': forecast_month,
            'months_elapsed': months_elapsed,
            'state': 'draft',
        })
        forecast._generate_lines()
        forecast._write_official_report()
        forecast.write({'state': 'generated'})
        forecast.message_post(body=_('تم توليد توقع انحرافات الموازنة آلياً.'))
        return forecast

    def action_recompute_forecast(self):
        for rec in self:
            rec.line_ids.unlink()
            rec._generate_lines()
            rec._write_official_report()
            rec.write({'state': 'generated'})
        return True

    def action_mark_reviewed(self):
        self.write({'state': 'reviewed'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_print_forecast_report(self):
        return self.env.ref('port_said_budget_forecast_ai_agent.action_report_budget_forecast').report_action(self)

    def _month_range(self, year, month):
        first = date(year, month, 1)
        last = date(year, month, calendar.monthrange(year, month)[1])
        return first, last

    def _generate_lines(self):
        D55 = self.env['port_said.daftar55']
        Commitment = self.env['port_said.commitment']

        for forecast in self:
            fy = forecast.plan_id.fiscal_year
            month_start, month_end = forecast._month_range(fy, forecast.forecast_month)
            year_start = date(fy, 1, 1)
            to_date = month_end

            for budget_line in forecast.plan_id.line_ids:
                code = budget_line.full_code
                amount_approved = budget_line.amount_approved or 0.0
                monthly_target = amount_approved / 12.0 if amount_approved else 0.0

                month_records = D55.search([
                    ('budget_line', '=', code),
                    ('date_received', '>=', month_start),
                    ('date_received', '<=', month_end),
                    ('state', 'in', ['posted', 'archived']),
                ])
                actual_month = sum(month_records.mapped('amount_gross'))

                ytd_records = D55.search([
                    ('budget_line', '=', code),
                    ('date_received', '>=', year_start),
                    ('date_received', '<=', to_date),
                    ('state', 'in', ['posted', 'archived']),
                ])
                actual_to_date = sum(ytd_records.mapped('amount_gross'))

                commitments = Commitment.search([
                    ('fiscal_year', '=', fy),
                    ('budget_line_code', '=', code),
                    ('state', 'in', ['approved', 'reserved', 'cleared']),
                ])
                commitments_amount = sum(commitments.mapped('amount_requested'))

                monthly_deviation_amount = actual_month - monthly_target
                monthly_deviation_pct = (monthly_deviation_amount / monthly_target * 100.0) if monthly_target else 0.0

                forecast_annual = (actual_to_date / forecast.months_elapsed * 12.0) if forecast.months_elapsed else 0.0
                expected_variance = amount_approved - forecast_annual
                expected_variance_pct = (expected_variance / amount_approved * 100.0) if amount_approved else 0.0
                projected_execution_pct = (forecast_annual / amount_approved * 100.0) if amount_approved else 0.0

                previous_alert = False
                previous_month = forecast.forecast_month - 1
                if previous_month >= 1 and monthly_target:
                    prev_start, prev_end = forecast._month_range(fy, previous_month)
                    prev_records = D55.search([
                        ('budget_line', '=', code),
                        ('date_received', '>=', prev_start),
                        ('date_received', '<=', prev_end),
                        ('state', 'in', ['posted', 'archived']),
                    ])
                    prev_actual = sum(prev_records.mapped('amount_gross'))
                    prev_dev_pct = ((prev_actual - monthly_target) / monthly_target * 100.0) if monthly_target else 0.0
                    previous_alert = abs(prev_dev_pct) >= 20 and abs(monthly_deviation_pct) >= 20

                if projected_execution_pct >= 120 or expected_variance < 0 and abs(expected_variance_pct) >= 20:
                    risk_level = 'critical'
                    risk_label = 'عجز متوقع / تجاوز حرج'
                elif previous_alert or abs(monthly_deviation_pct) >= 20 or projected_execution_pct >= 100:
                    risk_level = 'warning'
                    risk_label = 'انحراف يحتاج متابعة'
                elif projected_execution_pct <= 70 and forecast.forecast_month >= 6:
                    risk_level = 'surplus'
                    risk_label = 'فائض متوقع / بطء صرف'
                else:
                    risk_level = 'normal'
                    risk_label = 'ضمن الحدود المقبولة'

                note = forecast._line_note(
                    budget_line, monthly_deviation_pct, forecast_annual,
                    expected_variance, risk_level, risk_label
                )

                self.env['port_said.budget.forecast.line'].create({
                    'forecast_id': forecast.id,
                    'budget_line_id': budget_line.id,
                    'budget_code': code,
                    'description': budget_line.description,
                    'budget_category': budget_line.budget_category,
                    'amount_approved': amount_approved,
                    'monthly_target': monthly_target,
                    'actual_month': actual_month,
                    'actual_to_date': actual_to_date,
                    'monthly_deviation_amount': monthly_deviation_amount,
                    'monthly_deviation_pct': monthly_deviation_pct,
                    'forecast_annual': forecast_annual,
                    'expected_variance': expected_variance,
                    'expected_variance_pct': expected_variance_pct,
                    'projected_execution_pct': projected_execution_pct,
                    'commitments_amount': commitments_amount,
                    'two_months_alert': previous_alert,
                    'risk_level': risk_level,
                    'risk_label': risk_label,
                    'official_note': note,
                })

    def _line_note(self, line, monthly_dev_pct, forecast_annual, expected_variance, risk_level, risk_label):
        direction = 'زيادة في الصرف' if monthly_dev_pct > 0 else 'انخفاض في الصرف'
        variance_word = 'فائض متوقع' if expected_variance >= 0 else 'عجز متوقع'
        return (
            'البند "%s" بكود (%s) يظهر %s بنسبة %.2f%% خلال شهر التقرير. '
            'وبناءً على متوسط الصرف حتى تاريخه، فإن الصرف المتوقع بنهاية السنة يبلغ %.2f جنيه، '
            'مما ينتج عنه %s بقيمة %.2f جنيه. التصنيف الرقابي: %s.'
        ) % (
            line.description,
            line.full_code,
            direction,
            abs(monthly_dev_pct),
            forecast_annual,
            variance_word,
            abs(expected_variance),
            risk_label,
        )

    def _write_official_report(self):
        for rec in self:
            critical = rec.line_ids.filtered(lambda l: l.risk_level == 'critical')
            warning = rec.line_ids.filtered(lambda l: l.risk_level == 'warning')
            surplus = rec.line_ids.filtered(lambda l: l.risk_level == 'surplus')

            html = """
            <div dir="rtl" style="font-family: Tahoma, Arial;">
                <h3>تقرير توقع انحرافات الموازنة السنوية</h3>
                <p><strong>الموازنة:</strong> %s</p>
                <p><strong>السنة المالية:</strong> %s</p>
                <p><strong>شهر التقرير:</strong> %s</p>
                <p>
                    بناءً على بيانات الصرف الفعلي المرحلة بدفتر 55 ع.ح حتى تاريخ التقرير،
                    قام النظام بتحليل الانحرافات الشهرية ومقارنتها بالاعتماد الشهري التقديري
                    المحسوب على أساس توزيع الاعتماد السنوي على اثني عشر شهراً.
                </p>
                <h4>الملخص التنفيذي</h4>
                <ul>
                    <li>إجمالي الاعتمادات: %.2f جنيه.</li>
                    <li>إجمالي الصرف الفعلي حتى تاريخه: %.2f جنيه.</li>
                    <li>إجمالي الصرف المتوقع بنهاية السنة: %.2f جنيه.</li>
                    <li>إجمالي الانحراف المتوقع: %.2f جنيه.</li>
                    <li>عدد البنود الحرجة: %s.</li>
                    <li>عدد البنود التي تحتاج متابعة: %s.</li>
                </ul>
            """ % (
                rec.plan_id.name,
                rec.fiscal_year,
                rec.forecast_month,
                rec.total_approved,
                rec.total_actual_to_date,
                rec.total_forecast_annual,
                rec.total_expected_variance,
                rec.critical_count,
                rec.warning_count,
            )

            if critical:
                html += '<h4>أولاً: البنود المرشحة لعجز أو تجاوز حرج</h4><ul>'
                for l in critical[:10]:
                    html += '<li>%s — %s</li>' % (l.budget_code, l.official_note)
                html += '</ul>'

            if warning:
                html += '<h4>ثانياً: البنود التي تحتاج متابعة رقابية</h4><ul>'
                for l in warning[:10]:
                    html += '<li>%s — %s</li>' % (l.budget_code, l.official_note)
                html += '</ul>'

            if surplus:
                html += '<h4>ثالثاً: البنود المرشحة لفائض أو بطء صرف</h4><ul>'
                for l in surplus[:10]:
                    html += '<li>%s — %s</li>' % (l.budget_code, l.official_note)
                html += '</ul>'

            html += """
                <h4>التوصية</h4>
                <p>
                    يوصى بمراجعة البنود المصنفة كحرجة خلال اجتماع المتابعة المالي الشهري،
                    واتخاذ ما يلزم من إجراءات إعادة توزيع أو ضبط صرف أو تعزيز اعتماد وفقاً
                    للقواعد والإجراءات المعمول بها.
                </p>
            </div>
            """
            rec.report_text = html


class PortSaidBudgetForecastLine(models.Model):
    _name = 'port_said.budget.forecast.line'
    _description = 'بند توقع انحرافات الموازنة'
    _order = 'risk_level, budget_code'

    forecast_id = fields.Many2one('port_said.budget.forecast', string='تقرير التوقع', required=True, ondelete='cascade')
    budget_line_id = fields.Many2one('port_said.budget.line', string='بند الموازنة')
    budget_code = fields.Char(string='كود البند', index=True)
    description = fields.Char(string='الوصف')
    budget_category = fields.Selection([
        ('wages', 'أجور ومرتبات'),
        ('purchases', 'مشتريات وتوريدات'),
        ('services', 'خدمات'),
        ('assets', 'أصول ثابتة ومعدات'),
        ('maintenance', 'صيانة وإصلاح'),
        ('utilities', 'مرافق (كهرباء/مياه)'),
        ('other', 'بنود أخرى'),
    ], string='تصنيف البند')

    amount_approved = fields.Monetary(string='الاعتماد السنوي', currency_field='currency_id')
    monthly_target = fields.Monetary(string='المستهدف الشهري', currency_field='currency_id')
    actual_month = fields.Monetary(string='فعلي الشهر', currency_field='currency_id')
    actual_to_date = fields.Monetary(string='فعلي حتى تاريخه', currency_field='currency_id')
    monthly_deviation_amount = fields.Monetary(string='انحراف الشهر', currency_field='currency_id')
    monthly_deviation_pct = fields.Float(string='انحراف الشهر %')
    forecast_annual = fields.Monetary(string='المتوقع السنوي', currency_field='currency_id')
    expected_variance = fields.Monetary(string='الانحراف المتوقع', currency_field='currency_id')
    expected_variance_pct = fields.Float(string='الانحراف المتوقع %')
    projected_execution_pct = fields.Float(string='نسبة التنفيذ المتوقعة %')
    commitments_amount = fields.Monetary(string='الارتباطات القائمة', currency_field='currency_id')
    two_months_alert = fields.Boolean(string='انحراف شهرين متتاليين')
    risk_level = fields.Selection([
        ('critical', 'حرج'),
        ('warning', 'تحذير'),
        ('surplus', 'فائض متوقع'),
        ('normal', 'طبيعي'),
    ], string='مستوى الخطر', default='normal', index=True)
    risk_label = fields.Char(string='التصنيف الرقابي')
    official_note = fields.Text(string='ملاحظة التقرير')
    currency_id = fields.Many2one('res.currency', related='forecast_id.currency_id')
