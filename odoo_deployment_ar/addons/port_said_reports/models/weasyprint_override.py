# -*- coding: utf-8 -*-
import logging
import re
import base64
from odoo import models

_logger = logging.getLogger(__name__)

PORT_SAID_PREFIXES = ['port_said_reports']

_FONT_SEARCH_PATHS = [
    # Linux
    ('/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf',
     '/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf'),
    ('/usr/share/fonts/truetype/fonts-hosny-amiri/Amiri-Regular.ttf',
     '/usr/share/fonts/truetype/fonts-hosny-amiri/Amiri-Bold.ttf'),
    # Windows — Amiri if manually installed
    ('C:/Windows/Fonts/Amiri-Regular.ttf', 'C:/Windows/Fonts/Amiri-Bold.ttf'),
]

def _build_css():
    import os
    for regular_path, bold_path in _FONT_SEARCH_PATHS:
        if os.path.exists(regular_path) and os.path.exists(bold_path):
            try:
                with open(regular_path, 'rb') as f:
                    regular = base64.b64encode(f.read()).decode()
                with open(bold_path, 'rb') as f:
                    bold = base64.b64encode(f.read()).decode()
                return (
                    "@font-face{font-family:'Amiri';src:url('data:font/truetype;base64," + regular + "');font-weight:normal;}"
                    "@font-face{font-family:'Amiri';src:url('data:font/truetype;base64," + bold + "');font-weight:bold;}"
                    "html,body,div,table,tr,td,th,p,span,h1,h2,h3,h4,h5,li,a{"
                    "font-family:'Amiri',serif!important;direction:rtl!important;unicode-bidi:embed!important;}"
                    "@font-face{font-family:'Lato';src:url('data:font/truetype;base64," + regular + "');}"
                    "@font-face{font-family:'Arial';src:url('data:font/truetype;base64," + regular + "');}"
                    "@page{size:A4;margin:15mm;}"
                )
            except Exception as e:
                _logger.warning('Font load error (%s): %s', regular_path, e)
    # Fallback — use system Arabic fonts available on Windows/Linux
    _logger.warning('Amiri font not found — using system Arabic fonts for PDF')
    return (
        "body,*{font-family:'Arabic Typesetting','Traditional Arabic',"
        "'Simplified Arabic',Arial,serif!important;"
        "direction:rtl!important;unicode-bidi:embed!important;}"
        "@page{size:A4;margin:15mm;}"
    )

ARABIC_CSS = _build_css()

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        # WeasyPrint disabled — use Odoo's built-in wkhtmltopdf renderer.
        # QWeb templates already include Arabic RTL CSS via gov_page_style.
        return super()._render_qweb_pdf(report_ref, res_ids, data)

    def _render_with_weasyprint(self, report, res_ids, data):
        import weasyprint
        from weasyprint.text.fonts import FontConfiguration

        html_content, _ = self._render_qweb_html(report.report_name, res_ids, data=data)
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8', errors='ignore')

        html_content = re.sub(r'<link[^>]*>', '', html_content)
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = html_content.replace("font-family: 'Lato'", "font-family: 'Amiri'")
        html_content = html_content.replace('font-family: Lato', "font-family: 'Amiri'")

        if '<html' in html_content:
            html_content = re.sub(r'<html([^>]*)>', r'<html\1 lang="ar" dir="rtl">', html_content)
        else:
            html_content = '<html lang="ar" dir="rtl"><head><meta charset="utf-8"/></head><body dir="rtl">' + html_content + '</body></html>'

        if '<body' in html_content:
            html_content = re.sub(r'<body([^>]*)>', r'<body\1 dir="rtl">', html_content)

        font_config = FontConfiguration()
        arabic_css = weasyprint.CSS(string=ARABIC_CSS, font_config=font_config)

        pdf = weasyprint.HTML(string=html_content, base_url='file:///').write_pdf(
            stylesheets=[arabic_css], font_config=font_config
        )
        return pdf, 'pdf'
