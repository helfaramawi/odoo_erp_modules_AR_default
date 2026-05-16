# -*- coding: utf-8 -*-
import logging
import os
import re
import subprocess
import tempfile

_logger = logging.getLogger(__name__)

FORM50_PREFIXES = ['port_said_form50_print']

from .amiri_font_css import AMIRI_CSS as FORM50_CSS
from odoo import models, api, tools


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
            try:
                result = self._render_form50_wkhtmltopdf_utf8(report, res_ids, data)
                if result:
                    return result
            except Exception as e:
                _logger.warning("Form50 direct wkhtmltopdf failed: %s", e)
        return super()._render_qweb_pdf(report_ref, res_ids, data)

    def _render_form50_wkhtmltopdf_utf8(self, report, res_ids, data):
        """Call wkhtmltopdf directly with --encoding utf-8 to fix Arabic mojibake on Windows."""
        from odoo.tools import config as odoo_config

        # Resolve binary — config key in odoo.conf is 'wkhtmltopdf_path'
        wkhtmltopdf_bin = (
            odoo_config.get('wkhtmltopdf_path')
            or tools.find_in_path('wkhtmltopdf')
            or r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        )

        html_content, _ = self._render_qweb_html(report.report_name, res_ids, data=data)
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8', errors='ignore')

        html_fd, html_path = tempfile.mkstemp(suffix='.html')
        pdf_path = html_path[:-5] + '.pdf'
        try:
            with os.fdopen(html_fd, 'w', encoding='utf-8') as fh:
                fh.write(html_content)

            cmd = [
                wkhtmltopdf_bin,
                '--encoding', 'utf-8',
                '--quiet',
                '--disable-smart-shrinking',
                html_path,
                pdf_path,
            ]
            _logger.info("Form50 wkhtmltopdf: %s", cmd)
            proc = subprocess.run(cmd, capture_output=True, timeout=120)
            if proc.returncode != 0:
                _logger.warning(
                    "Form50 wkhtmltopdf stderr: %s",
                    proc.stderr.decode('utf-8', errors='ignore'),
                )

            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                with open(pdf_path, 'rb') as fh:
                    pdf_bytes = fh.read()
                _logger.info("Form50 wkhtmltopdf OK: %d bytes", len(pdf_bytes))
                return pdf_bytes, 'pdf'
        finally:
            try:
                os.unlink(html_path)
            except Exception:
                pass
            try:
                os.unlink(pdf_path)
            except Exception:
                pass
        return None

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
