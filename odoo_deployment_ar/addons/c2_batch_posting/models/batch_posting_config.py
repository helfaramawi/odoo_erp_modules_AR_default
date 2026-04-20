from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class BatchPostingConfig(models.Model):
    _name = 'batch.posting.config'
    _description = 'Batch Posting Configuration / تكوين الترحيل الدفعي'

    name = fields.Char(string='Name / الاسم', required=True, translate=True)
    active = fields.Boolean(default=True, string='Active / نشط')
    journal_ids = fields.Many2many('account.journal', string='Journals / الدفاتر')
    company_id = fields.Many2one('res.company', string='Company / الشركة',
        default=lambda self: self.env.company, required=True)
    last_run = fields.Datetime(string='Last Run / آخر تشغيل', readonly=True)
    last_run_count = fields.Integer(string='Posted / مُرحَّل', readonly=True)
    last_run_errors = fields.Integer(string='Errors / أخطاء', readonly=True)

    def run_batch_posting(self):
        configs = self.search([('active', '=', True)])
        for config in configs:
            config._do_batch_post()

    def _do_batch_post(self):
        self.ensure_one()
        domain = [('state', '=', 'draft'), ('company_id', '=', self.company_id.id)]
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        moves = self.env['account.move'].search(domain)
        posted = errors = 0
        for move in moves:
            try:
                move.action_post()
                posted += 1
            except Exception as e:
                errors += 1
                _logger.warning('Batch post failed %s: %s', move.name, e)
        self.write({'last_run': fields.Datetime.now(), 'last_run_count': posted, 'last_run_errors': errors})
        _logger.info('Batch posting: %d posted, %d errors', posted, errors)
        return {'posted': posted, 'errors': errors}

    def action_run_now(self):
        result = self._do_batch_post()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Batch Posting Complete / اكتمل الترحيل الدفعي'),
                'message': _('Posted: %(posted)d | Errors: %(errors)d', posted=result['posted'], errors=result['errors']),
                'sticky': False,
                'type': 'success' if not result['errors'] else 'warning',
            },
        }
