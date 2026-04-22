
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PurchaseRequisitionPS(models.Model):
    _name = "port_said.requisition"
    _description = "طلب الاحتياج الحكومي"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "requisition_number desc"
    _rec_name = "requisition_number"

    requisition_number = fields.Char(string="رقم طلب الاحتياج", readonly=True, copy=False, index=True)
    fiscal_year   = fields.Integer(string="السنة المالية", default=lambda s: fields.Date.today().year)
    date_request  = fields.Date(string="تاريخ الطلب", default=fields.Date.today, required=True)
    department_id = fields.Many2one("res.partner", string="الإدارة الطالبة", required=True)
    requested_by  = fields.Many2one("res.users", string="أعده", default=lambda s: s.env.uid)
    approved_by   = fields.Many2one("res.users", string="اعتمده", readonly=True)
    description   = fields.Text(string="وصف الاحتياج", required=True)
    justification = fields.Text(string="مبرر الطلب")
    urgency = fields.Selection([
        ("normal","عادي"),("urgent","عاجل"),("very_urgent","عاجل جداً")
    ], default="normal", string="درجة الاستعجال")

    line_ids     = fields.One2many("port_said.requisition.line","requisition_id",string="البنود")
    total_amount = fields.Monetary(string="الإجمالي التقديري",compute="_compute_total",store=True,currency_field="currency_id")

    budget_line        = fields.Char(string="بند الميزانية", required=True)
    budget_position_id = fields.Char(string="رمز بند الموازنة")
    commitment_id      = fields.Many2one("port_said.commitment", string="الارتباط المنشأ", readonly=True)
    available_balance  = fields.Monetary(string="الرصيد المتاح", compute="_compute_balance", currency_field="currency_id")

    po_count = fields.Integer(default=0, string="عدد أوامر التوريد")

    currency_id = fields.Many2one("res.currency", default=lambda s: s.env.company.currency_id)
    notes       = fields.Text(string="ملاحظات")
    state = fields.Selection([
        ("draft","مسودة"),("submitted","مُقدَّم"),("approved","موافق عليه"),
        ("po_created","أمر توريد مُنشأ"),("cancelled","ملغي"),
    ], default="draft", tracking=True)
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company)

    @api.depends("line_ids.estimated_amount")
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped("estimated_amount"))

    @api.depends("budget_position_id")
    def _compute_balance(self):
        for rec in self:
            # Lookup via commitment model if available
            commitments = self.env["port_said.commitment"].search([
                ("budget_line_code", "=", rec.budget_position_id or rec.budget_line),
                ("state", "not in", ("cancelled",)),
                ("fiscal_year", "=", rec.fiscal_year),
            ])
            approved = sum(commitments.mapped("budget_approved"))
            consumed = sum(commitments.mapped("budget_consumed"))
            rec.available_balance = approved - consumed if approved else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("requisition_number"):
                vals["requisition_number"] = self.env["ir.sequence"].next_by_code("port_said.requisition") or "/"
        return super().create(vals_list)

    def action_submit(self):
        self.write({"state": "submitted"})

    def action_approve(self):
        """موافقة + إنشاء ارتباط تلقائي في C-FM-06."""
        for rec in self:
            if rec.total_amount > rec.available_balance > 0:
                raise ValidationError(_(
                    "المبلغ المطلوب %(r)s يتجاوز الرصيد المتاح %(b)s في البند %(l)s.",
                    r=rec.total_amount, b=rec.available_balance, l=rec.budget_line))
            commitment = self.env["port_said.commitment"].create({
                "fiscal_year":      rec.fiscal_year,
                "date_requested":   fields.Date.today(),
                "department_id":    rec.department_id.id,
                "description":      f"ارتباط تلقائي من طلب احتياج {rec.requisition_number}\n{rec.description}",
                "budget_line_code": rec.budget_line,
                "budget_line_code": rec.budget_position_id or rec.budget_line,
                "amount_requested": rec.total_amount,
            })
            commitment.action_submit()
            commitment.action_approve()
            rec.write({"state":"approved","approved_by":self.env.uid,"commitment_id":commitment.id})
            rec.message_post(body=_("✅ موافق — ارتباط %s أُنشئ تلقائياً") % commitment.commitment_number)

    def action_create_po(self):
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("يجب الموافقة على الطلب أولاً."))
        return {"type":"ir.actions.act_window","name":"إنشاء أمر توريد","res_model":"purchase.order",
                "view_mode":"form","context":{"default_requisition_ps_id":self.id,"default_origin":self.requisition_number}}

    def action_view_pos(self):
        return {"type":"ir.actions.act_window","name":"أوامر التوريد","res_model":"purchase.order",
                "view_mode":"tree,form","domain":[("origin","=",self.requisition_number)]}

    def action_print_requisition(self):
        return self.env.ref(
            'port_said_scm_requisition.action_report_requisition'
        ).report_action(self)


class PurchaseRequisitionLine(models.Model):
    _name = "port_said.requisition.line"
    _description = "بند طلب الاحتياج"

    requisition_id   = fields.Many2one("port_said.requisition", ondelete="cascade")
    product_id       = fields.Many2one("product.product", string="الصنف")
    description      = fields.Char(string="الوصف", required=True)
    qty              = fields.Float(string="الكمية", default=1.0)
    uom_id           = fields.Many2one("uom.uom", string="الوحدة")
    estimated_price  = fields.Monetary(string="السعر التقديري", currency_field="currency_id")
    estimated_amount = fields.Monetary(string="الإجمالي", compute="_compute_amount", store=True, currency_field="currency_id")
    currency_id      = fields.Many2one(related="requisition_id.currency_id", store=True)

    @api.depends("qty","estimated_price")
    def _compute_amount(self):
        for l in self:
            l.estimated_amount = l.qty * l.estimated_price

