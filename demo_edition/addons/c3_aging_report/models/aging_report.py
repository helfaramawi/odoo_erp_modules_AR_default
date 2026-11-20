from odoo import models, fields, api, _
from datetime import date

class AgingReportWizard(models.TransientModel):
    _name = "aging.report.wizard"
    _description = "AR/AP Aging Report Wizard / معالج تقرير الأعمار"

    report_type = fields.Selection(
        [("receivable","Accounts Receivable / المدينون"),("payable","Accounts Payable / الدائنون")],
        string="Report Type / نوع التقرير", required=True, default="receivable")
    as_of_date = fields.Date(string="As of Date / حتى تاريخ", required=True, default=fields.Date.today)
    company_id = fields.Many2one("res.company", string="Company / الشركة",
        default=lambda self: self.env.company, required=True)
    partner_ids = fields.Many2many("res.partner", string="Partners / الشركاء")

    def action_print_report(self):
        # The report is printed with an explicit `data` payload (not relying on
        # `docids`): Odoo's own getReportUrl() only puts a report action's
        # `active_ids` into the download URL when `action.data` is EMPTY, so a
        # report invoked this way always receives an empty docids on the
        # server side. Every value `_get_aging_data()` needs must therefore be
        # serialized into `data` itself, not read back off `self` via docids.
        # NOTE: don't name any of these keys `company_id` -- `_get_rendering_
        # context()` merges this dict in flat (not nested), and web.external_
        # layout's own template unconditionally does
        # `<t t-if="company_id"><t t-set="company" t-value="company_id"/></t>`
        # expecting an actual res.company record there, not a bare int id.
        return self.env.ref("c3_aging_report.action_report_aging").report_action(
            self, data={
                "report_type": self.report_type,
                "as_of_date": str(self.as_of_date),
                "aging_company_id": self.company_id.id,
                "partner_ids": self.partner_ids.ids,
            })

    @api.model
    def _get_aging_data(self, data):
        report_type = data.get("report_type")
        account_type = "asset_receivable" if report_type == "receivable" else "liability_payable"
        domain = [("account_id.account_type","=",account_type),("reconciled","=",False),
                  ("move_id.state","=","posted"),("company_id","=",data.get("aging_company_id"))]
        partner_ids = data.get("partner_ids")
        if partner_ids:
            domain.append(("partner_id","in",partner_ids))
        lines = self.env["account.move.line"].search(domain)
        as_of = fields.Date.to_date(data.get("as_of_date")) or date.today()
        result = {}
        for line in lines:
            pid = line.partner_id.id
            days = (as_of - (line.date_maturity or line.date)).days
            amt = line.amount_residual
            if pid not in result:
                result[pid] = {"partner": line.partner_id.name, "current":0,"b1":0,"b2":0,"b3":0,"b4":0,"total":0}
            bucket = "current" if days<=0 else "b1" if days<=30 else "b2" if days<=60 else "b3" if days<=90 else "b4"
            result[pid][bucket] += amt
            result[pid]["total"] += amt
        return sorted(result.values(), key=lambda x: x["partner"])


class AgingReportDocument(models.AbstractModel):
    # Without this, Odoo's generic _get_rendering_context() fallback (used
    # whenever no report.<report_name> model is defined) never exposes the
    # wizard's `data` dict to the template at all -- the template's own
    # `data['report_type']` then reads `data` as an undefined QWeb variable,
    # which evaluates to None, raising "TypeError: 'NoneType' object is not
    # subscriptable" the moment the report is printed.
    _name = "report.c3_aging_report.report_aging_template"
    _description = "AR/AP Aging Report Document"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        return {
            "doc_ids": docids,
            "doc_model": "aging.report.wizard",
            "data": data,
            "lines": self.env["aging.report.wizard"]._get_aging_data(data),
        }
