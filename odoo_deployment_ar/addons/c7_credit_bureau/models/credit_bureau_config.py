from odoo import models, fields, api, _

class CreditBureauConfig(models.Model):
    _name = "credit.bureau.config"
    _description = "Credit Bureau API Config / تكوين واجهة مكتب الائتمان"

    name = fields.Char(string="Name / الاسم", required=True, default="Default")
    api_url = fields.Char(string="API URL", required=True)
    api_key = fields.Char(string="API Key", required=True)
    timeout = fields.Integer(string="Timeout (s) / المهلة", default=5)
    green_threshold = fields.Integer(string="Green Score Min / حد الدرجة الخضراء", default=700)
    amber_threshold = fields.Integer(string="Amber Score Min / حد الدرجة العنبرية", default=500)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
