#!/usr/bin/env python3
"""Entry point: assembles the full Arabic System Manual .docx.

Run: python3 manual/build.py
Output: manual/output/Paradise_AI_PortSaid_Odoo_System_Manual.docx
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (new_document, add_header_footer, add_cover_page,
                     add_document_control, add_toc_section, ManualBuilder,
                     Numbering)
from meta import META, REVISIONS, APPROVALS, DISTRIBUTION

from content import ch01_introduction
from content import ch02_architecture
from content import ch03_org_structure
from content import ch04_finance
from content import ch05_supply_chain
from content import ch06_customizations
from content import ch07_ai_agents
from content import ch08_reports
from content import ch09_dashboards
from content import ch10_security
from content import ch11_administration
from content import ch12_troubleshooting
from content import ch13_faq
from content import ch14_scenarios
from content import ch15_appendices

CHAPTERS = [
    ch01_introduction,
    ch02_architecture,
    ch03_org_structure,
    ch04_finance,
    ch05_supply_chain,
    ch06_customizations,
    ch07_ai_agents,
    ch08_reports,
    ch09_dashboards,
    ch10_security,
    ch11_administration,
    ch12_troubleshooting,
    ch13_faq,
    ch14_scenarios,
    ch15_appendices,
]


def main():
    doc = new_document()
    add_cover_page(doc, META)

    num = Numbering()
    mb = ManualBuilder(doc, num)

    add_document_control(doc, mb, REVISIONS, APPROVALS, DISTRIBUTION)
    add_toc_section(doc, mb)

    for chapter in CHAPTERS:
        chapter.build(mb)

    add_header_footer(doc, doc_title=f"{META['system_name']} — {META['client']}",
                       classification=META['classification'])

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "Paradise_AI_PortSaid_Odoo_System_Manual.docx")
    doc.save(out_path)
    print(f"Saved manual -> {out_path}")
    print(f"Paragraphs: {len(doc.paragraphs)}  Tables: {len(doc.tables)}")


if __name__ == "__main__":
    main()
