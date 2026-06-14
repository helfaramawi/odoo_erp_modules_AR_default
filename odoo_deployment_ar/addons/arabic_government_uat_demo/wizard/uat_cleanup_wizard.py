# -*- coding: utf-8 -*-
"""
معالج تنظيف بيانات الحركات
يعمل في وضع التجربة الجافة افتراضياً
الحذف الفعلي يتطلب تأكيداً صريحاً
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

UAT_BATCH = 'UAT-AR-GOV-2026'

# Ordered list: children (leaf) models first to avoid FK violations
CLEANUP_MODELS_ORDERED = [
    # Inventory / Stock (children first)
    ('stock.issue.permit',            'أذن الصرف',                   'name'),
    ('port_said.warehouse_addition',  'إضافة مخزن',                  'name'),
    ('port_said.inspection_committee','لجنة الفحص والاستلام',         'name'),
    ('stock.quant',                   'كميات المخزون',                None),
    # Procurement
    ('adjudication.supplier.line',    'بند مورد البت',               'name'),
    ('procurement.adjudication',      'البت الفني والمالي',          'name'),
    ('committee.member',              'عضو لجنة',                    'name'),
    ('procurement.committee',         'لجنة المشتريات',              'name'),
    ('port_said.requisition.line',    'بند طلب احتياج',              None),
    ('port_said.requisition',         'طلب احتياج',                   'name'),
    # Commitment
    ('port_said.commitment',          'ارتباط',                       'name'),
    # Dossier
    ('port_said.dossier.attachment',  'مرفق اضبارة',                  None),
    ('port_said.dossier',             'اضبارة',                        'name'),
    # Disbursement / payments
    ('port_said.form75',              'استمارة 75',                    'name'),
    ('port_said.form69',              'استمارة 69',                    'name'),
    ('port_said.daftar224',           'دفتر 224',                      'name'),
    ('port_said.daftar55',            'دفتر 55',                       'name'),
    ('port_said.payment_order',       'أمر دفع',                       'name'),
    ('port_said.outgoing_po',         'أمر دفع صادر',                  'name'),
    ('port_said.surety',              'كفالة',                          'name'),
    ('port_said.cheque',              'شيك',                            'name'),
    ('port_said.cheque.book',         'دفتر شيكات',                    'name'),
    ('port_said.cash.folio',          'كشف نقدي',                      None),
    # Advances & guarantees
    ('port_said.bank.guarantee',      'ضمان بنكي',                     'name'),
    ('port_said.advance',             'سلفة',                           'name'),
    # Budget (lines before header)
    ('port_said.budget.line',         'بند موازنة',                    None),
    ('port_said.budget.plan',         'خطة موازنة',                    'name'),
    # Accounting (move lines auto-deleted with move)
    ('account.move',                  'قيد محاسبي',                    'ref'),
    # Purchase orders
    ('purchase.order.line',           'بند أمر شراء',                  None),
    ('purchase.order',                'أمر شراء',                       'name'),
    # UAT internal records
    ('arabic.government.uat.scenario','سيناريو اختبار',                'name'),
    ('arabic.government.uat.generation.log.line', 'بند سجل التوليد',  None),
    ('arabic.government.uat.generation.log',      'سجل التوليد',       'name'),
]


class UATCleanupWizard(models.TransientModel):
    _name = 'arabic.government.uat.cleanup.wizard'
    _description = 'معالج تنظيف بيانات الحركات'

    dry_run = fields.Boolean(
        'تجربة جافة (بدون حذف فعلي)',
        default=True,
        help='في وضع التجربة الجافة يُعرض عدد السجلات فقط دون حذف',
    )
    confirm_cleanup = fields.Boolean(
        'تأكيد التنظيف الفعلي',
        default=False,
        help='يجب تفعيل هذا الخيار للحذف الفعلي عند إيقاف التجربة الجافة',
    )
    cleanup_scope = fields.Selection([
        ('uat_only', 'بيانات UAT-AR-GOV-2026 فقط'),
        ('all_transactions', '⚠ جميع بيانات الحركات (خطر)'),
    ], string='نطاق التنظيف', default='uat_only', required=True)
    reset_sequences = fields.Boolean('إعادة تعيين تسلسلات الحركات', default=False)
    cleanup_attachments = fields.Boolean('حذف المرفقات المرتبطة بالحركات', default=False)
    cleanup_ai_logs = fields.Boolean('حذف سجلات الذكاء الاصطناعي', default=False)
    notes = fields.Text('ملاحظات')
    warning_message = fields.Text(
        'تحذير', compute='_compute_warning', store=False
    )

    @api.depends('dry_run', 'cleanup_scope', 'confirm_cleanup')
    def _compute_warning(self):
        for rec in self:
            if not rec.dry_run and not rec.confirm_cleanup:
                rec.warning_message = '⚠ يجب تفعيل "تأكيد التنظيف الفعلي" للمتابعة'
            elif rec.cleanup_scope == 'all_transactions' and not rec.dry_run:
                rec.warning_message = (
                    '🚨 تحذير شديد: سيتم حذف جميع بيانات الحركات نهائياً.\n'
                    'هذا الإجراء لا يمكن التراجع عنه.'
                )
            elif not rec.dry_run:
                rec.warning_message = '⚠ سيتم حذف السجلات فعلياً. تأكد من أخذ نسخة احتياطية.'
            else:
                rec.warning_message = 'ℹ وضع التجربة الجافة: لن يتم حذف أي سجلات.'

    def action_run_cleanup(self):
        self.ensure_one()

        # Safety gate
        if not self.dry_run and not self.confirm_cleanup:
            raise UserError(
                'يجب تفعيل خيار "تأكيد التنظيف الفعلي" قبل المتابعة.\n'
                'هذا الإجراء يحذف البيانات نهائياً.'
            )

        # Create log record
        log = self.env['arabic.government.uat.cleanup.log'].create({
            'dry_run': self.dry_run,
            'cleanup_scope': self.cleanup_scope,
            'notes': self.notes or '',
        })

        total_deleted = 0
        lines = []
        seq = 10

        for model_name, arabic_name, ref_field in CLEANUP_MODELS_ORDERED:
            Model = self.env.get(model_name)
            if Model is None:
                lines.append((seq, model_name, arabic_name, 0, 'skipped', 'النموذج غير موجود'))
                seq += 10
                continue

            try:
                domain = self._build_domain(model_name, ref_field)
                records = Model.search(domain)
                count = len(records)

                if not self.dry_run and count:
                    records.unlink()
                    total_deleted += count
                    status = 'ok'
                    msg = f'تم حذف {count} سجل'
                else:
                    status = 'ok'
                    msg = f'{count} سجل (تجربة جافة)' if self.dry_run else 'لا توجد سجلات'

                lines.append((seq, model_name, arabic_name, count, status, msg))

            except Exception as exc:
                _logger.exception('Cleanup error for %s', model_name)
                lines.append((seq, model_name, arabic_name, 0, 'error', str(exc)[:200]))

            seq += 10

        # Cleanup attachments if requested
        if self.cleanup_attachments and not self.dry_run:
            self._cleanup_attachments()

        # Write log lines
        for s, mn, an, rc, st, ms in lines:
            self.env['arabic.government.uat.cleanup.log.line'].create({
                'log_id': log.id, 'sequence': s,
                'model_name': mn, 'arabic_name': an,
                'record_count': rc, 'status': st, 'message': ms,
            })

        summary_lines = [
            f'• {l[2]} ({l[1]}): {l[3]} سجل — {l[5]}'
            for l in lines if l[3] > 0 or l[4] == 'error'
        ]
        mode = 'تجربة جافة' if self.dry_run else 'حذف فعلي'
        summary = (
            f'وضع التشغيل: {mode}\n'
            f'النطاق: {dict(self._fields["cleanup_scope"].selection)[self.cleanup_scope]}\n'
            f'إجمالي السجلات: {total_deleted}\n\n'
            + ('\n'.join(summary_lines) or 'لا توجد سجلات تطابق النطاق المحدد')
        )

        log.write({
            'result_summary': summary,
            'total_deleted': total_deleted,
            'state': 'done',
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'نتيجة التنظيف',
            'res_model': 'arabic.government.uat.cleanup.log',
            'res_id': log.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _build_domain(self, model_name, ref_field):
        """Build search domain based on cleanup scope."""
        if self.cleanup_scope == 'all_transactions':
            return []  # all records
        # uat_only: search for UAT batch reference in name/ref fields
        if ref_field and ref_field in self.env[model_name]._fields:
            return [(ref_field, 'ilike', UAT_BATCH)]
        # Fallback: try common fields
        Model = self.env[model_name]
        for f in ('name', 'ref', 'notes', 'description', 'origin'):
            if f in Model._fields:
                return [(f, 'ilike', UAT_BATCH)]
        return [('id', '=', -1)]  # match nothing if no searchable field

    def _cleanup_attachments(self):
        """Remove ir.attachment records linked to deleted models."""
        try:
            model_names = [m[0] for m in CLEANUP_MODELS_ORDERED]
            attachments = self.env['ir.attachment'].search([
                ('res_model', 'in', model_names),
            ])
            attachments.unlink()
        except Exception as e:
            _logger.warning('Attachment cleanup failed: %s', e)
