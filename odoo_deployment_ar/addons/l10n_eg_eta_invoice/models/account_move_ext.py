# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveEta(models.Model):
    """
    تمديد account.move بحقول ETA الفاتورة الإلكترونية
    """
    _inherit = 'account.move'

    # ── ETA fields ───────────────────────────────────────────────
    eta_invoice_ids = fields.One2many(
        'eta.invoice', 'move_id',
        string='سجلات ETA'
    )
    eta_invoice_count = fields.Integer(
        string='عدد سجلات ETA',
        compute='_compute_eta_count'
    )
    eta_state = fields.Selection(
        related='eta_invoice_ids.state',
        string='حالة ETA',
        store=False
    )
    eta_uuid = fields.Char(
        related='eta_invoice_ids.eta_uuid',
        string='ETA UUID',
        store=False
    )
    is_eta_required = fields.Boolean(
        string='تتطلب ETA',
        compute='_compute_eta_required',
        help='هل يجب إرسال هذه الفاتورة لـ ETA؟'
    )

    @api.depends('eta_invoice_ids')
    def _compute_eta_count(self):
        for rec in self:
            rec.eta_invoice_count = len(rec.eta_invoice_ids)

    @api.depends('move_type', 'state', 'partner_id')
    def _compute_eta_required(self):
        for rec in self:
            rec.is_eta_required = (
                rec.move_type in ('out_invoice', 'out_refund', 'in_invoice')
                and rec.state == 'posted'
                and bool(rec.partner_id)
            )

    def action_view_eta_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'سجلات ETA — {self.name}',
            'res_model': 'eta.invoice',
            'view_mode': 'list,form',
            'domain': [('move_id', '=', self.id)],
        }

    def action_create_eta_invoice(self):
        """إنشاء سجل ETA جديد وإرساله"""
        self.ensure_one()
        if self.state != 'posted':
            raise UserError(_('يجب ترحيل الفاتورة قبل الإرسال لـ ETA'))
        if not self.is_eta_required:
            raise UserError(_('هذه الفاتورة لا تحتاج إرسال لـ ETA'))

        # تحديد نوع المستند
        doc_type = 'I'
        if self.move_type == 'out_refund':
            doc_type = 'C'
        elif self.move_type in ('in_refund',):
            doc_type = 'D'

        eta = self.env['eta.invoice'].create({
            'move_id': self.id,
            'document_type': doc_type,
        })
        eta.action_submit()

        return {
            'type': 'ir.actions.act_window',
            'name': 'سجل ETA',
            'res_model': 'eta.invoice',
            'res_id': eta.id,
            'view_mode': 'form',
        }

    def action_send_all_to_eta(self):
        """إرسال دفعي لجميع الفواتير المرحّلة غير المُرسَلة"""
        invoices = self.filtered(
            lambda m: m.state == 'posted'
            and m.move_type in ('out_invoice', 'out_refund')
            and not m.eta_invoice_ids.filtered(lambda e: e.state in ('submitted', 'valid'))
        )
        count = 0
        for inv in invoices:
            try:
                inv.action_create_eta_invoice()
                count += 1
            except Exception as e:
                _logger = __import__('logging').getLogger(__name__)
                _logger.warning(f'ETA batch send failed for {inv.name}: {e}')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('ETA — إرسال دفعي'),
                'message': _(f'تم إرسال {count} فاتورة من أصل {len(invoices)}'),
                'type': 'success' if count == len(invoices) else 'warning',
            }
        }
