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
        return self.env.ref("c3_aging_report.action_report_aging").report_action(
            self, data={"report_type": self.report_type, "as_of_date": str(self.as_of_date)})

    def _get_aging_data(self):
        account_type = "asset_receivable" if self.report_type == "receivable" else "liability_payable"
        domain = [("account_id.account_type","=",account_type),("reconciled","=",False),
                  ("move_id.state","=","posted"),("company_id","=",self.company_id.id)]
        if self.partner_ids:
            domain.append(("partner_id","in",self.partner_ids.ids))
        lines = self.env["account.move.line"].search(domain)
        as_of = self.as_of_date or date.today()
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
