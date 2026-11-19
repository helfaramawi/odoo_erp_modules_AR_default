# -*- coding: utf-8 -*-
import re
from collections import defaultdict
from odoo import api, models, _

class PortSaidConflictInterestEngine(models.TransientModel):
    _name = 'port_said.conflict.interest.engine'
    _description = 'محرك فحص تضارب المصالح'

    def action_run_full_scan(self):
        created = self.sudo()._run_full_scan()
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'title': _('تم تشغيل فحص تضارب المصالح'),
                           'message': _('تم إنشاء/تحديث %s تنبيه محتمل.') % created,
                           'type': 'success', 'sticky': False}}

    @api.model
    def cron_weekly_conflict_interest_scan(self):
        return self.sudo()._run_full_scan()

    @api.model
    def _run_full_scan(self):
        created = 0
        if 'procurement.adjudication' in self.env:
            for rec in self.env['procurement.adjudication'].sudo().search([]):
                created += self._scan_procurement_record(rec)
        if 'purchase.order' in self.env:
            pos = self.env['purchase.order'].sudo().search([
                ('partner_id', '!=', False), ('state', 'in', ['purchase', 'done'])
            ], limit=500)
            created += self._scan_repeated_supplier_patterns(pos)
        return created

    def _scan_procurement_record(self, rec):
        created = 0
        suppliers = self._extract_suppliers(rec)
        members = self._extract_committee_members(rec)
        committee_name = self._extract_committee_name(rec)
        for supplier in suppliers:
            for member in members:
                created += self._evaluate_pair(rec, supplier, member, committee_name)
        created += self._scan_repeated_supplier_committee(rec, suppliers, committee_name)
        return created

    def _extract_suppliers(self, rec):
        partners = self.env['res.partner'].sudo()
        for fname in ['partner_id', 'supplier_id', 'vendor_id']:
            if fname in rec._fields and rec[fname]:
                partners |= rec[fname]
        for line_field in ['supplier_line_ids','supplier_ids','bid_line_ids','offer_line_ids','line_ids','adjudication_line_ids','vendor_line_ids']:
            if line_field not in rec._fields:
                continue
            for line in rec[line_field]:
                for partner_field in ['partner_id','supplier_id','vendor_id','partner']:
                    if partner_field in line._fields and line[partner_field]:
                        partners |= line[partner_field]
        return partners

    def _extract_committee_members(self, rec):
        employees = self.env['hr.employee'].sudo()
        committee = False
        for fname in ['committee_id','procurement_committee_id','technical_committee_id','financial_committee_id']:
            if fname in rec._fields and rec[fname]:
                committee = rec[fname]
                break
        candidates = []
        if committee: candidates.append(committee)
        candidates.append(rec)
        for obj in candidates:
            for member_field in ['member_ids','committee_member_ids','members_ids','line_ids']:
                if member_field not in obj._fields:
                    continue
                for line in obj[member_field]:
                    if line._name == 'hr.employee':
                        employees |= line
                    elif 'employee_id' in line._fields and line.employee_id:
                        employees |= line.employee_id
                    elif 'partner_id' in line._fields and line.partner_id:
                        emp = self.env['hr.employee'].sudo().search([
                            '|',
                            ('work_email', '=', line.partner_id.email or '__none__'),
                            ('work_phone', '=', line.partner_id.phone or '__none__')
                        ], limit=1)
                        employees |= emp
        return employees

    def _extract_committee_name(self, rec):
        for fname in ['committee_id','procurement_committee_id','technical_committee_id','financial_committee_id']:
            if fname in rec._fields and rec[fname]:
                return rec[fname].display_name
        return rec.display_name

    def _normalize_phone(self, phone):
        return re.sub(r'\D+', '', phone or '')

    def _email_domain(self, email):
        email = (email or '').strip().lower()
        return email.split('@')[-1] if '@' in email else ''

    def _family_tokens(self, name):
        cleaned = re.sub(r'[\W_]+', ' ', name or '', flags=re.UNICODE)
        tokens = [t.strip().lower() for t in cleaned.split() if len(t.strip()) >= 4]
        ignored = {'company','office','furniture','مؤسسة','شركة','للتجارة','للمقاولات','توريدات'}
        return set(t for t in tokens if t not in ignored)

    def _evaluate_pair(self, source_record, supplier, employee, committee_name):
        risk_score, reasons, checks = 0, [], []
        sp = self._normalize_phone(supplier.phone or supplier.mobile)
        ep = self._normalize_phone(employee.work_phone or employee.mobile_phone)
        if sp and ep and sp[-8:] == ep[-8:]:
            risk_score += 40; reasons.append('تطابق أو تشابه قوي في رقم الهاتف بين المورد وعضو اللجنة.'); checks.append('phone_match')
        se = (supplier.email or '').strip().lower()
        ee = (employee.work_email or '').strip().lower()
        if se and ee and se == ee:
            risk_score += 45; reasons.append('تطابق البريد الإلكتروني بين المورد وعضو اللجنة.'); checks.append('email_match')
        sd, ed = self._email_domain(se), self._email_domain(ee)
        public_domains = {'gmail.com','yahoo.com','hotmail.com','outlook.com','icloud.com','live.com'}
        if sd and ed and sd == ed and sd not in public_domains:
            risk_score += 25; reasons.append('تطابق نطاق البريد الإلكتروني بين المورد وعضو اللجنة.'); checks.append('domain_match')
        common = self._family_tokens(supplier.name).intersection(self._family_tokens(employee.name))
        if common:
            risk_score += 20; reasons.append('وجود تشابه في الاسم/العائلة: %s.' % ', '.join(list(common)[:3])); checks.append('family_name_match')
        if risk_score >= 40:
            return self._create_alert(source_record, supplier, employee, committee_name, 'combined' if len(checks)>1 else checks[0], risk_score, '\n'.join(reasons))
        return 0

    def _scan_repeated_supplier_committee(self, rec, suppliers, committee_name):
        created = 0
        if not suppliers or not committee_name or 'procurement.adjudication' not in self.env:
            return 0
        Model = self.env['procurement.adjudication'].sudo()
        for supplier in suppliers:
            count = 0
            for old in Model.search([], limit=1000):
                if self._extract_committee_name(old) != committee_name:
                    continue
                if supplier in self._extract_suppliers(old):
                    count += 1
            if count >= 5:
                created += self._create_alert(rec, supplier, False, committee_name, 'repeated_supplier_committee',
                    min(90, 35 + count * 8),
                    'تكرر ظهور المورد مع نفس اللجنة أو نفس جهة الفحص عدد %s مرات، مما يستدعي مراجعة نمط التعامل.' % count)
        return created

    def _scan_repeated_supplier_patterns(self, purchase_orders):
        created = 0
        supplier_counts = defaultdict(int)
        for po in purchase_orders:
            supplier_counts[po.partner_id] += 1
        for supplier, count in supplier_counts.items():
            if count >= 10:
                created += self._create_alert(False, supplier, False, 'تحليل أوامر الشراء', 'historical_pattern',
                    min(85, 30 + count * 3),
                    'وجود تعاملات شراء متكررة مع المورد بعدد %s أوامر شراء. هذا مؤشر رقابي عام ويحتاج مراجعة سياق التعامل.' % count)
        return created

    def _recommendation(self, risk_score):
        if risk_score >= 80: return 'تصعيد فوري للمراجعة الداخلية مع وقف الاعتماد لحين فحص العلاقة المحتملة.'
        if risk_score >= 60: return 'مراجعة عضو اللجنة والمورد، وطلب إقرار عدم تعارض مصالح قبل الاعتماد.'
        if risk_score >= 40: return 'اعتماد مع تحفظ أو استكمال بيانات للتحقق من العلاقة المحتملة.'
        return 'متابعة دورية دون إجراء إلزامي.'

    def _create_alert(self, source_record, supplier, employee, committee_name, check_type, risk_score, reason):
        Alert = self.env['port_said.conflict.interest.alert'].sudo()
        vals = {
            'source_model': source_record._name if source_record else False,
            'source_res_id': source_record.id if source_record else 0,
            'source_display_name': source_record.display_name if source_record else 'تحليل عام',
            'committee_name': committee_name or '',
            'supplier_id': supplier.id if supplier else False,
            'supplier_name': supplier.display_name if supplier else '',
            'employee_id': employee.id if employee else False,
            'employee_name': employee.display_name if employee else '',
            'check_type': check_type,
            'risk_score': risk_score,
            'reason': reason,
            'recommendation': self._recommendation(risk_score),
        }
        existing = Alert.search([
            ('source_model', '=', vals['source_model']),
            ('source_res_id', '=', vals['source_res_id']),
            ('supplier_id', '=', vals['supplier_id']),
            ('employee_id', '=', vals['employee_id'] or False),
            ('check_type', '=', check_type),
        ], limit=1)
        if existing:
            existing.write({'risk_score': max(existing.risk_score, risk_score), 'reason': reason, 'recommendation': vals['recommendation']})
            return 0
        Alert.create(vals)
        return 1
