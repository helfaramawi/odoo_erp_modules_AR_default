# -*- coding: utf-8 -*-
import logging
import os
import re
import shutil
import subprocess
import tempfile

_logger = logging.getLogger(__name__)
_logger.info("=== port_said_form50_print.weasyprint_override imported ===")

FORM50_PREFIXES = ['port_said_form50_print']

from .amiri_font_css import AMIRI_CSS as FORM50_CSS
from odoo import models


class IrActionsReportForm50(models.Model):
    _inherit = 'ir.actions.report'

    # ------------------------------------------------------------------ #
    #  Override both _render_qweb_pdf (Odoo ≤17) and _render (Odoo 18+)  #
    # ------------------------------------------------------------------ #

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        _logger.info("Form50 _render_qweb_pdf called for %s", report_ref)
        return self._form50_dispatch(report_ref, res_ids, data,
                                     super_fn=lambda: super(IrActionsReportForm50, self)
                                     ._render_qweb_pdf(report_ref, res_ids, data))

    def _render(self, report_ref, res_ids=None, data=None):
        _logger.info("Form50 _render called for %s", report_ref)
        return self._form50_dispatch(report_ref, res_ids, data,
                                     super_fn=lambda: super(IrActionsReportForm50, self)
                                     ._render(report_ref, res_ids, data))

    # ------------------------------------------------------------------ #

    def _form50_dispatch(self, report_ref, res_ids, data, super_fn):
        try:
            report = self._get_report(report_ref)
            report_name = report.report_name or ''
        except Exception:
            return super_fn()

        if not any(report_name.startswith(p) for p in FORM50_PREFIXES):
            return super_fn()

        _logger.info("Form50: dispatching %s", report_name)

        # 1) WeasyPrint (Linux / if installed)
        try:
            result = self._render_form50_weasyprint(report, res_ids, data)
            if result:
                return result
        except Exception as e:
            _logger.warning("Form50 WeasyPrint unavailable: %s", e)

        # 2) Entity-encoded wkhtmltopdf (works regardless of OS locale)
        try:
            result = self._render_form50_entity_pdf(report, res_ids, data)
            if result:
                return result
        except Exception as e:
            _logger.warning("Form50 entity-PDF failed: %s", e)

        # 3) Last resort: Odoo default (still garbled but at least doesn't crash)
        _logger.warning("Form50: falling back to Odoo default renderer")
        return super_fn()

    # ------------------------------------------------------------------ #

    def _render_form50_entity_pdf(self, report, res_ids, data):
        """
        Convert all non-ASCII characters to HTML entities so the HTML file is
        pure ASCII and wkhtmltopdf reads it correctly regardless of the OS
        default encoding.  Amiri font is already embedded as base64 in the CSS.
        """
        from odoo.tools import config as odoo_config

        wk_bin = (
            odoo_config.get('wkhtmltopdf_path')
            or shutil.which('wkhtmltopdf')
            or r'E:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
            or r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        )
        _logger.info("Form50 entity-PDF: wkhtmltopdf=%s", wk_bin)

        if not wk_bin or not os.path.exists(str(wk_bin)):
            _logger.warning("Form50: wkhtmltopdf binary not found at %s", wk_bin)
            return None

        html_content, _ = self._render_qweb_html(report.report_name, res_ids, data=data)
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8', errors='replace')

        # Convert every non-ASCII character to &#NNN; entity — pure ASCII output
        safe_html = ''.join(
            '&#{};'.format(ord(c)) if ord(c) > 127 else c
            for c in html_content
        )

        html_fd, html_path = tempfile.mkstemp(suffix='.html')
        pdf_path = html_path[:-5] + '.pdf'
        try:
            with os.fdopen(html_fd, 'w', encoding='ascii') as fh:
                fh.write(safe_html)

            cmd = [
                wk_bin,
                '--quiet',
                '--disable-smart-shrinking',
                '--page-width',  '210mm',
                '--page-height', '297mm',
                '--margin-top',    '0',
                '--margin-bottom', '0',
                '--margin-left',   '0',
                '--margin-right',  '0',
                '--disable-external-links',
                '--no-background',
                html_path, pdf_path,
            ]
            _logger.info("Form50 entity-PDF cmd: %s", ' '.join(cmd))
            proc = subprocess.run(cmd, capture_output=True, timeout=120)
            if proc.returncode != 0:
                _logger.warning("Form50 wkhtmltopdf stderr: %s",
                                proc.stderr.decode('utf-8', 'ignore'))

            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                with open(pdf_path, 'rb') as fh:
                    pdf_bytes = fh.read()
                _logger.info("Form50 entity-PDF OK: %d bytes", len(pdf_bytes))
                return pdf_bytes, 'pdf'
        finally:
            for p in (html_path, pdf_path):
                try:
                    os.unlink(p)
                except Exception:
                    pass
        return None

    # ------------------------------------------------------------------ #

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
