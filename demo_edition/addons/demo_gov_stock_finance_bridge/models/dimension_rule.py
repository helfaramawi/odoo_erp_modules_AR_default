# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockFinanceDimensionRule(models.Model):
    """
    قاعدة الأبعاد المالية لكل مستودع / فئة صنف / إدارة
    """
    _name = "stock.finance.dimension.rule"
    _description = "قاعدة الأبعاد المالية للمخازن"
    _order = "sequence"

    name = fields.Char(string="اسم القاعدة", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    # مصادر تحديد البعد
    warehouse_id = fields.Many2one(
        "stock.warehouse", string="المستودع",
    )
    product_categ_id = fields.Many2one(
        "product.category", string="فئة الصنف",
    )
    department_name = fields.Char(
        string="الإدارة الطالبة",
        help="اسم الإدارة كما يظهر في إذن الصرف",
    )

    # الأبعاد المالية الناتجة
    dimension_id = fields.Many2one(
        "financial.dimension", string="البعد المالي",
        required=True,
        domain="[(\'dimension_type\',\'=\',\'department\')]",
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="الحساب التحليلي",
    )
    notes = fields.Text(string="ملاحظات")

    def get_dimension(self, warehouse_id=None, product_categ_id=None, department_name=None):
        """استخراج البعد المالي بالأولوية"""
        domain = [("active", "=", True)]
        for wh, cat, dept in [
            (warehouse_id, product_categ_id, department_name),
            (warehouse_id, product_categ_id, False),
            (warehouse_id, False, False),
            (False, product_categ_id, False),
            (False, False, False),
        ]:
            d = [("warehouse_id", "=", wh),
                 ("product_categ_id", "=", cat)]
            if dept:
                d.append(("department_name", "=", dept))
            else:
                d.append(("department_name", "=", False))
            rule = self.search(domain + d, limit=1)
            if rule:
                return rule
        return self.browse()
