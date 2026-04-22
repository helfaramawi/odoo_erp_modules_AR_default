# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date


class StockIssueBridge(models.Model):
    """
    إذن الصرف — زر إنشاء قيد محاسبي
    """
    _inherit = "stock.issue.permit"

    journal_entry_ids = fields.One2many(
        "stock.finance.journal.entry", "issue_permit_id",
        string="القيود المحاسبية",
    )
    journal_entry_count = fields.Integer(
        compute="_compute_entry_count", string="عدد القيود",
    )
    finance_status = fields.Selection([
        ("pending",  "لم يُقيَّد بعد"),
        ("posted",   "تم الترحيل المحاسبي"),
        ("manual",   "يدوي"),
    ], default="pending", string="الحالة المحاسبية", readonly=True)

    @api.depends("journal_entry_ids")
    def _compute_entry_count(self):
        for rec in self:
            rec.journal_entry_count = len(rec.journal_entry_ids)

    def action_view_journal_entries(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "القيود المحاسبية",
            "res_model": "stock.finance.journal.entry",
            "view_mode": "list,form",
            "domain": [("issue_permit_id", "=", self.id)],
        }


class StockAdditionBridge(models.Model):
    """
    إذن الإضافة — زر إنشاء قيد محاسبي
    """
    _inherit = "stock.addition.permit"

    journal_entry_ids = fields.One2many(
        "stock.finance.journal.entry", "addition_permit_id",
        string="القيود المحاسبية",
    )
    journal_entry_count = fields.Integer(
        compute="_compute_entry_count", string="عدد القيود",
    )
    finance_status = fields.Selection([
        ("pending", "لم يُقيَّد بعد"),
        ("posted",  "تم الترحيل المحاسبي"),
        ("manual",  "يدوي"),
    ], default="pending", string="الحالة المحاسبية", readonly=True)

    @api.depends("journal_entry_ids")
    def _compute_entry_count(self):
        for rec in self:
            rec.journal_entry_count = len(rec.journal_entry_ids)

    def action_create_journal_entry(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(_("يجب ترحيل إذن الإضافة أولاً"))
        if self.finance_status == "posted":
            raise UserError(_("تم إنشاء القيد المحاسبي مسبقاً"))
        return {
            "type": "ir.actions.act_window",
            "name": "إنشاء قيد محاسبي",
            "res_model": "stock.finance.journal.entry",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_addition_permit_id": self.id,
                "default_move_type": "addition",
                "default_date": self.permit_date,
                "default_warehouse_id": self.warehouse_id.id,
                "default_amount": self.qty * (self.product_id.standard_price if self.product_id else 0),
                "default_ref": f"إذن إضافة {self.name}",
            },
        }

    def action_view_journal_entries(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "القيود المحاسبية",
            "res_model": "stock.finance.journal.entry",
            "view_mode": "list,form",
            "domain": [("addition_permit_id", "=", self.id)],
        }


class StockTransferBridge(models.Model):
    _inherit = "stock.transfer.permit"

    journal_entry_ids = fields.One2many(
        "stock.finance.journal.entry", "transfer_permit_id",
        string="القيود المحاسبية",
    )
    journal_entry_count = fields.Integer(
        compute="_compute_entry_count",
    )
    finance_status = fields.Selection([
        ("pending", "لم يُقيَّد بعد"),
        ("posted",  "تم الترحيل المحاسبي"),
    ], default="pending", readonly=True)

    @api.depends("journal_entry_ids")
    def _compute_entry_count(self):
        for rec in self:
            rec.journal_entry_count = len(rec.journal_entry_ids)

    def action_create_journal_entry(self):
        self.ensure_one()
        if self.state not in ("posted", "received"):
            raise UserError(_("يجب ترحيل إذن التحويل أولاً"))
        return {
            "type": "ir.actions.act_window",
            "name": "إنشاء قيد محاسبي",
            "res_model": "stock.finance.journal.entry",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_transfer_permit_id": self.id,
                "default_move_type": "transfer",
                "default_date": self.transfer_date,
                "default_warehouse_id": self.from_warehouse_id.id,
                "default_amount": self.total_value,
                "default_ref": f"إذن تحويل {self.name}",
            },
        }


class StockReturnBridge(models.Model):
    _inherit = "stock.return.permit"

    journal_entry_ids = fields.One2many(
        "stock.finance.journal.entry", "return_permit_id",
        string="القيود المحاسبية",
    )
    journal_entry_count = fields.Integer(
        compute="_compute_entry_count",
    )
    finance_status = fields.Selection([
        ("pending", "لم يُقيَّد بعد"),
        ("posted",  "تم الترحيل المحاسبي"),
    ], default="pending", readonly=True)

    @api.depends("journal_entry_ids")
    def _compute_entry_count(self):
        for rec in self:
            rec.journal_entry_count = len(rec.journal_entry_ids)

    def action_create_journal_entry(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(_("يجب ترحيل إذن الارتجاع أولاً"))
        return {
            "type": "ir.actions.act_window",
            "name": "إنشاء قيد محاسبي",
            "res_model": "stock.finance.journal.entry",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_return_permit_id": self.id,
                "default_move_type": "return",
                "default_date": self.return_date,
                "default_warehouse_id": self.warehouse_id.id,
                "default_amount": self.total_value,
                "default_ref": f"إذن ارتجاع {self.name}",
            },
        }


class StockFinanceJournalEntry(models.Model):
    """
    القيد المحاسبي الناتج عن الحركة المخزنية
    يتضمن: الحسابات + الأبعاد المالية + الربط بالإذن الأصلي
    """
    _name = "stock.finance.journal.entry"
    _description = "قيد محاسبي للحركة المخزنية"
    _inherit = ["mail.thread"]
    _order = "date desc, id desc"

    name = fields.Char(string="رقم القيد", readonly=True, default="/")
    date = fields.Date(string="التاريخ", required=True, default=fields.Date.context_today)
    ref = fields.Char(string="المرجع")
    move_type = fields.Selection([
        ("addition",   "إذن إضافة"),
        ("issue",      "إذن صرف"),
        ("transfer",   "إذن تحويل"),
        ("return",     "إذن ارتجاع"),
        ("scrap",      "إتلاف"),
        ("adjustment", "تسوية"),
    ], string="نوع الحركة", required=True)

    # الربط بالأذونات
    issue_permit_id = fields.Many2one("stock.issue.permit", string="إذن الصرف")
    addition_permit_id = fields.Many2one("stock.addition.permit", string="إذن الإضافة")
    transfer_permit_id = fields.Many2one("stock.transfer.permit", string="إذن التحويل")
    return_permit_id = fields.Many2one("stock.return.permit", string="إذن الارتجاع")

    # بيانات القيد
    warehouse_id = fields.Many2one("stock.warehouse", string="المستودع")
    amount = fields.Monetary(
        string="المبلغ", required=True, currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency", default=lambda s: s.env.company.currency_id,
    )

    # الحسابات (تُملأ تلقائياً من القواعد أو يدوياً)
    debit_account_id = fields.Many2one(
        "account.account", string="حساب المدين", required=True,
    )
    credit_account_id = fields.Many2one(
        "account.account", string="حساب الدائن", required=True,
    )
    journal_id = fields.Many2one(
        "account.journal", string="دفتر اليومية", required=True,
    )

    # الأبعاد المالية
    dimension_id = fields.Many2one(
        "financial.dimension", string="البعد المالي",
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="الحساب التحليلي",
    )

    # القيد الفعلي في Odoo
    account_move_id = fields.Many2one(
        "account.move", string="القيد المحاسبي", readonly=True,
    )

    notes = fields.Text(string="ملاحظات")
    state = fields.Selection([
        ("draft",  "مسودة"),
        ("posted", "مرحَّل"),
        ("cancel", "ملغي"),
    ], default="draft", tracking=True)

    company_id = fields.Many2one(
        "res.company", default=lambda s: s.env.company,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "stock.finance.journal.entry") or "/"
            # auto-fill accounts from rules if not set
            if not vals.get("debit_account_id") and vals.get("move_type") and vals.get("warehouse_id"):
                rule = self.env["stock.finance.account.rule"].get_rule(
                    vals["move_type"], vals.get("warehouse_id"),
                )
                if rule:
                    vals.setdefault("debit_account_id", rule.debit_account_id.id)
                    vals.setdefault("credit_account_id", rule.credit_account_id.id)
                    vals.setdefault("journal_id", rule.journal_id.id)
            # auto-fill dimension
            if not vals.get("dimension_id") and vals.get("warehouse_id"):
                dim_rule = self.env["stock.finance.dimension.rule"].get_dimension(
                    warehouse_id=vals.get("warehouse_id"),
                )
                if dim_rule:
                    vals.setdefault("dimension_id", dim_rule.dimension_id.id)
                    if dim_rule.analytic_account_id:
                        vals.setdefault("analytic_account_id", dim_rule.analytic_account_id.id)
        return super().create(vals_list)

    def action_auto_fill(self):
        """تحديث الحسابات والأبعاد تلقائياً من القواعد"""
        for rec in self:
            rule = self.env["stock.finance.account.rule"].get_rule(
                rec.move_type,
                rec.warehouse_id.id if rec.warehouse_id else None,
            )
            if rule:
                rec.debit_account_id = rule.debit_account_id
                rec.credit_account_id = rule.credit_account_id
                rec.journal_id = rule.journal_id
            dim_rule = self.env["stock.finance.dimension.rule"].get_dimension(
                warehouse_id=rec.warehouse_id.id if rec.warehouse_id else None,
            )
            if dim_rule:
                rec.dimension_id = dim_rule.dimension_id
                if dim_rule.analytic_account_id:
                    rec.analytic_account_id = dim_rule.analytic_account_id
        return True

    def action_post(self):
        """ترحيل القيد — إنشاء account.move فعلي"""
        for rec in self:
            if rec.state == "posted":
                raise UserError(_("القيد مرحَّل مسبقاً"))
            if not rec.debit_account_id or not rec.credit_account_id:
                raise UserError(_("يجب تحديد حسابي المدين والدائن"))
            if rec.amount <= 0:
                raise UserError(_("المبلغ يجب أن يكون أكبر من صفر"))

            line_vals = [
                (0, 0, {
                    "account_id": rec.debit_account_id.id,
                    "name": rec.ref or rec.name,
                    "debit": rec.amount,
                    "credit": 0.0,
                    "analytic_distribution": (
                        {str(rec.analytic_account_id.id): 100}
                        if rec.analytic_account_id else {}
                    ),
                }),
                (0, 0, {
                    "account_id": rec.credit_account_id.id,
                    "name": rec.ref or rec.name,
                    "debit": 0.0,
                    "credit": rec.amount,
                    "analytic_distribution": (
                        {str(rec.analytic_account_id.id): 100}
                        if rec.analytic_account_id else {}
                    ),
                }),
            ]

            move = self.env["account.move"].create({
                "journal_id": rec.journal_id.id,
                "date": rec.date,
                "ref": rec.ref or rec.name,
                "line_ids": line_vals,
                "company_id": rec.company_id.id,
            })
            move.action_post()

            rec.write({
                "state": "posted",
                "account_move_id": move.id,
            })

            # تحديث حالة الإذن الأصلي
            permit = (rec.issue_permit_id or rec.addition_permit_id
                      or rec.transfer_permit_id or rec.return_permit_id)
            if permit:
                permit.finance_status = "posted"

            rec.message_post(body=_(
                f"تم إنشاء القيد المحاسبي: {move.name} — مدين: {rec.debit_account_id.name} | دائن: {rec.credit_account_id.name}"
            ))
        return True

    def action_cancel(self):
        for rec in self:
            if rec.account_move_id:
                rec.account_move_id.button_cancel()
            rec.write({"state": "cancel"})
        return True

    def action_view_account_move(self):
        self.ensure_one()
        if not self.account_move_id:
            return
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.account_move_id.id,
            "view_mode": "form",
            "target": "current",
        }
