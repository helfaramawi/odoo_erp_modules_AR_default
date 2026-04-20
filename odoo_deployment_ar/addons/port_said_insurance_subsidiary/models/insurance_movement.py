# -*- coding: utf-8 -*-
"""
حركة تأمين (Insurance Movement)
=================================
سجل لكل حدث يؤثر على فولية دفتر التأمينات:
- deposit (إيداع): استلام تأمين جديد
- withdrawal (استرداد): إفراج
- forfeiture (مصادرة): تحويل إلى الإيرادات

هذا النموذج هو المصدر الذي يقرأ منه قالب طباعة الفولية (QWeb).
"""
from odoo import models, fields, api, _


class InsuranceMovement(models.Model):
    _name = 'port_said.insurance.movement'
    _description = 'حركة تأمين'
    _order = 'movement_date desc, id desc'

    # ── الهوية ───────────────────────────────────────────────────────────────
    movement_type = fields.Selection([
        ('deposit',    'إيداع'),
        ('withdrawal', 'استرداد / إفراج'),
        ('forfeiture', 'مصادرة'),
    ], string='نوع الحركة', required=True, index=True)

    movement_date = fields.Date(string='تاريخ الحركة', required=True, index=True)

    # ── الطرف ───────────────────────────────────────────────────────────────
    partner_id = fields.Many2one('res.partner', string='المورد / المقاول',
        required=True, index=True)

    # ── تصنيف الضمانة ───────────────────────────────────────────────────────
    collateral_type = fields.Selection([
        ('cash',     'نقدية'),
        ('cheque',   'شيك'),
        ('guarantee','خطاب ضمان'),
    ], string='صيغة الضمانة', required=True, index=True)

    # ── الربط (واحد فقط يُستخدم حسب النوع) ──────────────────────────────────
    bank_guarantee_id = fields.Many2one('port_said.bank.guarantee',
        string='خطاب الضمان', ondelete='cascade', index=True)
    insurance_deposit_id = fields.Many2one('port_said.insurance_deposit',
        string='إيداع التأمين', ondelete='cascade', index=True)

    # ── المبلغ ──────────────────────────────────────────────────────────────
    amount = fields.Monetary(string='المبلغ', required=True,
        currency_field='currency_id')
    currency_id = fields.Many2one('res.currency',
        default=lambda s: s.env.company.currency_id)

    description = fields.Char(string='البيان', required=True)

    # ── ربط بفولية شهرية ────────────────────────────────────────────────────
    folio_id = fields.Many2one('port_said.insurance.folio',
        string='الفولية', index=True,
        help='تُسنَد تلقائياً عند إنشاء الفولية الشهرية.')

    company_id = fields.Many2one('res.company',
        default=lambda s: s.env.company)

    def name_get(self):
        return [(rec.id, '%s — %s — %s — %s' % (
            dict(self._fields['movement_type'].selection).get(rec.movement_type),
            rec.partner_id.name or '—',
            rec.movement_date,
            rec.amount,
        )) for rec in self]
