# -*- coding: utf-8 -*-
import logging
import re
import subprocess

_logger = logging.getLogger(__name__)

FORM50_PREFIXES = ['port_said_form50_print']

from .amiri_font_css import AMIRI_CSS as FORM50_CSS
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
                _logger.warning("Form50 WeasyPrint not available: %s", e)
            # Patch subprocess.Popen so Odoo's own wkhtmltopdf call gets --encoding utf-8
            return self._render_form50_patched_wkhtmltopdf(report_ref, res_ids, data)
        return super()._render_qweb_pdf(report_ref, res_ids, data)

    def _render_form50_patched_wkhtmltopdf(self, report_ref, res_ids, data):
        """
        Run Odoo's standard wkhtmltopdf pipeline with --encoding utf-8 injected.
        This fixes Arabic mojibake on Windows where wkhtmltopdf reads HTML as
        Windows-1252 instead of UTF-8.
        """
        _orig_popen = subprocess.Popen

        class _UTF8Popen(_orig_popen):
            def __init__(self_inner, cmd, *a, **kw):
                if (isinstance(cmd, (list, tuple)) and cmd
                        and 'wkhtmltopdf' in str(cmd[0]).lower()
                        and '--encoding' not in cmd):
                    cmd = list(cmd)
                    cmd.insert(1, 'utf-8')
                    cmd.insert(1, '--encoding')
                    _logger.info("Form50: injected --encoding utf-8 → %s", cmd[0])
                _orig_popen.__init__(self_inner, cmd, *a, **kw)

        subprocess.Popen = _UTF8Popen
        try:
            _logger.info("Form50: rendering %s via patched wkhtmltopdf", report_ref)
            return super(IrActionsReportForm50, self)._render_qweb_pdf(
                report_ref, res_ids, data
            )
        finally:
            subprocess.Popen = _orig_popen

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
