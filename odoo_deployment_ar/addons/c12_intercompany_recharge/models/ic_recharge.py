from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ICRechargeRule(models.Model):
    """
    Inter-company recharge rule: defines how costs are recharged between entities.
    قاعدة إعادة التوزيع: تحدد كيفية إعادة توزيع التكاليف بين الكيانات.
    """
    _name = "ic.recharge.rule"
    _description = "IC Recharge Rule / قاعدة إعادة التوزيع"

    name = fields.Char(string="Rule Name / اسم القاعدة", required=True, translate=True)
    source_company_id = fields.Many2one("res.company", string="Source Company / الشركة المصدر", required=True)
    target_company_id = fields.Many2one("res.company", string="Target Company / الشركة الهدف", required=True)
    source_account_id = fields.Many2one("account.account", string="Source Account / الحساب المصدر", required=True,
        domain="[('company_id','=',source_company_id)]")
    target_account_id = fields.Many2one("account.account", string="Target Account / الحساب الهدف", required=True,
        domain="[('company_id','=',target_company_id)]")
    recharge_account_source = fields.Many2one("account.account",
        string="IC Recharge Account (Source) / حساب إعادة التوزيع (مصدر)",
        required=True, domain="[('company_id','=',source_company_id)]")
    recharge_account_target = fields.Many2one("account.account",
        string="IC Recharge Account (Target) / حساب إعادة التوزيع (هدف)",
        required=True, domain="[('company_id','=',target_company_id)]")
    journal_source_id = fields.Many2one("account.journal", string="Journal (Source) / دفتر يومية المصدر",
        domain="[('company_id','=',source_company_id)]")
    journal_target_id = fields.Many2one("account.journal", string="Journal (Target) / دفتر يومية الهدف",
        domain="[('company_id','=',target_company_id)]")
    active = fields.Boolean(default=True)

    @api.constrains("source_company_id","target_company_id")
    def _check_different_companies(self):
        for rec in self:
            if rec.source_company_id == rec.target_company_id:
                raise ValidationError(_("Source and target company must be different. الشركة المصدر والهدف يجب أن تكونا مختلفتين."))


class ICRechargeWizard(models.TransientModel):
    """
    Wizard to create inter-company recharge journal entries.
    معالج لإنشاء قيود إعادة التوزيع بين الشركات.
    """
    _name = "ic.recharge.wizard"
    _description = "IC Recharge Wizard / معالج إعادة التوزيع"

    rule_id = fields.Many2one("ic.recharge.rule", string="Rule / القاعدة", required=True)
    amount = fields.Monetary(string="Amount / المبلغ", required=True, currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id)
    date = fields.Date(string="Date / التاريخ", required=True, default=fields.Date.today)
    reference = fields.Char(string="Reference / المرجع", required=True)
    narration = fields.Text(string="Description / الوصف", translate=True)

    def action_create_recharge(self):
        self.ensure_one()
        rule = self.rule_id

        # Create source journal entry
        source_move = self.env["account.move"].with_company(rule.source_company_id).create({
            "journal_id": rule.journal_source_id.id,
            "date": self.date,
            "ref": f"IC Recharge — {self.reference}",
            "narration": self.narration or "",
            "line_ids": [
                (0,0,{"account_id": rule.source_account_id.id,
                      "debit": self.amount, "credit": 0,
                      "name": f"IC Recharge to {rule.target_company_id.name} / إعادة توزيع إلى {rule.target_company_id.name}"}),
                (0,0,{"account_id": rule.recharge_account_source.id,
                      "debit": 0, "credit": self.amount,
                      "name": f"IC payable to {rule.target_company_id.name} / مستحق لـ {rule.target_company_id.name}"}),
            ],
        })
        source_move.action_post()

        # Create target journal entry
        target_move = self.env["account.move"].with_company(rule.target_company_id).create({
            "journal_id": rule.journal_target_id.id,
            "date": self.date,
            "ref": f"IC Recharge — {self.reference}",
            "narration": self.narration or "",
            "line_ids": [
                (0,0,{"account_id": rule.recharge_account_target.id,
                      "debit": self.amount, "credit": 0,
                      "name": f"IC receivable from {rule.source_company_id.name} / مستحق من {rule.source_company_id.name}"}),
                (0,0,{"account_id": rule.target_account_id.id,
                      "debit": 0, "credit": self.amount,
                      "name": f"IC Recharge from {rule.source_company_id.name} / إعادة توزيع من {rule.source_company_id.name}"}),
            ],
        })
        target_move.action_post()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("IC Recharge Created / تم إنشاء إعادة التوزيع"),
                "message": _("Source: %(src)s | Target: %(tgt)s", src=source_move.name, tgt=target_move.name),
                "type": "success",
                "sticky": False,
            },
        }
