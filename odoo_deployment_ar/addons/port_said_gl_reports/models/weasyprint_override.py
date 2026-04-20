# -*- coding: utf-8 -*-
import logging
import re
import base64
_logger = logging.getLogger(__name__)

PORT_SAID_PREFIXES = [
    'port_said_gl_reports', 'port_said_acct_reports',
    'port_said_daftar55', 'port_said_daftar224',
    'port_said_form69', 'port_said_form75',
    'port_said_commitment', 'port_said_dossier',
    'port_said_scm_requisition', 'port_said_scm_warehouse',
    'port_said_fixed_assets', 'l10n_eg_auction',
    'c3_aging_report', 'port_said_budget_planning',
    'port_said_reports',
]

def _build_css():
    try:
        with open('/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf','rb') as f:
            r = base64.b64encode(f.read()).decode()
        with open('/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf','rb') as f:
            b = base64.b64encode(f.read()).decode()
        return (
            "@font-face{font-family:'Amiri';"
            "src:url('data:font/truetype;base64," + r + "');font-weight:normal;}"
            "@font-face{font-family:'Amiri';"
            "src:url('data:font/truetype;base64," + b + "');font-weight:bold;}"
            # Force Amiri everywhere with highest specificity
            "html,body,div,table,tr,td,th,p,span,h1,h2,h3,h4,h5,li,a{"
            "font-family:'Amiri',serif!important;"
            "direction:rtl!important;"
            "unicode-bidi:embed!important;}"
            # Override any Lato/Arial from Odoo
            "@font-face{font-family:'Lato';src:url('data:font/truetype;base64," + r + "');}"
            "@font-face{font-family:'Arial';src:url('data:font/truetype;base64," + r + "');}"
            "@page{size:A4;margin:15mm;}"
        )
    except Exception as e:
        _logger.error("Font load error: %s", e)
        return "body{font-family:serif;direction:rtl;}"

ARABIC_CSS = _build_css()

from odoo import models

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        report_name = report.report_name or ''
        is_port_said = any(report_name.startswith(p) for p in PORT_SAID_PREFIXES)
        is_form50 = 'form50' in report_name
        if is_port_said and not is_form50:
            try:
                result = self._render_with_weasyprint(report, res_ids, data)
                if result:
                    return result
            except Exception as e:
                _logger.error("WeasyPrint error for %s: %s", report_name, e)
        return super()._render_qweb_pdf(report_ref, res_ids, data)

    def _render_with_weasyprint(self, report, res_ids, data):
        import weasyprint
        from weasyprint.text.fonts import FontConfiguration

        html_content, _ = self._render_qweb_html(
            report.report_name, res_ids, data=data
        )
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8', errors='ignore')

        # Strip ALL external CSS/JS that WeasyPrint can't load
        html_content = re.sub(r'<link[^>]*>', '', html_content)
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        # Remove inline style that sets Lato font
        html_content = html_content.replace("font-family: 'Lato'", "font-family: 'Amiri'")
        html_content = html_content.replace('font-family: Lato', "font-family: 'Amiri'")

        # Force Arabic document metadata for proper shaping/bidi
        if '<html' in html_content:
            html_content = re.sub(r'<html([^>]*)>', r'<html\1 lang="ar" dir="rtl">', html_content)
        else:
            html_content = '<html lang="ar" dir="rtl"><head><meta charset="utf-8"/></head><body dir="rtl">' + html_content + '</body></html>'

        if '<body' in html_content:
            html_content = re.sub(r'<body([^>]*)>', r'<body\1 dir="rtl">', html_content)

        font_config = FontConfiguration()
        arabic_css = weasyprint.CSS(string=ARABIC_CSS, font_config=font_config)

        pdf = weasyprint.HTML(
            string=html_content,
            base_url='file:///',
        ).write_pdf(
            stylesheets=[arabic_css],
            font_config=font_config,
        )
        _logger.info("WeasyPrint OK: %s (%d bytes)", report.report_name, len(pdf))
        return pdf, 'pdf'
