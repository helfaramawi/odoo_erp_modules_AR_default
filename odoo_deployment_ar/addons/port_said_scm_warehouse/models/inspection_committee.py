
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InspectionCommittee(models.Model):
    """
    محضر لجنة الفحص — نموذج 12 مخازن
    مطلوب كمرفق في استمارة 50 (إجراءات الاستمارة ص.2)
    """
    _name = "port_said.inspection.committee"
    _description = "محضر لجنة الفحص (نموذج 12 مخازن)"
    _inherit = ["mail.thread"]
    _rec_name = "committee_number"

    committee_number = fields.Char(string="رقم المحضر", readonly=True, copy=False, index=True)
    date_inspection  = fields.Date(string="تاريخ الفحص", default=fields.Date.today, required=True)
    purchase_order_id = fields.Many2one("purchase.order", string="أمر التوريد")
    dossier_id        = fields.Many2one("port_said.dossier", string="الاضبارة")

    # اللجنة
    chairman_id      = fields.Many2one("res.users", string="رئيس اللجنة")
    member1_id       = fields.Many2one("res.users", string="العضو الأول")
    member2_id       = fields.Many2one("res.users", string="العضو الثاني")
    storekeeper_id   = fields.Many2one("res.users", string="أمين المخازن")

    # بيانات الفحص
    items_received   = fields.Text(string="الأصناف المُستلمة", required=True)
    quantity_ordered = fields.Float(string="الكمية المطلوبة")
    quantity_received = fields.Float(string="الكمية المُستلمة الفعلية")
    quantity_accepted = fields.Float(string="الكمية المقبولة")
    quantity_rejected = fields.Float(string="الكمية المرفوضة", compute="_compute_rejected", store=True)
    rejection_reason  = fields.Text(string="أسباب الرفض")
    specs_conformity  = fields.Selection([
        ("conforming",   "مطابق للمواصفات"),
        ("partial",      "مطابق جزئياً"),
        ("nonconforming","غير مطابق"),
    ], string="مطابقة المواصفات", required=True, default="conforming")

    # إقرار أمين المخازن
    storekeeper_declaration = fields.Text(string="إقرار أمين المخازن")
    storekeeper_signed      = fields.Boolean(string="وقّع أمين المخازن")

    # نموذج 1 — إذن الإضافة
    addition_permit_no   = fields.Char(string="رقم إذن الإضافة (نموذج 1)")
    addition_permit_date = fields.Date(string="تاريخ إذن الإضافة")
    stock_location_id    = fields.Many2one("stock.location", string="موقع التخزين")

    result = fields.Selection([
        ("approved",  "موافق على الاستلام"),
        ("partial",   "موافق جزئياً"),
        ("rejected",  "مرفوض — يُعاد للمورد"),
    ], string="قرار اللجنة", required=True, default="approved")

    state = fields.Selection([
        ("draft",    "مسودة"),
        ("signed",   "موقّع من اللجنة"),
        ("finalized","مُعتمد ومُدرج في الاضبارة"),
    ], default="draft", tracking=True)
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company)

    @api.depends("quantity_received","quantity_accepted")
    def _compute_rejected(self):
        for rec in self:
            rec.quantity_rejected = max(rec.quantity_received - rec.quantity_accepted, 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("committee_number"):
                vals["committee_number"] = self.env["ir.sequence"].next_by_code("port_said.inspection") or "/"
        return super().create(vals_list)

    def action_sign(self):
        if not self.storekeeper_signed:
            raise UserError(_("يجب توقيع أمين المخازن قبل اعتماد المحضر."))
        self.write({"state": "signed"})

    def action_finalize_and_attach_to_dossier(self):
        """إرفاق المحضر بالاضبارة تلقائياً."""
        self.ensure_one()
        if self.state != "signed":
            raise UserError(_("يجب توقيع المحضر أولاً."))
        # إنشاء مرفق PDF في الاضبارة
        if self.dossier_id:
            # إضافة تسجيل في قائمة مرفقات الاضبارة
            attachment = self.env["ir.attachment"].create({
                "name": f"محضر لجنة الفحص {self.committee_number}",
                "res_model": "port_said.inspection.committee",
                "res_id": self.id,
            })
            self.env["port_said.dossier.attachment"].create({
                "dossier_id":      self.dossier_id.id,
                "attachment_type": "committee_report",
                "attachment_id":   attachment.id,
                "notes":           f"محضر {self.committee_number} — {self.date_inspection}",
            })
        self.write({"state": "finalized"})
        self.message_post(body=_("✅ المحضر مُعتمد ومُدرج في الاضبارة"))

    def action_print_inspection(self):
        return self.env.ref('port_said_scm_warehouse.action_report_inspection').report_action(self)

    def action_print_committee(self):
        return self.env.ref(
            'port_said_scm_warehouse.action_report_inspection'
        ).report_action(self)
