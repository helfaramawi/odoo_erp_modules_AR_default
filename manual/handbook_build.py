#!/usr/bin/env python3
"""Entry point: assembles the Setup & Configuration Handbook .docx.

Run: python3 manual/handbook_build.py
Output: manual/output/Paradise_AI_PortSaid_Setup_Configuration_Handbook.docx

Distinct from build.py (the System Manual) — this handbook is a
reverse-engineering-grade technical reference that cites actual files, ACL
rows, SQL constraints, cron jobs, etc., extracted by
manual/tools/extract_modules.py, and explicitly marks anything not found in
the source (per handbook_meta.NOT_FOUND) instead of inventing it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (new_document, add_header_footer, add_cover_page,
                     add_document_control, add_toc_section, add_index_section,
                     ManualBuilder, Numbering)
from handbook_meta import META, REVISIONS, APPROVALS, DISTRIBUTION

from handbook_content import ch01_introduction
from handbook_content import ch02_architecture
from handbook_content import ch03_security
from handbook_content import ch04_finance_config
from handbook_content import ch05_scm_config
from handbook_content import ch06_custom_modules
from handbook_content import ch07_database
from handbook_content import ch08_reports
from handbook_content import ch09_workflows
from handbook_content import ch10_ai_agents
from handbook_content import ch11_appendices

CHAPTERS = [
    ch01_introduction,
    ch02_architecture,
    ch03_security,
    ch04_finance_config,
    ch05_scm_config,
    ch06_custom_modules,
    ch07_database,
    ch08_reports,
    ch09_workflows,
    ch10_ai_agents,
    ch11_appendices,
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

    add_index_section(doc, mb)

    add_header_footer(doc, doc_title=f"{META['system_name']} — {META['client']}",
                       classification=META['classification'])

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "Paradise_AI_PortSaid_Setup_Configuration_Handbook.docx")
    doc.save(out_path)
    print(f"Saved handbook -> {out_path}")
    print(f"Paragraphs: {len(doc.paragraphs)}  Tables: {len(doc.tables)}")


if __name__ == "__main__":
    main()
