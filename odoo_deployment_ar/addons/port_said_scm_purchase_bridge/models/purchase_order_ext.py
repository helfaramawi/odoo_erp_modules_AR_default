
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrderPS(models.Model):
    """
    C-SCM-02: تمديد purchase.order
    - ربط بطلب الاحتياج (C-SCM-01)
    - ربط بالارتباط (C-FM-06)
    - توليد مسودة استمارة 50 تلقائياً عند التأكيد (FDD ص.13)
    - خطابات الضمان (FDD ص.38-40)
    """
    _inherit = "purchase.order"

    requisition_ps_id = fields.Many2one("port_said.requisition", string="طلب الاحتياج", readonly=True, index=True)
    commitment_id     = fields.Many2one("port_said.commitment", string="الارتباط / التجنيب",
                                        domain="[('state','in',['approved','reserved'])]")
    # daftar55 records linked via form50 origin field
    form50_count      = fields.Integer(compute="_compute_form50_count")

    # خطاب الضمان — FDD ص.38-40
    guarantee_letter_required = fields.Boolean(string="يستلزم خطاب ضمان")
    guarantee_letter_ref      = fields.Char(string="مرجع خطاب الضمان")
    guarantee_amount          = fields.Monetary(string="مبلغ خطاب الضمان")
    guarantee_expiry          = fields.Date(string="تاريخ انتهاء الضمان")
    guarantee_state           = fields.Selection([
        ("not_required","غير مطلوب"),("pending","قيد الإصدار"),
        ("issued","صادر"),("expired","منتهي"),("released","مُفرج عنه"),
    ], default="not_required", string="حالة الضمان")

    budget_line = fields.Char(string="بند الميزانية", related="commitment_id.budget_line_code", store=True)

    def _compute_form50_count(self):
        for rec in self:
            rec.form50_count = self.env["port_said.daftar55"].search_count(
                [("form50_ref", "like", rec.name or "")])

    def button_confirm(self):
        for rec in self:
            if rec.commitment_id and rec.commitment_id.state not in ("approved","reserved","cleared"):
                raise ValidationError(_(
                    "لا يمكن تأكيد أمر التوريد قبل اعتماد الارتباط.\n"
                    "حالة الارتباط: %s") % rec.commitment_id.state)
            if rec.commitment_id and rec.commitment_id.state == "approved":
                rec.commitment_id.action_reserve()

        result = super().button_confirm()

        for rec in self:
            if not self.env["port_said.daftar55"].search([("form50_ref", "like", rec.name or "")], limit=1):
                rec._create_form50_draft()
        return result

    def _create_form50_draft(self):
        """
        ينشئ مسودة استمارة 50 (دفتر 55) من أمر التوريد.
        هذه نقطة التكامل الحرجة: SCM → مالية.
        FDD ص.13: استمارة اعتماد الصرف جزء (أ)
        """
        self.ensure_one()
        partner = self.partner_id
        bank    = partner.bank_ids[:1] if partner.bank_ids else False
        form50  = self.env["port_said.daftar55"].create({
            "department_name":   self.company_id.name,
            "division_name":     self.requisition_ps_id.department_id.name if self.requisition_ps_id else "",
            "form50_ref":        f"مرجع: {self.name}",
            "vendor_id":         partner.id,
            "national_id":       partner.vat or "",
            "bank_name":         (bank.bank_id.name if bank and bank.bank_id else ""),
            "iban":              (bank.acc_number or "" if bank else ""),
            "budget_line":       self.commitment_id.budget_line_code if self.commitment_id else "",
            "amount_gross":      self.amount_total,
                        "commitment_ref":    self.commitment_id.commitment_number if self.commitment_id else "",
            "commitment_id":     self.commitment_id.id if self.commitment_id else False,
            "purchase_order_id": self.id,
            "state":             "draft",
            "notes":             f"مُنشأ تلقائياً من أمر التوريد {self.name}",
        })
        self.message_post(body=_("📄 استمارة 50 رقم %s أُنشئت تلقائياً") % form50.sequence_number)
        return form50

    def action_view_form50(self):
        return {"type":"ir.actions.act_window","name":"استمارات 50","res_model":"port_said.daftar55",
                "view_mode":"list,form","domain":[("purchase_order_id","=",self.id)]}


class Daftar55PSExtension(models.Model):
    """Add purchase_order_id to daftar55 only when purchase bridge is installed."""
    _inherit = 'port_said.daftar55'

    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='أمر التوريد المصدر',
        readonly=True,
        ondelete='set null',
    )
