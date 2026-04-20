# -*- coding: utf-8 -*-
"""
WeasyPrint renderer for Form 50 - proper Arabic support.
Overrides the standard wkhtmltopdf rendering for form50 reports only.
"""
import logging
import os
import tempfile
from odoo import models, api
from odoo.http import request

_logger = logging.getLogger(__name__)


class Form50ReportAction(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        """Override for form50 reports to use WeasyPrint instead of wkhtmltopdf."""
        report = self._get_report(report_ref)
        if report and 'form50' in (report.report_name or ''):
            return self._render_with_weasyprint(report, res_ids, data)
        return super()._render_qweb_pdf(report_ref, res_ids, data)

    def _render_with_weasyprint(self, report, res_ids, data):
        """Render using WeasyPrint for proper Arabic support."""
        try:
            import weasyprint
            from weasyprint.text.fonts import FontConfiguration

            # Get HTML content from QWeb
            html_content, _ = self._render_qweb_html(
                report.report_name, res_ids, data=data
            )

            # Configure fonts for Arabic
            font_config = FontConfiguration()

            # Add Arabic font CSS
            arabic_css = weasyprint.CSS(string='''
                @font-face {
                    font-family: "Amiri";
                    src: url("/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf");
                    font-weight: normal;
                }
                @font-face {
                    font-family: "Amiri";
                    src: url("/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf");
                    font-weight: bold;
                }
                * {
                    font-family: "Amiri", serif !important;
                }
                body, div, td, th, p, span {
                    direction: rtl !important;
                }
                @page {
                    size: A4 portrait;
                    margin: 0;
                }
            ''', font_config=font_config)

            # Render to PDF
            pdf = weasyprint.HTML(
                string=html_content.decode('utf-8') if isinstance(html_content, bytes) else html_content,
                base_url='file:///',
            ).write_pdf(
                stylesheets=[arabic_css],
                font_config=font_config,
            )

            return pdf, 'pdf'

        except Exception as e:
            _logger.error("WeasyPrint rendering failed: %s — falling back to wkhtmltopdf", e)
            return super()._render_qweb_pdf(report.report_name, res_ids, data)
