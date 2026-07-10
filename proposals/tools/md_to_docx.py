#!/usr/bin/env python3
"""
Generic Arabic-Markdown -> Word(RTL) converter, reused for the three
proposal documents. Built on manual/common.py so it shares the exact same
RTL styling, fonts, and table formatting as the System Manual and Setup &
Configuration Handbook, but with lighter section numbering (no "Chapter N"
prefix — the markdown headers already carry their own numbers) suited to a
short business proposal rather than a 600-page manual.

Supported markdown subset (matches what the three proposal .md files use):
  # Title                -> cover title (first one only)
  ## Heading              -> level-1 heading
  ### Heading             -> level-2 heading
  ---                      -> section break / page break (first one ignored,
                              since it directly follows the cover title)
  | a | b |                -> table (header row + `---` separator + body rows)
  - item                   -> bullet list
  1. item                  -> numbered list
  > text                   -> callout / note box
  **bold**                 -> inline bold run (supported in paragraphs,
                              table cells, and list items)
  blank line                -> paragraph break

Usage: python3 md_to_docx.py <input.md> <output.docx> <doc_title> <classification>
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "manual"))
from common import (new_document, add_header_footer, ManualBuilder, Numbering,
                     set_para_rtl, style_run, add_field, NAVY, GREY, GOLD)
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def add_rich_paragraph(doc, text, size=12, base_bold=False, align=WD_ALIGN_PARAGRAPH.RIGHT,
                        space_after=6, space_before=0, color=None):
    """Paragraph supporting **bold** inline spans, RTL, justified sizing."""
    p = doc.add_paragraph()
    set_para_rtl(p)
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    pos = 0
    for m in BOLD_RE.finditer(text):
        if m.start() > pos:
            r = p.add_run(text[pos:m.start()])
            style_run(r, size=size, bold=base_bold, color=color)
        r = p.add_run(m.group(1))
        style_run(r, size=size, bold=True, color=color)
        pos = m.end()
    if pos < len(text):
        r = p.add_run(text[pos:])
        style_run(r, size=size, bold=base_bold, color=color)
    return p


def add_rich_run_to_cell(cell, text, size=8, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    set_para_rtl(p)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    pos = 0
    for m in BOLD_RE.finditer(text):
        if m.start() > pos:
            r = p.add_run(text[pos:m.start()])
            style_run(r, size=size, bold=bold, color=color)
        r = p.add_run(m.group(1))
        style_run(r, size=size, bold=True, color=color)
        pos = m.end()
    if pos < len(text):
        r = p.add_run(text[pos:])
        style_run(r, size=size, bold=bold, color=color)
    if not text:
        r = p.add_run("")
        style_run(r, size=size, bold=bold, color=color)


def strip_bold(text):
    return BOLD_RE.sub(r"\1", text)


def parse_table_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def is_separator_row(cells):
    return all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in cells)


def render_table(mb, headers, rows):
    t = mb.doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    from common import (set_rtl_table, shade_cell, set_cell_margins, WD_TABLE_ALIGNMENT,
                        WD_ALIGN_VERTICAL, OxmlElement, qn)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_rtl_table(t)
    trPr = t.rows[0]._tr.get_or_add_trPr()
    trPr.append(OxmlElement('w:tblHeader'))
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        add_rich_run_to_cell(hdr[i], strip_bold(h), size=9, bold=True, color=(0xFF, 0xFF, 0xFF))
        shade_cell(hdr[i], "0B2E4E")
        hdr[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        set_cell_margins(hdr[i])
    for ridx, row in enumerate(rows):
        cells = t.add_row().cells
        for i in range(len(headers)):
            val = row[i] if i < len(row) else ""
            bold = val.strip().startswith("**") and val.strip().endswith("**")
            add_rich_run_to_cell(cells[i], val, size=9, bold=False)
            if ridx % 2 == 1:
                shade_cell(cells[i], "F2F5F8")
            set_cell_margins(cells[i])
    mb.para("", size=2)
    return t


def convert(md_path, out_path, doc_title, classification, cover_meta=None):
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    doc = new_document()
    num = Numbering()
    mb = ManualBuilder(doc, num)

    title_rendered = False
    subtitle_rendered = False
    seen_first_rule = False
    toc_inserted = False

    i = 0
    n = len(lines)
    bullet_buf = []
    numbered_buf = []

    def flush_bullets():
        nonlocal bullet_buf
        if bullet_buf:
            for it in bullet_buf:
                p = doc.add_paragraph(style="List Bullet")
                set_para_rtl(p)
                pos = 0
                for m in BOLD_RE.finditer(it):
                    if m.start() > pos:
                        r = p.add_run(it[pos:m.start()]); style_run(r, size=12)
                    r = p.add_run(m.group(1)); style_run(r, size=12, bold=True)
                    pos = m.end()
                if pos < len(it):
                    r = p.add_run(it[pos:]); style_run(r, size=12)
            bullet_buf = []

    def flush_numbered():
        nonlocal numbered_buf
        if numbered_buf:
            for it in numbered_buf:
                p = doc.add_paragraph(style="List Number")
                set_para_rtl(p)
                pos = 0
                for m in BOLD_RE.finditer(it):
                    if m.start() > pos:
                        r = p.add_run(it[pos:m.start()]); style_run(r, size=12)
                    r = p.add_run(m.group(1)); style_run(r, size=12, bold=True)
                    pos = m.end()
                if pos < len(it):
                    r = p.add_run(it[pos:]); style_run(r, size=12)
            numbered_buf = []

    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_bullets(); flush_numbered()
            i += 1
            continue

        if stripped.startswith("# ") and not title_rendered:
            flush_bullets(); flush_numbered()
            title_rendered = True
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(60)
            set_para_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(stripped[2:].strip())
            style_run(r, size=26, bold=True, color=NAVY)
            i += 1
            continue

        if stripped.startswith("## ") and title_rendered and not subtitle_rendered and not seen_first_rule:
            flush_bullets(); flush_numbered()
            subtitle_rendered = True
            p = doc.add_paragraph()
            set_para_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(stripped[3:].strip())
            style_run(r, size=15, color=GREY)
            for _ in range(2):
                doc.add_paragraph()
            i += 1
            continue

        if stripped == "---":
            flush_bullets(); flush_numbered()
            if not seen_first_rule:
                seen_first_rule = True
                if not toc_inserted:
                    toc_inserted = True
                    tocp = doc.add_paragraph()
                    tocp.paragraph_format.space_before = Pt(20)
                    set_para_rtl(tocp)
                    r = tocp.add_run("فهرس المحتويات")
                    style_run(r, size=14, bold=True, color=NAVY)
                    fp = doc.add_paragraph()
                    set_para_rtl(fp)
                    add_field(fp, 'TOC \\o "1-2" \\h \\z \\u', "اضغط F9 لتحديث الفهرس بعد فتح المستند في Word")
                    doc.add_page_break()
            else:
                doc.add_page_break()
            i += 1
            continue

        if stripped.startswith("#### "):
            flush_bullets(); flush_numbered()
            mb.heading(3, strip_bold(stripped[5:].strip()))
            i += 1
            continue
        if stripped.startswith("### "):
            flush_bullets(); flush_numbered()
            mb.heading(2, strip_bold(stripped[4:].strip()))
            i += 1
            continue
        if stripped.startswith("## "):
            flush_bullets(); flush_numbered()
            mb.heading(1, strip_bold(stripped[3:].strip()))
            i += 1
            continue

        if stripped.startswith("> "):
            flush_bullets(); flush_numbered()
            mb.note(strip_bold(stripped[2:].strip()))
            i += 1
            continue

        if stripped.startswith("|"):
            flush_bullets(); flush_numbered()
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = [parse_table_row(l) for l in table_lines]
            if len(rows) >= 2 and is_separator_row(rows[1]):
                headers = rows[0]
                body = rows[2:]
            else:
                headers = rows[0]
                body = rows[1:]
            render_table(mb, headers, body)
            continue

        if re.match(r"^-\s+", stripped):
            flush_numbered()
            bullet_buf.append(re.sub(r"^-\s+", "", stripped))
            i += 1
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_bullets()
            numbered_buf.append(re.sub(r"^\d+\.\s+", "", stripped))
            i += 1
            continue

        # plain paragraph
        flush_bullets(); flush_numbered()
        add_rich_paragraph(doc, stripped, size=12)
        i += 1

    flush_bullets(); flush_numbered()

    add_header_footer(doc, doc_title=doc_title, classification=classification)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc.save(out_path)
    print(f"Saved -> {out_path}  (paragraphs={len(doc.paragraphs)}, tables={len(doc.tables)})")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("usage: md_to_docx.py <input.md> <output.docx> <doc_title> <classification>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
