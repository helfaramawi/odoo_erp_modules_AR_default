# -*- coding: utf-8 -*-
import logging
import re
from odoo import models

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

# Injected into HTML <head> before wkhtmltopdf renders — no WeasyPrint
RTL_CSS = (
    "<style>"
    "html,body,div,table,tr,td,th,p,span,h1,h2,h3,h4,h5,li,a{"
    "direction:rtl!important;unicode-bidi:embed!important;"
    "font-family:'Traditional Arabic','Arabic Typesetting',"
    "'Arial Unicode MS','Arial',serif!important;}"
    "@page{size:A4;margin:15mm;}"
    "</style>"
)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_html(self, report_ref, res_ids=None, data=None):
        html_content, content_type = super()._render_qweb_html(
            report_ref, res_ids, data=data
        )

        report = self._get_report(report_ref)
        report_name = report.report_name or ''

        is_port_said = any(report_name.startswith(p) for p in PORT_SAID_PREFIXES)
        is_form50 = 'form50' in report_name
        if not is_port_said or is_form50:
            return html_content, content_type

        as_bytes = isinstance(html_content, bytes)
        html_str = html_content.decode('utf-8', errors='ignore') if as_bytes else html_content

        if '</head>' in html_str:
            html_str = html_str.replace('</head>', RTL_CSS + '</head>', 1)
        elif '<body' in html_str:
            html_str = re.sub(r'(<body[^>]*>)', r'\1' + RTL_CSS, html_str, count=1)
        else:
            html_str = RTL_CSS + html_str

        html_content = html_str.encode('utf-8') if as_bytes else html_str
        return html_content, content_type
