from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMoveLine(models.Model):
    """
    Extend journal entry lines with financial dimension Many2many fields.
    توسيع سطور القيود بحقول الأبعاد المالية.
    """
    _inherit = "account.move.line"

    x_dimension_department_id = fields.Many2one(
        "financial.dimension",
        string="Department / القسم",
        domain="[('dimension_type','=','department')]",
        ondelete="restrict",
    )
    x_dimension_project_id = fields.Many2one(
        "financial.dimension",
        string="Project / المشروع",
        domain="[('dimension_type','=','project')]",
        ondelete="restrict",
    )
    x_dimension_region_id = fields.Many2one(
        "financial.dimension",
        string="Region / المنطقة",
        domain="[('dimension_type','=','region')]",
        ondelete="restrict",
    )

    @api.constrains("x_dimension_department_id","x_dimension_project_id","account_id")
    def _check_mandatory_dimensions(self):
        """
        Enforce mandatory dimensions based on account configuration.
        فرض الأبعاد الإلزامية بناءً على تكوين الحساب.
        """
        for line in self:
            if line.account_id.x_requires_department and not line.x_dimension_department_id:
                raise ValidationError(_(
                    "Account %s requires a Department dimension.\n"
                    "الحساب %s يتطلب بعد القسم.",
                    line.account_id.code, line.account_id.code,
                ))


class AccountAccount(models.Model):
    _inherit = "account.account"

    x_requires_department = fields.Boolean(
        string="Requires Department / يتطلب القسم",
        help="Validate that all journal lines on this account have a Department dimension",
    )
    x_requires_project = fields.Boolean(
        string="Requires Project / يتطلب المشروع",
    )
    x_requires_region = fields.Boolean(
        string="Requires Region / يتطلب المنطقة",
    )


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        """
        Override _post to propagate dimensions from invoice header to lines
        where dimensions are not already set.
        تجاوز _post لنشر الأبعاد من رأس الفاتورة إلى السطور.
        """
        for move in self:
            header_dept = move.line_ids.filtered(
                lambda l: l.x_dimension_department_id
            ).mapped("x_dimension_department_id")[:1]
            header_proj = move.line_ids.filtered(
                lambda l: l.x_dimension_project_id
            ).mapped("x_dimension_project_id")[:1]
            header_region = move.line_ids.filtered(
                lambda l: l.x_dimension_region_id
            ).mapped("x_dimension_region_id")[:1]

            for line in move.line_ids:
                vals = {}
                if header_dept and not line.x_dimension_department_id:
                    vals["x_dimension_department_id"] = header_dept.id
                if header_proj and not line.x_dimension_project_id:
                    vals["x_dimension_project_id"] = header_proj.id
                if header_region and not line.x_dimension_region_id:
                    vals["x_dimension_region_id"] = header_region.id
                if vals:
                    line.write(vals)
        return super()._post(soft=soft)
