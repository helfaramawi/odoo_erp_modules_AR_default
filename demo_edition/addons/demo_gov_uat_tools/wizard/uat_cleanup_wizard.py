# -*- coding: utf-8 -*-
"""
معالج تنظيف بيانات الحركات
يعمل في وضع التجربة الجافة افتراضياً
الحذف الفعلي يتطلب تأكيداً صريحاً

ملاحظة أمان: هذه الأداة مقيّدة بقواعد بيانات نسخة العرض التجريبي فقط
(اسم قاعدة البيانات يبدأ بـ demo_ و APP_ENV=demo) — نفس القيد المطبق في
scripts/demo-seed/demo-reset.sh. أداة تحذف بيانات الحركات (وتتجاوز حماية
unlink() على دفتر 55/224 عبر SQL مباشر) لا يجوز أبداً أن تعمل بدون هذا
القيد، خاصة أن نطاق "جميع بيانات الحركات" يحذف كل شيء بلا استثناء.
"""
import logging
import os
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

UAT_BATCH = 'UAT-AR-GOV-2026'

# Ordered list: children (leaf) models first to avoid FK violations
CLEANUP_MODELS_ORDERED = [
    # Inventory / Stock (children first)
    ('stock.issue.permit',            'أذن الصرف',                   'name'),
    ('demo_gov.warehouse.addition',   'إضافة مخزن',                  'name'),
    ('demo_gov.inspection.committee', 'لجنة الفحص والاستلام',         'name'),
    ('stock.quant',                   'كميات المخزون',                None),
    # Procurement
    ('adjudication.supplier.line',    'بند مورد البت',               'name'),
    ('procurement.adjudication',      'البت الفني والمالي',          'name'),
    ('committee.member',              'عضو لجنة',                    'name'),
    ('procurement.committee',         'لجنة المشتريات',              'name'),
    ('demo_gov.requisition.line',     'بند طلب احتياج',              None),
    ('demo_gov.requisition',          'طلب احتياج',                   'name'),
    # Commitment
    ('demo_gov.commitment',           'ارتباط',                       'name'),
    # Dossier
    ('demo_gov.dossier.attachment',   'مرفق اضبارة',                  None),
    ('demo_gov.dossier',              'اضبارة',                        'name'),
    # Disbursement / payments
    ('demo_gov.form75',               'استمارة 75',                    'name'),
    ('demo_gov.form69',               'استمارة 69',                    'name'),
    ('demo_gov.daftar224',            'دفتر 224',                      'notes'),
    ('demo_gov.daftar55',             'دفتر 55',                       'notes'),
    ('demo_gov.payment_order',        'أمر دفع',                       'purpose'),
    ('demo_gov.outgoing_po',          'أمر دفع صادر',                  'name'),
    ('demo_gov.surety',               'كفالة',                          'name'),
    ('demo_gov.cheque',               'شيك',                            'name'),
    ('demo_gov.cheque.book',          'دفتر شيكات',                    'name'),
    ('demo_gov.cash.folio',           'كشف نقدي',                      None),
    # Advances & guarantees
    ('demo_gov.bank.guarantee',       'ضمان بنكي',                     'name'),
    ('demo_gov.advance',              'سلفة',                           'name'),
    # Budget (lines before header)
    ('demo_gov.budget.line',          'بند موازنة',                    None),
    ('demo_gov.budget.plan',          'خطة موازنة',                    'name'),
    # Accounting (move lines auto-deleted with move)
    ('account.move',                  'قيد محاسبي',                    'ref'),
    # Purchase orders
    ('purchase.order.line',           'بند أمر شراء',                  None),
    ('purchase.order',                'أمر شراء',                       'name'),
    # UAT internal records (keep generation logs — they are navigation anchors)
    ('arabic.government.uat.scenario','سيناريو اختبار',                'name'),
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

    def _check_demo_environment(self):
        """Hard gate: this wizard may only ever run against a Demo Edition
        database. Mirrors the exact guard in scripts/demo-seed/demo-reset.sh
        (APP_ENV=demo + db name starting with demo_). Unlike that script,
        the original version of this tool shipped with NO such guard at
        all — added here because 'all_transactions' scope deletes every
        row with domain=[] and _force_delete() bypasses unlink() business
        rules via raw SQL for demo_gov.daftar55/daftar224. That combination
        must never be reachable outside a demo_ database, dry_run or not."""
        dbname = self.env.cr.dbname
        if not dbname.startswith('demo_') or os.environ.get('APP_ENV') != 'demo':
            raise UserError(_(
                'أداة التنظيف هذه مخصصة فقط لقواعد بيانات نسخة العرض التجريبي '
                '(Demo Edition). يجب أن يبدأ اسم قاعدة البيانات بـ demo_ وأن '
                'يكون متغير البيئة APP_ENV=demo. اسم قاعدة البيانات الحالية: '
                '"%s". تم إيقاف التنفيذ لحماية البيانات.'
            ) % dbname)

    def action_run_cleanup(self):
        self.ensure_one()
        self._check_demo_environment()

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
                with self.env.cr.savepoint(flush=False):
                    domain = self._build_domain(model_name, ref_field)
                    records = Model.search(domain)
                    count = len(records)

                    if not self.dry_run and count:
                        deleted = self._force_delete(model_name, records)
                        total_deleted += deleted
                        status = 'ok'
                        msg = f'تم حذف {deleted} سجل'
                    else:
                        status = 'ok'
                        msg = f'{count} سجل (تجربة جافة)' if self.dry_run else 'لا توجد سجلات'

                lines.append((seq, model_name, arabic_name, count, status, msg))

            except Exception as exc:
                _logger.exception('Cleanup error for %s', model_name)
                self.env.invalidate_all()  # clear ORM cache after savepoint rollback
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

        return {'type': 'ir.actions.act_window_close'}

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

    # Models whose Python unlink() always raises — use SQL bypass for UAT cleanup
    _SQL_DELETE_MODELS = {
        'demo_gov.daftar224',
        'demo_gov.daftar55',
    }

    def _force_delete(self, model_name, records):
        """Delete records, using SQL bypass for models with unconditional unlink restrictions."""
        if not records:
            return 0
        count = len(records)

        if model_name in self._SQL_DELETE_MODELS:
            # Bypass Python unlink() guard — UAT cleanup only
            table = self.env[model_name]._table
            ids = tuple(records.ids)
            if len(ids) == 1:
                self.env.cr.execute(f'DELETE FROM "{table}" WHERE id = %s', (ids[0],))
            else:
                self.env.cr.execute(f'DELETE FROM "{table}" WHERE id = ANY(%s)', (list(ids),))
            return count

        # For advance: reset to draft/cancelled first so unlink() allows it
        if model_name == 'demo_gov.advance':
            for rec in records:
                if rec.state not in ('draft', 'cancelled'):
                    try:
                        with self.env.cr.savepoint(flush=False):
                            rec.write({'state': 'cancelled'})
                    except Exception:
                        pass  # savepoint rolled back, transaction still valid

        try:
            with self.env.cr.savepoint(flush=False):
                records.unlink()
        except Exception:
            # Last resort: SQL bypass — transaction valid after savepoint rollback
            table = self.env[model_name]._table
            self.env.cr.execute(f'DELETE FROM "{table}" WHERE id = ANY(%s)', (list(records.ids),))

        return count

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
