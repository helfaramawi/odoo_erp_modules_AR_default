# -*- coding: utf-8 -*-
"""
ساحر استيراد البيانات الورقية التاريخية
========================================
يستورد أرصدة الفوليوهات الورقية الموجودة قبل بدء التشغيل الإلكتروني.
يُنشئ فوليوهات حالة 'archived' برصيد افتتاحي يدوي وبدون سطور محاسبية.
الهدف: السنة الأولى الإلكترونية تبدأ من الرصيد الصحيح في 1 يوليو.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import csv
import base64
import io


class MigratePaperWizard(models.TransientModel):
    _name = 'port_said.subsidiary.migrate.paper.wizard'
    _description = 'استيراد الفوليوهات الورقية التاريخية'

    book_id = fields.Many2one('port_said.subsidiary.book',
                               string='الدفتر', required=True)
    fiscal_year = fields.Char(string='السنة المالية المغلقة', required=True,
                               help='السنة المالية المنتهية، مثلاً 2023/2024 — '
                                    'سيتم إنشاء فوليوهات يونيو 30 منها كرصيد افتتاحي.')
    csv_file = fields.Binary(string='ملف CSV',
        help='تنسيق CSV: partner_code,account_code,closing_balance')
    csv_filename = fields.Char()
    log = fields.Text(string='سجل العملية', readonly=True)

    def action_import(self):
        self.ensure_one()
        if not self.csv_file:
            raise UserError(_('ارفع ملف CSV.'))

        decoded = base64.b64decode(self.csv_file).decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))

        Folio = self.env['port_said.subsidiary.folio']
        Partner = self.env['res.partner']
        Account = self.env['account.account']

        created, skipped, errors = 0, 0, []
        for row_num, row in enumerate(reader, start=2):
            try:
                partner_id = False
                account_id = False
                if row.get('partner_code'):
                    p = Partner.search([('ref', '=', row['partner_code'])], limit=1)
                    if not p:
                        errors.append(_('السطر %d: شريك غير موجود (%s)') %
                                       (row_num, row['partner_code']))
                        continue
                    partner_id = p.id
                if row.get('account_code'):
                    a = Account.search([('code', '=', row['account_code'])], limit=1)
                    if not a:
                        errors.append(_('السطر %d: حساب غير موجود (%s)') %
                                       (row_num, row['account_code']))
                        continue
                    account_id = a.id

                # 30 يونيو من السنة المنتهية
                fy_end_year = int(self.fiscal_year.split('/')[1])
                from datetime import date
                date_to = date(fy_end_year, 6, 30)
                date_from = date(fy_end_year, 6, 1)

                # تخطَّ المكرر
                exists = Folio.search([
                    ('book_id', '=', self.book_id.id),
                    ('fiscal_year', '=', self.fiscal_year),
                    ('period_month', '=', '06'),
                    ('partner_id', '=', partner_id or False),
                    ('account_id', '=', account_id or False),
                ], limit=1)
                if exists:
                    skipped += 1
                    continue

                folio = Folio.create({
                    'book_id': self.book_id.id,
                    'fiscal_year': self.fiscal_year,
                    'period_month': '06',
                    'date_from': date_from,
                    'date_to': date_to,
                    'partner_id': partner_id,
                    'account_id': account_id,
                    'opening_balance': float(row.get('closing_balance', 0)),
                    'notes': _('استيراد من البيانات الورقية التاريخية.'),
                })
                # نقل مباشر إلى archived (لا تُعدَّل)
                folio.write({
                    'state': 'archived',
                    'crossout_signed_by': _('استيراد ورقي'),
                    'accounts_head_signed_by': _('استيراد ورقي'),
                    'closed_by': self.env.user.id,
                    'closed_date': fields.Datetime.now(),
                })
                created += 1
            except Exception as e:
                errors.append(_('السطر %d: %s') % (row_num, str(e)))

        self.log = _(
            'تم الإنشاء: %d فولية\nتم التخطي (مكرر): %d\nأخطاء: %d\n\n%s'
        ) % (created, skipped, len(errors), '\n'.join(errors[:50]))
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
