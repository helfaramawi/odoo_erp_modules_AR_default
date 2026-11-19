from odoo import models, fields, api, _
from odoo.exceptions import UserError
import hashlib
import os
import requests
import logging
_logger = logging.getLogger(__name__)

CREDIT_STATES = [
    ("not_checked", "Not Checked / غير محقق"),
    ("green", "Green - OK / أخضر"),
    ("amber", "Amber - Warning / عنبري"),
    ("red", "Red - Blocked / أحمر"),
    ("api_error", "API Error / خطأ في الواجهة"),
]

class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_check_state = fields.Selection(
        CREDIT_STATES, string="Credit Status / حالة الائتمان",
        default="not_checked", tracking=True, copy=False)
    credit_score = fields.Integer(string="Credit Score / درجة الائتمان", readonly=True, copy=False)
    credit_override_reason = fields.Text(string="Override Reason / سبب التجاوز", copy=False)
    credit_checked_by = fields.Many2one("res.users", readonly=True, copy=False)

    def action_credit_check(self):
        self.ensure_one()
        config = self.env["credit.bureau.config"].search(
            [("active","=",True),("company_id","=",self.company_id.id)], limit=1)
        if not config:
            raise UserError(_("No Credit Bureau API configuration found."))

        score = self._call_credit_api(config)
        if score is None:
            self.write({"credit_check_state": "api_error"})
            return

        if score >= config.green_threshold:
            state = "green"
        elif score >= config.amber_threshold:
            state = "amber"
        else:
            state = "red"

        self.write({
            "credit_score": score,
            "credit_check_state": state,
            "credit_checked_by": self.env.user.id,
        })
        self.message_post(body=_("Credit check: score=%d state=%s") % (score, state))

        if state == "red" and not self.credit_override_reason:
            raise UserError(_("Credit check FAILED (score: %d). Override reason required.") % score)

    def _is_demo_environment(self):
        if os.environ.get('APP_ENV') == 'demo':
            return True
        try:
            return self.env['demo.branding'].sudo().is_demo_environment()
        except KeyError:
            # demo_branding not installed alongside this module - default safe
            return False

    def _call_credit_api(self, config):
        if self._is_demo_environment():
            # Demo Edition never calls a real Credit Bureau endpoint.
            # Return a deterministic synthetic score so the workflow is
            # still demonstrable (same partner -> same score every run).
            digest = hashlib.sha256(str(self.partner_id.id).encode()).hexdigest()
            score = 300 + (int(digest[:8], 16) % 601)  # 300-900 range
            self.message_post(body=_(
                "DEMO MODE — Credit Bureau check simulated (no external API "
                "call made). Synthetic score: %d"
            ) % score)
            return score
        try:
            resp = requests.get(
                "%s/check" % config.api_url,
                params={"partner_vat": self.partner_id.vat or "", "partner_id": self.partner_id.id},
                headers={"Authorization": "Bearer %s" % config.api_key},
                timeout=config.timeout,
            )
            resp.raise_for_status()
            return resp.json().get("score")
        except Exception as e:
            _logger.warning("Credit Bureau API error: %s", e)
            self.message_post(body=_("Credit Bureau API unreachable: %s") % str(e))
            return None

    def action_confirm(self):
        for order in self:
            if order.credit_check_state == "red" and not order.credit_override_reason:
                raise UserError(_("Cannot confirm: customer credit is RED. Provide an override reason."))
        return super().action_confirm()
