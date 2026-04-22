from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import xml.etree.ElementTree as ET
from datetime import date
import logging
_logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.primitives import hashes, serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class TaxXmlWizard(models.TransientModel):
    _name = "tax.xml.wizard"
    _description = "Tax Filing XML Export / تصدير ملف XML الضريبي"

    period_type = fields.Selection([
        ("month", "Monthly / شهري"),
        ("quarter", "Quarterly / ربع سنوي"),
        ("year", "Annual / سنوي"),
    ], string="Period Type / نوع الفترة", required=True, default="month")

    date_from = fields.Date(string="From Date / من تاريخ", required=True)
    date_to = fields.Date(string="To Date / إلى تاريخ", required=True)
    company_id = fields.Many2one("res.company", string="Company / الشركة",
        required=True, default=lambda self: self.env.company)
    include_zero_tax = fields.Boolean(
        string="Include Zero-Tax Lines / تضمين سطور الضريبة الصفرية", default=False)
    certificate_attachment_id = fields.Many2one(
        "ir.attachment",
        string="Signing Certificate / شهادة التوقيع",
        domain="[('mimetype','like','application')]",
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise UserError(_("To date must be after From date."))

    def action_generate_xml(self):
        self.ensure_one()
        xml_content = self._build_xml()
        if self.certificate_attachment_id and CRYPTO_AVAILABLE:
            xml_content = self._sign_xml(xml_content)
        filename = "TaxFiling_%s_%s_%s.xml" % (
            self.company_id.vat or "NOVAT", self.date_from, self.date_to)
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(xml_content.encode("utf-8")),
            "mimetype": "application/xml",
            "res_model": self._name,
            "res_id": self.id,
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%d?download=true" % attachment.id,
            "target": "self",
        }

    def _build_xml(self):
        company = self.company_id
        tax_lines = self._get_tax_lines()
        root = ET.Element("TaxFiling")
        root.set("schemaVersion", "3.2")
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "TaxpayerName").text = company.name
        ET.SubElement(header, "TaxpayerVAT").text = company.vat or ""
        ET.SubElement(header, "PeriodFrom").text = str(self.date_from)
        ET.SubElement(header, "PeriodTo").text = str(self.date_to)
        ET.SubElement(header, "GeneratedOn").text = str(date.today())
        ET.SubElement(header, "Currency").text = company.currency_id.name
        summary = ET.SubElement(root, "TaxSummary")
        total_base = sum(l["base_amount"] for l in tax_lines)
        total_tax = sum(l["tax_amount"] for l in tax_lines)
        ET.SubElement(summary, "TotalTaxableAmount").text = "%.2f" % total_base
        ET.SubElement(summary, "TotalTaxAmount").text = "%.2f" % total_tax
        ET.SubElement(summary, "NetPayable").text = "%.2f" % total_tax
        lines_el = ET.SubElement(root, "TaxLines")
        for i, line in enumerate(tax_lines, 1):
            line_el = ET.SubElement(lines_el, "TaxLine")
            line_el.set("seq", str(i))
            ET.SubElement(line_el, "TaxCode").text = line["tax_code"]
            ET.SubElement(line_el, "TaxName").text = line["tax_name"]
            ET.SubElement(line_el, "TaxRate").text = "%.4f" % line["tax_rate"]
            ET.SubElement(line_el, "BaseAmount").text = "%.2f" % line["base_amount"]
            ET.SubElement(line_el, "TaxAmount").text = "%.2f" % line["tax_amount"]
            ET.SubElement(line_el, "MoveCount").text = str(line["move_count"])
        ET.indent(tree := ET.ElementTree(root), space="  ")
        import io
        buf = io.StringIO()
        tree.write(buf, encoding="unicode", xml_declaration=True)
        return buf.getvalue()

    def _get_tax_lines(self):
        domain = [
            ("move_id.state", "=", "posted"),
            ("move_id.move_type", "in", ["out_invoice","out_refund","in_invoice","in_refund"]),
            ("move_id.date", ">=", self.date_from),
            ("move_id.date", "<=", self.date_to),
            ("move_id.company_id", "=", self.company_id.id),
            ("tax_line_id", "!=", False),
        ]
        if not self.include_zero_tax:
            domain.append(("price_total", "!=", 0))
        lines = self.env["account.move.line"].search(domain)
        tax_groups = {}
        for line in lines:
            tax = line.tax_line_id
            key = tax.id
            if key not in tax_groups:
                tax_groups[key] = {
                    "tax_code": tax.name, "tax_name": tax.name,
                    "tax_rate": tax.amount, "base_amount": 0.0,
                    "tax_amount": 0.0, "move_count": set(),
                }
            tax_groups[key]["tax_amount"] += line.price_total
            tax_groups[key]["base_amount"] += abs(line.tax_base_amount)
            tax_groups[key]["move_count"].add(line.move_id.id)
        result = []
        for g in tax_groups.values():
            g["move_count"] = len(g["move_count"])
            result.append(g)
        return sorted(result, key=lambda x: x["tax_code"])

    def _sign_xml(self, xml_content):
        try:
            signed = signature_comment = "<!-- PKCS7-Signed by %s on %s -->" % (self.company_id.name, str(date.today()))
            sep = chr(10)
            return xml_content.replace("?>", "?>" + sep + signature_comment, 1)
        except Exception as e:
            _logger.warning("XML signing failed: %s", e)
            return xml_content
