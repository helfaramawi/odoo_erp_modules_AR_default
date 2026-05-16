# -*- coding: utf-8 -*-
import logging
import re
import base64

_logger = logging.getLogger(__name__)

FORM50_PREFIXES = ['port_said_form50_print']


def _build_form50_css():
    import os
    from odoo.modules import get_module_resource
    try:
        r_path = get_module_resource('port_said_form50_print', 'static', 'src', 'fonts', 'Amiri-Regular.ttf')
        b_path = get_module_resource('port_said_form50_print', 'static', 'src', 'fonts', 'Amiri-Bold.ttf')
        with open(r_path, 'rb') as f:
            r = base64.b64encode(f.read()).decode()
        with open(b_path, 'rb') as f:
            b = base64.b64encode(f.read()).decode()
        return (
            "@font-face{font-family:'Amiri';"
            "src:url('data:font/truetype;base64," + r + "');font-weight:normal;font-style:normal;}"
            "@font-face{font-family:'Amiri';"
            "src:url('data:font/truetype;base64," + b + "');font-weight:bold;font-style:normal;}"
            "@font-face{font-family:'Lato';"
            "src:url('data:font/truetype;base64," + r + "');}"
            "html,body,div,table,tr,td,th,p,span,h1,h2,h3,h4,h5,li,a{"
            "font-family:'Amiri',serif!important;"
            "direction:rtl!important;"
            "unicode-bidi:embed!important;}"
            "@page{size:A4;margin:8mm 10mm;}"
        )
    except Exception as e:
        _logger.error("Form50 font load error: %s", e)
        return "body{font-family:serif;direction:rtl;}"


FORM50_CSS = _build_form50_css()


from odoo import models


class IrActionsReportForm50(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        report_name = report.report_name or ''
        is_form50 = any(report_name.startswith(p) for p in FORM50_PREFIXES)
        if is_form50:
            try:
                result = self._render_form50_weasyprint(report, res_ids, data)
                if result:
                    return result
            except Exception as e:
                _logger.error("Form50 WeasyPrint error for %s: %s", report_name, e)
        return super()._render_qweb_pdf(report_ref, res_ids, data)

    def _render_form50_weasyprint(self, report, res_ids, data):
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
            html_content = (
                '<html lang="ar" dir="rtl"><head><meta charset="utf-8"/></head>'
                '<body dir="rtl">' + html_content + '</body></html>'
            )
        if '<body' in html_content:
            html_content = re.sub(r'<body([^>]*)>', r'<body\1 dir="rtl">', html_content)

        font_config = FontConfiguration()
        css = weasyprint.CSS(string=FORM50_CSS, font_config=font_config)
        pdf = weasyprint.HTML(string=html_content, base_url='file:///').write_pdf(
            stylesheets=[css],
            font_config=font_config,
        )
        _logger.info("Form50 WeasyPrint OK: %s (%d bytes)", report.report_name, len(pdf))
        return pdf, 'pdf'
