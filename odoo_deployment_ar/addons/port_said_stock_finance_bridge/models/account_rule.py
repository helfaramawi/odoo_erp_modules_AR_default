# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockFinanceAccountRule(models.Model):
    """
    قاعدة الحسابات المحاسبية لكل نوع حركة مخزنية
    نوع الحركة → حساب مدين + حساب دائن + دفتر يومية
    """
    _name = "stock.finance.account.rule"
    _description = "قاعدة الحسابات المحاسبية للحركات المخزنية"
    _order = "move_type, sequence"

    name = fields.Char(string="اسم القاعدة", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    move_type = fields.Selection([
        ("addition",   "إذن إضافة — استلام"),
        ("issue",      "إذن صرف (111 ع.ح)"),
        ("transfer",   "إذن تحويل بين مخازن"),
        ("return",     "إذن ارتجاع (نموذج 8)"),
        ("scrap",      "إتلاف / شطب"),
        ("adjustment", "تسوية جرد"),
    ], string="نوع الحركة", required=True)

    warehouse_id = fields.Many2one(
        "stock.warehouse", string="المستودع (فارغ = الكل)",
    )
    product_categ_id = fields.Many2one(
        "product.category", string="فئة الصنف (فارغ = الكل)",
    )

    debit_account_id = fields.Many2one(
        "account.account", string="حساب المدين", required=True,
    )
    credit_account_id = fields.Many2one(
        "account.account", string="حساب الدائن", required=True,
    )
    journal_id = fields.Many2one(
        "account.journal", string="دفتر اليومية", required=True,
        domain="[(\'type\',\'in\',[\'general\',\'stock\'])]",
    )
    move_ref_template = fields.Char(
        string="نموذج المرجع", default="{move_type} / {move_name}",
    )
    notes = fields.Text(string="ملاحظات")

    def get_rule(self, move_type, warehouse_id=None, product_categ_id=None):
        domain = [("move_type", "=", move_type), ("active", "=", True)]
        for wh, cat in [
            (warehouse_id, product_categ_id),
            (warehouse_id, False),
            (False, product_categ_id),
            (False, False),
        ]:
            rule = self.search(domain + [
                ("warehouse_id", "=", wh),
                ("product_categ_id", "=", cat),
            ], limit=1)
            if rule:
                return rule
        return self.browse()
