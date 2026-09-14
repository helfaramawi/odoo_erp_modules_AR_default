from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class Project(models.Model):
    _inherit = "project.project"

    x_budget_amount = fields.Monetary(
        string="Budget / الميزانية",
        currency_field="currency_id",
        help="Total approved budget for this project / إجمالي الميزانية المعتمدة",
    )
    x_budget_alert_threshold = fields.Float(
        string="Alert Threshold % / نسبة حد التنبيه",
        default=80.0,
        help="Send alert when actual spend reaches this % of budget",
    )
    x_budget_alert_sent = fields.Boolean(
        string="Alert Sent / تم إرسال التنبيه", copy=False, default=False)
    x_budget_spent = fields.Monetary(
        string="Spent / المُنفق",
        currency_field="currency_id",
        compute="_compute_budget_spent", store=True,
    )
    x_budget_remaining = fields.Monetary(
        string="Remaining / المتبقي",
        currency_field="currency_id",
        compute="_compute_budget_spent", store=True,
    )
    x_budget_pct = fields.Float(
        string="% Spent / % المُنفق",
        compute="_compute_budget_spent", store=True,
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True)

    @api.depends("x_budget_amount","analytic_account_id")
    def _compute_budget_spent(self):
        for proj in self:
            if proj.analytic_account_id and proj.x_budget_amount:
                lines = self.env["account.analytic.line"].search([
                    ("account_id","=",proj.analytic_account_id.id),
                ])
                spent = abs(sum(lines.mapped("amount")))
                proj.x_budget_spent = spent
                proj.x_budget_remaining = proj.x_budget_amount - spent
                proj.x_budget_pct = (spent / proj.x_budget_amount * 100) if proj.x_budget_amount else 0
            else:
                proj.x_budget_spent = 0
                proj.x_budget_remaining = proj.x_budget_amount
                proj.x_budget_pct = 0

    def run_budget_alerts(self):
        """Called by cron nightly. / يُستدعى بواسطة الجدولة ليلاً."""
        projects = self.search([
            ("x_budget_amount",">",0),
            ("active","=",True),
        ])
        for proj in projects:
            proj._compute_budget_spent()
            if proj.x_budget_pct >= proj.x_budget_alert_threshold and not proj.x_budget_alert_sent:
                proj._send_budget_alert()
            elif proj.x_budget_pct < proj.x_budget_alert_threshold:
                proj.x_budget_alert_sent = False  # Reset if spend drops (e.g. credit note)

    def _send_budget_alert(self):
        self.ensure_one()
        self.message_post(
            body=_(
                "<b>⚠ Budget Alert / تنبيه الميزانية</b><br/>"
                "Project <b>%(name)s</b> has reached <b>%(pct).1f%%</b> of budget.<br/>"
                "المشروع <b>%(name)s</b> وصل إلى <b>%(pct).1f%%</b> من الميزانية.<br/>"
                "Spent: %(spent)s | Budget: %(budget)s | Remaining: %(remaining)s",
                name=self.name,
                pct=self.x_budget_pct,
                spent=self.x_budget_spent,
                budget=self.x_budget_amount,
                remaining=self.x_budget_remaining,
            ),
            subtype_xmlid="mail.mt_comment",
            partner_ids=self.user_id.partner_id.ids,
        )
        self.x_budget_alert_sent = True
        _logger.info("Budget alert sent for project: %s (%.1f%%)", self.name, self.x_budget_pct)
