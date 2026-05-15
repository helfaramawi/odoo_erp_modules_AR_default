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

ARABIC_CSS = (
    "html,body,div,table,tr,td,th,p,span,h1,h2,h3,h4,h5,li,a{"
    "font-family:'Arial','Tahoma','DejaVu Sans',sans-serif!important;"
    "direction:rtl!important;unicode-bidi:embed!important;}"
    "@page{size:A4;margin:15mm;}"
)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_html(self, report_ref, res_ids=None, data=None):
        html_content, content_type = super()._render_qweb_html(report_ref, res_ids, data=data)

        try:
            report = self._get_report(report_ref)
            report_name = report.report_name or ''
            is_port_said = any(report_name.startswith(p) for p in PORT_SAID_PREFIXES)
        except Exception:
            is_port_said = False

        if not is_port_said:
            return html_content, content_type

        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8', errors='ignore')

        style_tag = '<style type="text/css">' + ARABIC_CSS + '</style>'

        if '</head>' in html_content:
            html_content = html_content.replace('</head>', style_tag + '</head>', 1)
        elif '<body' in html_content:
            html_content = re.sub(r'(<body[^>]*>)', style_tag + r'\1', html_content, count=1)
        else:
            html_content = style_tag + html_content

        if '<html' in html_content:
            html_content = re.sub(r'<html([^>]*)>', r'<html\1 lang="ar" dir="rtl">', html_content, count=1)

        if '<body' in html_content:
            html_content = re.sub(r'<body([^>]*)>', r'<body\1 dir="rtl">', html_content, count=1)

        return html_content.encode('utf-8'), content_type
