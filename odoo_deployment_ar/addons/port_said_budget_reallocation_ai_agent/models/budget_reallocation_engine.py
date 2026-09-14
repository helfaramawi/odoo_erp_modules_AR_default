# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PortSaidBudgetReallocationEngine(models.TransientModel):
    _name = 'port_said.budget.reallocation.engine'
    _description = 'محرك توصية إعادة توزيع الاعتمادات'

    @api.model
    def _param_float(self, key, default):
        try:
            return float(self.env['ir.config_parameter'].sudo().get_param(key, default))
        except Exception:
            return float(default)

    def action_run_recommendation_now(self):
        count = self.sudo().run_reallocation_recommendations()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('تم تشغيل توصيات إعادة توزيع الاعتمادات'),
                'message': _('تم إنشاء/تحديث %s توصية.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_monthly_budget_reallocation_recommendation(self):
        return self.sudo().run_reallocation_recommendations()

    @api.model
    def run_reallocation_recommendations(self):
        if 'port_said.budget.forecast' in self.env:
            forecasts = self.env['port_said.budget.forecast'].sudo().search([], order='create_date desc', limit=5)
            total = 0
            for forecast in forecasts:
                total += self._recommend_from_forecast(forecast)
            if total:
                return total
        return self._recommend_from_budget_plans()

    def _safe_amount(self, rec, names):
        for fname in names:
            if fname in rec._fields:
                try:
                    return float(rec[fname] or 0.0)
                except Exception:
                    return 0.0
        return 0.0

    def _recommend_from_forecast(self, forecast):
        line_field = False
        for fname in ['line_ids', 'forecast_line_ids']:
            if fname in forecast._fields:
                line_field = fname
                break
        if not line_field:
            return 0

        budget_plan = self._forecast_budget_plan(forecast)
        deficits, surpluses = [], []

        for line in forecast[line_field]:
            variance = self._safe_amount(line, ['expected_variance', 'projected_variance', 'variance', 'forecast_variance'])
            budget_line = self._line_budget_line(line)
            if not budget_line:
                continue
            if variance < 0:
                deficits.append((budget_line, abs(variance)))
            elif variance > 0:
                surpluses.append((budget_line, variance))

        count = 0
        for deficit_line, needed in deficits:
            count += self._match_surplus_to_deficit(budget_plan, forecast, surpluses, deficit_line, needed, 'forecast')
        return count

    def _recommend_from_budget_plans(self):
        Plan = self.env['port_said.budget.plan'].sudo()
        plan_domain = []
        if 'state' in Plan._fields:
            plan_domain.append(('state', 'in', ['active', 'approved', 'open']))
        plans = Plan.search(plan_domain, limit=5)

        Line = self.env['port_said.budget.line'].sudo()
        count = 0

        for plan in plans:
            if 'line_ids' in plan._fields:
                lines = plan.line_ids
            elif 'plan_id' in Line._fields:
                lines = Line.search([('plan_id', '=', plan.id)])
            else:
                lines = Line.search([], limit=1000)

            deficits, surpluses = [], []
            for line in lines:
                approved = self._safe_amount(line, ['amount_approved', 'approved_amount', 'budget_amount'])
                actual = self._safe_amount(line, ['amount_actual', 'actual_amount'])
                committed = self._safe_amount(line, ['amount_committed', 'committed_amount'])
                expected_balance = approved - actual - committed

                if expected_balance < 0:
                    deficits.append((line, abs(expected_balance)))
                elif expected_balance > approved * 0.20 and expected_balance > self._param_float('port_said_budget_reallocation.min_surplus_amount', 10000):
                    surpluses.append((line, expected_balance))

            for deficit_line, needed in deficits:
                count += self._match_surplus_to_deficit(plan, False, surpluses, deficit_line, needed, 'direct_budget_analysis')

        return count

    def _match_surplus_to_deficit(self, budget_plan, forecast, surpluses, deficit_line, needed, source_type):
        count = 0
        max_ratio = self._param_float('port_said_budget_reallocation.transfer_ratio', 0.80)
        min_amount = self._param_float('port_said_budget_reallocation.min_recommendation_amount', 1000)
        remaining_need = needed

        for surplus_line, surplus_amount in surpluses:
            if remaining_need <= 0:
                break
            if surplus_line.id == deficit_line.id:
                continue
            if not self._same_budget_category(deficit_line, surplus_line):
                continue
            if self._is_restricted_line(surplus_line) or self._is_restricted_line(deficit_line):
                continue

            transferable = surplus_amount * max_ratio
            amount = min(remaining_need, transferable)

            if amount < min_amount:
                continue

            count += self._create_recommendation(
                budget_plan=budget_plan,
                forecast=forecast,
                from_line=surplus_line,
                to_line=deficit_line,
                surplus_amount=surplus_amount,
                deficit_amount=needed,
                transferable_amount=transferable,
                recommended_amount=amount,
                source_type=source_type,
            )
            remaining_need -= amount

        return count

    def _create_recommendation(self, budget_plan, forecast, from_line, to_line, surplus_amount, deficit_amount,
                               transferable_amount, recommended_amount, source_type):
        Rec = self.env['port_said.budget.reallocation.recommendation'].sudo()

        confidence = self._confidence(from_line, to_line, surplus_amount, deficit_amount, recommended_amount)
        priority = self._priority(deficit_amount, recommended_amount)

        vals = {
            'source_type': source_type,
            'source_forecast_model': forecast._name if forecast else False,
            'source_forecast_id': forecast.id if forecast else 0,
            'budget_plan_id': budget_plan.id if budget_plan else False,
            'from_budget_line_id': from_line.id,
            'to_budget_line_id': to_line.id,
            'from_budget_code': self._line_code(from_line),
            'from_budget_name': self._line_name(from_line),
            'from_budget_category': self._line_category(from_line),
            'to_budget_code': self._line_code(to_line),
            'to_budget_name': self._line_name(to_line),
            'to_budget_category': self._line_category(to_line),
            'surplus_amount': surplus_amount,
            'deficit_amount': deficit_amount,
            'transferable_amount': transferable_amount,
            'recommended_amount': recommended_amount,
            'confidence_score': confidence,
            'priority': priority,
            'reason': self._reason(from_line, to_line, surplus_amount, deficit_amount, recommended_amount),
            'official_memo': self._official_memo(budget_plan, from_line, to_line, surplus_amount, deficit_amount, recommended_amount, confidence),
        }

        existing = Rec.search([
            ('budget_plan_id', '=', budget_plan.id if budget_plan else False),
            ('from_budget_line_id', '=', from_line.id),
            ('to_budget_line_id', '=', to_line.id),
            ('state', 'in', ['draft', 'to_review']),
        ], limit=1)

        if existing:
            existing.write(vals)
            return 0

        Rec.create(vals)
        return 1

    def _forecast_budget_plan(self, forecast):
        for fname in ['budget_plan_id', 'plan_id']:
            if fname in forecast._fields and forecast[fname]:
                return forecast[fname]
        return False

    def _line_budget_line(self, forecast_line):
        for fname in ['budget_line_id', 'line_id']:
            if fname in forecast_line._fields and forecast_line[fname] and forecast_line[fname]._name == 'port_said.budget.line':
                return forecast_line[fname]
        return False

    def _line_code(self, line):
        for fname in ['full_code', 'code', 'budget_line', 'budget_code']:
            if fname in line._fields and line[fname]:
                return str(line[fname])
        return str(line.id)

    def _line_name(self, line):
        for fname in ['description', 'name']:
            if fname in line._fields and line[fname]:
                return str(line[fname])
        return line.display_name

    def _line_category(self, line):
        for fname in ['budget_category', 'category', 'budget_chapter', 'chapter']:
            if fname in line._fields and line[fname]:
                val = line[fname]
                return val.display_name if hasattr(val, 'display_name') else str(val)
        code = self._line_code(line)
        return code[:2] if code else ''

    def _same_budget_category(self, a, b):
        return self._line_category(a) == self._line_category(b)

    def _is_restricted_line(self, line):
        text = ('%s %s %s' % (self._line_code(line), self._line_name(line), self._line_category(line))).lower()
        restricted = ['مرتبات', 'أجور', 'رواتب', 'wages', 'salary', 'salaries', 'قروض', 'فوائد', 'debt']
        return any(word.lower() in text for word in restricted)

    def _confidence(self, from_line, to_line, surplus_amount, deficit_amount, recommended_amount):
        score = 60.0
        if self._same_budget_category(from_line, to_line):
            score += 20.0
        if recommended_amount <= surplus_amount * 0.80:
            score += 10.0
        if recommended_amount <= deficit_amount:
            score += 10.0
        return min(100.0, score)

    def _priority(self, deficit_amount, recommended_amount):
        ratio = recommended_amount / deficit_amount if deficit_amount else 0.0
        if deficit_amount >= 100000 and ratio >= 0.75:
            return 'critical'
        if deficit_amount >= 50000:
            return 'high'
        if deficit_amount >= 10000:
            return 'medium'
        return 'low'

    def _reason(self, from_line, to_line, surplus_amount, deficit_amount, recommended_amount):
        return (
            'تم رصد عجز متوقع في البند "%s" بقيمة %.2f، مع وجود فائض متوقع في البند "%s" بقيمة %.2f. '
            'يقترح الوكيل تحويل مبلغ %.2f من بند الفائض إلى بند العجز، دون تنفيذ فعلي، لحين المراجعة والاعتماد.'
        ) % (self._line_name(to_line), deficit_amount, self._line_name(from_line), surplus_amount, recommended_amount)

    def _official_memo(self, budget_plan, from_line, to_line, surplus_amount, deficit_amount, recommended_amount, confidence):
        plan_name = budget_plan.display_name if budget_plan else 'خطة الموازنة الحالية'
        return """
        <div dir="rtl" style="font-family: Arial, sans-serif; line-height: 1.8;">
            <h3>مذكرة توصية بإعادة توزيع اعتماد</h3>
            <p><strong>خطة الموازنة:</strong> %s</p>
            <p><strong>الموضوع:</strong> توصية بإعادة توزيع جزئي للاعتمادات في ضوء مؤشرات العجز والفائض المتوقعة.</p>
            <table class="table table-sm table-bordered">
                <tr><th>من بند فائض</th><td>%s - %s</td></tr>
                <tr><th>إلى بند عجز</th><td>%s - %s</td></tr>
                <tr><th>الفائض المتوقع</th><td>%.2f</td></tr>
                <tr><th>العجز المتوقع</th><td>%.2f</td></tr>
                <tr><th>القيمة المقترحة للتحويل</th><td>%.2f</td></tr>
                <tr><th>درجة الثقة</th><td>%.2f%%</td></tr>
            </table>
            <p><strong>مبرر التوصية:</strong> تهدف التوصية إلى تقليل العجز المتوقع قبل نهاية السنة المالية، وتحسين كفاءة استخدام الاعتمادات دون تنفيذ أي تحويل فعلي إلا بعد المراجعة والاعتماد الرسمي.</p>
            <p><strong>تنبيه رقابي:</strong> هذه التوصية لا تمثل قيدًا أو تحويلًا فعليًا، وإنما مذكرة مساعدة لاتخاذ القرار المالي.</p>
        </div>
        """ % (
            plan_name,
            self._line_code(from_line), self._line_name(from_line),
            self._line_code(to_line), self._line_name(to_line),
            surplus_amount,
            deficit_amount,
            recommended_amount,
            confidence,
        )
