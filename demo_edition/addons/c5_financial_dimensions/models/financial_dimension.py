from odoo import models, fields, api, _

class FinancialDimension(models.Model):
    """
    Master dimension values (Department, Project, Region).
    قيم الأبعاد الرئيسية (القسم، المشروع، المنطقة).
    """
    _name = "financial.dimension"
    _description = "Financial Dimension / البعد المالي"
    _order = "dimension_type, code"

    name = fields.Char(string="Name / الاسم", required=True, translate=True)
    code = fields.Char(string="Code / الرمز", required=True)
    dimension_type = fields.Selection([
        ("department","Department / القسم"),
        ("project","Project / المشروع"),
        ("region","Region / المنطقة"),
    ], string="Type / النوع", required=True, index=True)
    active = fields.Boolean(default=True, string="Active / نشط")
    company_id = fields.Many2one("res.company", string="Company / الشركة",
        default=lambda self: self.env.company)

    _sql_constraints = [
        ("code_type_uniq","UNIQUE(code, dimension_type, company_id)",
         "Dimension code must be unique per type and company / رمز البعد يجب أن يكون فريداً"),
    ]

    def name_get(self):
        return [(r.id, f"[{r.code}] {r.name}") for r in self]
