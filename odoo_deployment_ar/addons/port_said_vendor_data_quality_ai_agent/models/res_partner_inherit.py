# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vendor_quality_id = fields.One2many(
        'port_said.vendor.data.quality',
        'partner_id',
        string='جودة بيانات المورد'
    )

    vendor_quality_score = fields.Integer(
        string='درجة جودة بيانات المورد',
        compute='_compute_vendor_quality_fields',
        store=False
    )

    vendor_quality_status = fields.Selection([
        ('valid', 'صالح للتعامل'),
        ('needs_completion', 'يحتاج استكمال'),
        ('blocked', 'موقوف رقابيًا'),
    ], string='حالة جودة المورد', compute='_compute_vendor_quality_fields', store=False)

    vendor_quality_issue_count = fields.Integer(
        string='عدد نواقص بيانات المورد',
        compute='_compute_vendor_quality_fields',
        store=False
    )

    @api.depends('vendor_quality_id.score', 'vendor_quality_id.status', 'vendor_quality_id.issue_count')
    def _compute_vendor_quality_fields(self):
        for rec in self:
            quality = rec.vendor_quality_id[:1]
            rec.vendor_quality_score = quality.score if quality else 0
            rec.vendor_quality_status = quality.status if quality else False
            rec.vendor_quality_issue_count = quality.issue_count if quality else 0

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner in partners:
            if partner.supplier_rank > 0:
                partner.sudo().action_recalculate_vendor_quality()
        return partners

    def write(self, vals):
        res = super().write(vals)
        watched_fields = {
            'name', 'vat', 'street', 'street2', 'city', 'state_id', 'country_id',
            'phone', 'mobile', 'email', 'bank_ids', 'child_ids', 'supplier_rank', 'active'
        }
        if watched_fields.intersection(vals.keys()):
            for partner in self:
                if partner.supplier_rank > 0:
                    partner.sudo().action_recalculate_vendor_quality()
        return res

    def action_recalculate_vendor_quality(self):
        Quality = self.env['port_said.vendor.data.quality'].sudo()
        for partner in self.sudo():
            if partner.supplier_rank <= 0:
                continue

            result = partner._calculate_vendor_quality()

            quality = Quality.search([('partner_id', '=', partner.id)], limit=1)
            vals = {
                'partner_id': partner.id,
                'score': result['score'],
                'status': result['status'],
                'issue_summary': result['issue_summary'],
                'recommendation': result['recommendation'],
                'missing_vat': result['missing_vat'],
                'invalid_vat': result['invalid_vat'],
                'missing_bank': result['missing_bank'],
                'missing_address': result['missing_address'],
                'missing_contact': result['missing_contact'],
                'duplicate_vat': result['duplicate_vat'],
                'open_penalties': result['open_penalties'],
                'eta_not_ready': result['eta_not_ready'],
                'open_penalty_count': result['open_penalty_count'],
                'last_check_date': fields.Datetime.now(),
                'checked_by': self.env.user.id,
            }

            if quality:
                quality.write(vals)
            else:
                quality = Quality.create(vals)

            quality.duplicate_partner_ids = [(6, 0, result['duplicate_partner_ids'])]

        return True

    def _calculate_vendor_quality(self):
        self.ensure_one()

        score = 100
        issues = []
        recommendations = []

        missing_vat = False
        invalid_vat = False
        missing_bank = False
        missing_address = False
        missing_contact = False
        duplicate_vat = False
        open_penalties = False
        eta_not_ready = False

        duplicate_partner_ids = []
        open_penalty_count = 0

        vat = (self.vat or '').strip()
        vat_digits = re.sub(r'\D+', '', vat)

        if not vat:
            missing_vat = True
            score -= 25
            issues.append('رقم التسجيل الضريبي غير مسجل.')
            recommendations.append('استكمال رقم التسجيل الضريبي قبل التعامل.')
        elif len(vat_digits) < 9:
            invalid_vat = True
            score -= 20
            issues.append('رقم التسجيل الضريبي غير صحيح أو قصير.')
            recommendations.append('مراجعة الرقم الضريبي والتحقق من صحته.')

        if vat:
            duplicates = self.env['res.partner'].sudo().search([
                ('vat', '=', vat),
                ('id', '!=', self.id),
                ('supplier_rank', '>', 0),
            ])
            if duplicates:
                duplicate_vat = True
                duplicate_partner_ids = duplicates.ids
                score -= 30
                issues.append('يوجد مورد آخر بنفس الرقم الضريبي.')
                recommendations.append('مراجعة ازدواجية الموردين قبل إصدار أوامر شراء جديدة.')

        if not self.bank_ids:
            missing_bank = True
            score -= 20
            issues.append('لا يوجد حساب بنكي مسجل للمورد.')
            recommendations.append('إضافة الحساب البنكي المعتمد للمورد.')

        if not self.street or not self.city:
            missing_address = True
            score -= 15
            issues.append('العنوان غير مكتمل.')
            recommendations.append('استكمال العنوان والمدينة وبيانات الدولة/المحافظة.')

        has_contact_person = bool(self.child_ids.filtered(lambda c: c.type in ('contact', 'other') and (c.phone or c.mobile or c.email)))
        if not has_contact_person and not (self.phone or self.mobile or self.email):
            missing_contact = True
            score -= 10
            issues.append('لا يوجد مسؤول اتصال أو بيانات تواصل واضحة.')
            recommendations.append('إضافة مسؤول اتصال أو رقم هاتف/بريد إلكتروني للمورد.')

        penalty_result = self._check_open_vendor_penalties()
        if penalty_result['count'] > 0:
            open_penalties = True
            open_penalty_count = penalty_result['count']
            score -= min(25, 10 + open_penalty_count * 5)
            issues.append('يوجد جزاءات أو ملاحظات مفتوحة على المورد بعدد %s.' % open_penalty_count)
            recommendations.append('مراجعة الجزاءات المفتوحة قبل التعامل الجديد.')

        eta_result = self._check_eta_readiness(vat_digits)
        if not eta_result['ready']:
            eta_not_ready = True
            score -= 15
            issues.append(eta_result['reason'])
            recommendations.append('استكمال بيانات الفاتورة الإلكترونية أو الرقم الضريبي قبل إصدار مستندات ETA.')

        score = max(0, min(100, score))

        min_score = self.env['port_said.vendor.data.quality.engine']._get_min_score()
        if score < min_score:
            status = 'blocked'
            recommendations.append('المورد أقل من حد الجودة المسموح به لاعتماد أوامر الشراء.')
        elif score < 80:
            status = 'needs_completion'
            recommendations.append('المورد يحتاج استكمال بيانات قبل التوسع في التعامل.')
        else:
            status = 'valid'
            recommendations.append('المورد صالح للتعامل من ناحية جودة البيانات الأساسية.')

        return {
            'score': score,
            'status': status,
            'issue_summary': '\n'.join(issues) if issues else 'لا توجد نواقص جوهرية في بيانات المورد.',
            'recommendation': '\n'.join(dict.fromkeys(recommendations)),
            'missing_vat': missing_vat,
            'invalid_vat': invalid_vat,
            'missing_bank': missing_bank,
            'missing_address': missing_address,
            'missing_contact': missing_contact,
            'duplicate_vat': duplicate_vat,
            'open_penalties': open_penalties,
            'eta_not_ready': eta_not_ready,
            'duplicate_partner_ids': duplicate_partner_ids,
            'open_penalty_count': open_penalty_count,
        }

    def _check_open_vendor_penalties(self):
        self.ensure_one()

        count = 0

        # Dynamic scan across installed penalty-related models.
        candidate_models = [
            'port_said.vendor.penalty',
            'port_said.penalty',
            'port_said.penalties',
            'penalties.said.port',
        ]

        for model_name in candidate_models:
            if model_name not in self.env:
                continue
            Model = self.env[model_name].sudo()
            partner_field = False
            for fname in ['partner_id', 'supplier_id', 'vendor_id']:
                if fname in Model._fields:
                    partner_field = fname
                    break
            if not partner_field:
                continue

            domain = [(partner_field, '=', self.id)]

            if 'state' in Model._fields:
                domain.append(('state', 'not in', ['done', 'closed', 'cancelled', 'paid']))
            elif 'active' in Model._fields:
                domain.append(('active', '=', True))

            try:
                count += Model.search_count(domain)
            except Exception:
                continue

        return {'count': count}

    def _check_eta_readiness(self, vat_digits):
        self.ensure_one()

        if not vat_digits:
            return {'ready': False, 'reason': 'المورد غير صالح للفاتورة الإلكترونية لعدم وجود رقم ضريبي.'}

        if len(vat_digits) < 9:
            return {'ready': False, 'reason': 'رقم التسجيل الضريبي غير كافٍ لاستخدامه في الفاتورة الإلكترونية.'}

        if not self.country_id:
            return {'ready': False, 'reason': 'الدولة غير محددة، مما قد يؤثر على جاهزية الفاتورة الإلكترونية.'}

        # If ETA-specific fields exist in this localization, check them lightly.
        for fname in ['l10n_eg_tax_id', 'eta_registration_number', 'eta_activity_code']:
            if fname in self._fields and not self[fname]:
                return {'ready': False, 'reason': 'بيانات ETA غير مكتملة: %s غير مسجل.' % fname}

        return {'ready': True, 'reason': 'جاهز مبدئيًا للفوترة الإلكترونية.'}
