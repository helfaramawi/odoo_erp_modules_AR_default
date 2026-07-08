"""
Shared docx-building infrastructure for the Paradise AI / Port Said Governorate
Arabic Odoo System Manual.

Provides: RTL Arabic styling, cover page, document-control tables, automatic
TOC / List of Figures / List of Tables fields (real Word field codes so they
refresh in Word/LibreOffice), numbered headings (manually computed so they are
always correct without relying on multilevel-list XML), numbered figure/table
captions (via SEQ fields so Word's native List of Figures/Tables mechanism
works), bookmarked cross-references, and reusable documentation templates for
screens / reports / menus / fields, matching the manual's required structure.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.style import WD_STYLE_TYPE

ARABIC_FONT = "Arial"
LATIN_FONT = "Arial"

NAVY = (0x0B, 0x2E, 0x4E)
GOLD = (0xB8, 0x86, 0x0B)
GREY = (0x59, 0x59, 0x59)
LIGHT_GREY = (0xE9, 0xED, 0xF1)


# --------------------------------------------------------------------------
# low level OOXML helpers
# --------------------------------------------------------------------------

PPR_ORDER = [
    'w:pStyle', 'w:keepNext', 'w:keepLines', 'w:pageBreakBefore', 'w:framePr',
    'w:widowControl', 'w:numPr', 'w:suppressLineNumbers', 'w:pBdr', 'w:shd',
    'w:tabs', 'w:suppressAutoHyphens', 'w:kinsoku', 'w:wordWrap',
    'w:overflowPunct', 'w:topLinePunct', 'w:autoSpaceDE', 'w:autoSpaceDN',
    'w:bidi', 'w:adjustRightInd', 'w:snapToGrid', 'w:spacing', 'w:ind',
    'w:contextualSpacing', 'w:mirrorIndents', 'w:suppressOverlap', 'w:jc',
    'w:textDirection', 'w:textAlignment', 'w:textboxTightWrap', 'w:outlineLvl',
    'w:divId', 'w:cnfStyle', 'w:rPr', 'w:sectPr', 'w:pPrChange',
]

SECTPR_ORDER = [
    'w:headerReference', 'w:footerReference', 'w:footnotePr', 'w:endnotePr',
    'w:type', 'w:pgSz', 'w:pgMar', 'w:paperSrc', 'w:pgBorders', 'w:lnNumType',
    'w:pgNumType', 'w:cols', 'w:formProt', 'w:vAlign', 'w:noEndnote',
    'w:titlePg', 'w:textDirection', 'w:bidi', 'w:rtlGutter', 'w:docGrid',
    'w:printerSettings', 'w:sectPrChange',
]

TBLPR_ORDER = [
    'w:tblStyle', 'w:tblpPr', 'w:tblOverlap', 'w:bidiVisual',
    'w:tblStyleRowBandSize', 'w:tblStyleColBandSize', 'w:tblW', 'w:jc',
    'w:tblCellSpacing', 'w:tblInd', 'w:tblBorders', 'w:shd', 'w:tblLayout',
    'w:tblCellMar', 'w:tblLook', 'w:tblCaption', 'w:tblDescription',
    'w:tblPrChange',
]


def insert_ordered(parent, element, tag, order_list):
    idx = order_list.index(tag)
    successors = order_list[idx + 1:]
    parent.insert_element_before(element, *successors)


def _rpr(run):
    return run._r.get_or_add_rPr()


def set_run_rtl(run):
    rPr = _rpr(run)
    el = OxmlElement('w:rtl')
    rPr.append(el)


def set_para_rtl(paragraph, align_right=True):
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    insert_ordered(pPr, bidi, 'w:bidi', PPR_ORDER)
    if align_right:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def style_run(run, size=12, bold=False, italic=False, color=None, font=None):
    f = font or LATIN_FONT
    run.font.name = f
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)
    rPr = _rpr(run)
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), f)
    rFonts.set(qn('w:hAnsi'), f)
    rFonts.set(qn('w:cs'), ARABIC_FONT)
    rFonts.set(qn('w:eastAsia'), ARABIC_FONT)
    set_run_rtl(run)
    lang = OxmlElement('w:lang')
    lang.set(qn('w:val'), 'ar-EG')
    lang.set(qn('w:bidi'), 'ar-EG')
    rPr.append(lang)


def add_field(paragraph, field_code, result_text=""):
    """Insert a real Word field (TOC, SEQ, REF, PAGE ...)."""
    run = paragraph.add_run()
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = field_code
    fld_sep = OxmlElement('w:fldChar')
    fld_sep.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t')
    t.text = result_text
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    r = run._r
    r.append(fld_begin)
    r.append(instr)
    r.append(fld_sep)
    r.append(t)
    r.append(fld_end)
    style_run(run, size=12)
    return run


_bookmark_id = [0]


def add_bookmark(paragraph, name):
    _bookmark_id[0] += 1
    bid = str(_bookmark_id[0])
    start = OxmlElement('w:bookmarkStart')
    start.set(qn('w:id'), bid)
    start.set(qn('w:name'), name)
    end = OxmlElement('w:bookmarkEnd')
    end.set(qn('w:id'), bid)
    paragraph._p.append(start)
    paragraph._p.append(end)


def add_cross_reference(paragraph, bookmark_name, display_text):
    add_field(paragraph, f'REF {bookmark_name} \\h', display_text)


def set_update_fields_on_open(document):
    settings = document.settings.element
    el = OxmlElement('w:updateFields')
    el.set(qn('w:val'), 'true')
    settings.append(el)


def shade_cell(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement('w:tcMar')
    for tag, val in (('top', top), ('bottom', bottom), ('start', left), ('end', right)):
        node = OxmlElement(f'w:{tag}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        mar.append(node)
    tcPr.append(mar)


def set_rtl_table(table):
    tblPr = table._tbl.tblPr
    bidi = OxmlElement('w:bidiVisual')
    insert_ordered(tblPr, bidi, 'w:bidiVisual', TBLPR_ORDER)


# --------------------------------------------------------------------------
# Numbering tracker for chapters/sections and figures/tables
# --------------------------------------------------------------------------

class Numbering:
    def __init__(self):
        self.c = [0, 0, 0, 0]
        self.fig = 0
        self.tbl = 0
        self.chapter_no = 0

    def reset_chapter(self, n=None):
        self.c = [n if n is not None else self.c[0] + 1, 0, 0, 0]
        self.chapter_no = self.c[0]
        return str(self.c[0])

    def h2(self):
        self.c[1] += 1
        self.c[2] = 0
        self.c[3] = 0
        return f"{self.c[0]}.{self.c[1]}"

    def h3(self):
        self.c[2] += 1
        self.c[3] = 0
        return f"{self.c[0]}.{self.c[1]}.{self.c[2]}"

    def h4(self):
        self.c[3] += 1
        return f"{self.c[0]}.{self.c[1]}.{self.c[2]}.{self.c[3]}"

    def next_fig(self):
        self.fig += 1
        return self.fig

    def next_tbl(self):
        self.tbl += 1
        return self.tbl


# --------------------------------------------------------------------------
# Builder
# --------------------------------------------------------------------------

class ManualBuilder:
    def __init__(self, document, numbering):
        self.doc = document
        self.num = numbering

    # ---- basic text -----------------------------------------------------
    def para(self, text="", size=12, bold=False, italic=False, color=None,
              align=WD_ALIGN_PARAGRAPH.RIGHT, style=None, space_after=6,
              space_before=0):
        p = self.doc.add_paragraph(style=style)
        set_para_rtl(p)
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        if text:
            r = p.add_run(text)
            style_run(r, size=size, bold=bold, italic=italic, color=color)
        return p

    def heading(self, level, text, number=None):
        p = self.doc.add_paragraph(style=f"Heading {level}")
        set_para_rtl(p)
        p.paragraph_format.space_before = Pt([0, 24, 16, 10][level - 1])
        p.paragraph_format.space_after = Pt(8)
        label = f"{number}  {text}" if number else text
        r = p.add_run(label)
        sizes = {1: 20, 2: 16, 3: 13.5, 4: 12}
        colors = {1: NAVY, 2: NAVY, 3: GREY, 4: GREY}
        style_run(r, size=sizes[level], bold=True, color=colors[level])
        return p

    def h1(self, text, chapter_no=None):
        n = self.num.reset_chapter(chapter_no)
        self.page_break()
        p = self.heading(1, text, number=f"الفصل {n} —")
        add_bookmark(p, f"ch{n}")
        return p

    def h2(self, text):
        n = self.num.h2()
        self.page_break()
        p = self.heading(2, text, number=n)
        add_bookmark(p, f"sec{n.replace('.', '_')}")
        return p

    def h3(self, text):
        n = self.num.h3()
        return self.heading(3, text, number=n)

    def h4(self, text):
        n = self.num.h4()
        return self.heading(4, text, number=n)

    def page_break(self):
        self.doc.add_page_break()

    def bullets(self, items, style="List Bullet"):
        for it in items:
            p = self.doc.add_paragraph(style=style)
            set_para_rtl(p)
            r = p.add_run(it)
            style_run(r, size=12)

    def numbered(self, items, style="List Number"):
        for it in items:
            p = self.doc.add_paragraph(style=style)
            set_para_rtl(p)
            r = p.add_run(it)
            style_run(r, size=12)

    # ---- callouts ---------------------------------------------------------
    def _callout(self, label, text, color):
        p = self.doc.add_paragraph()
        set_para_rtl(p)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:fill'), 'F2F2F2')
        insert_ordered(pPr, shd, 'w:shd', PPR_ORDER)
        r1 = p.add_run(f"{label}: ")
        style_run(r1, size=12, bold=True, color=color)
        r2 = p.add_run(text)
        style_run(r2, size=12)
        return p

    def note(self, text):
        return self._callout("ملاحظة", text, NAVY)

    def tip(self, text):
        return self._callout("إرشاد", text, (0x1B, 0x5E, 0x20))

    def warning(self, text):
        return self._callout("تحذير", text, (0x8B, 0x00, 0x00))

    def placeholder(self, text):
        p = self.doc.add_paragraph()
        set_para_rtl(p)
        r = p.add_run(f"[{text}]")
        style_run(r, size=12, italic=True, color=(0x8B, 0x5A, 0x00))
        return p

    # ---- figures / tables ---------------------------------------------------
    def screenshot(self, description, resolution="1920×1080"):
        n = self.num.next_fig()
        box = self.doc.add_paragraph()
        set_para_rtl(box)
        box.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pPr = box._p.get_or_add_pPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:fill'), 'F5F5F5')
        insert_ordered(pPr, shd, 'w:shd', PPR_ORDER)
        border = OxmlElement('w:pBdr')
        for side in ('top', 'bottom', 'start', 'end'):
            b = OxmlElement(f'w:{side}')
            b.set(qn('w:val'), 'single')
            b.set(qn('w:sz'), '8')
            b.set(qn('w:color'), '999999')
            border.append(b)
        insert_ordered(pPr, border, 'w:pBdr', PPR_ORDER)
        r = box.add_run(f"\n[لقطة شاشة هنا — {description}]\nدقة الالتقاط الموصى بها: {resolution}\n")
        style_run(r, size=11, italic=True, color=(0x66, 0x66, 0x66))

        cap = self.doc.add_paragraph(style="Caption")
        set_para_rtl(cap)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = cap.add_run("شكل ")
        style_run(r1, size=11, bold=True)
        r2 = cap.add_run(f"{self.num.chapter_no}-{n}")
        style_run(r2, size=11, bold=True)
        r3 = cap.add_run(f": {description}")
        style_run(r3, size=11)
        add_bookmark(cap, f"fig_{self.num.chapter_no}_{n}")
        return f"{self.num.chapter_no}-{n}"

    def table_caption(self, description):
        n = self.num.next_tbl()
        cap = self.doc.add_paragraph(style="Caption")
        set_para_rtl(cap)
        r1 = cap.add_run("جدول ")
        style_run(r1, size=11, bold=True)
        r2 = cap.add_run(f"{self.num.chapter_no}-{n}")
        style_run(r2, size=11, bold=True)
        r3 = cap.add_run(f": {description}")
        style_run(r3, size=11)
        add_bookmark(cap, f"tbl_{self.num.chapter_no}_{n}")
        return f"{self.num.chapter_no}-{n}"

    def table(self, headers, rows, caption=None, col_widths=None):
        if caption:
            self.table_caption(caption)
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_rtl_table(t)
        hdr = t.rows[0].cells
        for i, h in enumerate(headers):
            hdr[i].text = ""
            p = hdr[i].paragraphs[0]
            set_para_rtl(p)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(h)
            style_run(r, size=10, bold=True, color=(0xFF, 0xFF, 0xFF))
            shade_cell(hdr[i], "0B2E4E")
            hdr[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(hdr[i])
        for ridx, row in enumerate(rows):
            cells = t.add_row().cells
            for i, val in enumerate(row):
                cells[i].text = ""
                p = cells[i].paragraphs[0]
                set_para_rtl(p)
                r = p.add_run("" if val is None else str(val))
                style_run(r, size=10)
                if ridx % 2 == 1:
                    shade_cell(cells[i], "F2F5F8")
                set_cell_margins(cells[i])
        if col_widths:
            for row in t.rows:
                for i, w in enumerate(col_widths):
                    row.cells[i].width = Cm(w)
        self.para("", size=2)
        return t

    # ---- field documentation table --------------------------------------
    def field_table(self, fields, caption="بيانات الحقول"):
        """fields: list of dicts with keys name, arabic, desc, mandatory,
        default, validation, example, related"""
        headers = ["اسم الحقل (تقني)", "الاسم بالعربية", "الوصف", "إلزامي",
                   "القيمة الافتراضية", "قاعدة التحقق", "مثال", "الجداول المرتبطة"]
        rows = []
        for f in fields:
            rows.append([
                f.get("name", ""), f.get("arabic", ""), f.get("desc", ""),
                "نعم" if f.get("mandatory") else "لا",
                f.get("default", "—"), f.get("validation", "—"),
                f.get("example", "—"), f.get("related", "—"),
            ])
        return self.table(headers, rows, caption=caption,
                            col_widths=[3, 3, 4, 1.5, 2.5, 3, 2.5, 3])

    # ---- screen documentation template -----------------------------------
    def screen_doc(self, title, purpose, navigation, description, buttons=None,
                    fields=None, validations=None, business_rules=None,
                    related_screens=None, tips=None, warnings=None, notes=None,
                    screenshot_desc=None):
        self.h3(f"شاشة: {title}")
        self.para(f"الغرض: {purpose}", bold=False)
        p = self.para("")
        r1 = p.add_run("مسار التنقل: ")
        style_run(r1, size=12, bold=True)
        r2 = p.add_run(navigation)
        style_run(r2, size=12)
        self.h4("الوصف")
        self.para(description)
        if screenshot_desc:
            self.screenshot(screenshot_desc)
        if buttons:
            self.h4("الأزرار")
            self.bullets(buttons)
        if fields:
            self.h4("الحقول")
            self.field_table(fields, caption=f"حقول شاشة {title}")
        if validations:
            self.h4("قواعد التحقق (Validations)")
            self.bullets(validations)
        if business_rules:
            self.h4("قواعد العمل")
            self.bullets(business_rules)
        if related_screens:
            self.h4("شاشات ذات صلة")
            self.bullets(related_screens)
        if tips:
            for t in tips:
                self.tip(t)
        if warnings:
            for w in warnings:
                self.warning(w)
        if notes:
            for n in notes:
                self.note(n)

    # ---- report documentation template -----------------------------------
    def report_doc(self, title, purpose, source_data, filters, sorting=None,
                    export_formats=None, charts=None, kpis=None,
                    sample_note=None, screenshot_desc=None):
        self.h3(f"تقرير: {title}")
        self.para(f"الغرض من التقرير: {purpose}")
        self.h4("مصدر البيانات")
        self.para(source_data)
        self.h4("عوامل التصفية (Filters)")
        self.bullets(filters)
        if sorting:
            self.h4("الفرز والتجميع")
            self.para(sorting)
        self.h4("صيغ التصدير")
        self.bullets(export_formats or ["Excel (XLSX)", "PDF", "طباعة مباشرة"])
        if charts:
            self.h4("الرسوم البيانية")
            self.bullets(charts)
        if kpis:
            self.h4("مؤشرات الأداء المرتبطة (KPIs)")
            self.bullets(kpis)
        if screenshot_desc:
            self.screenshot(screenshot_desc)
        if sample_note:
            self.note(sample_note)

    # ---- menu documentation template --------------------------------------
    def menu_table(self, rows, caption="بنية القوائم"):
        headers = ["المسار الكامل", "الغرض", "صلاحيات الوصول"]
        return self.table(headers, rows, caption=caption, col_widths=[6, 6, 4])

    # ---- standard functional-topic template (Ch.4/5/8/9 style) -----------
    SECTION_LABELS = {
        "overview": "نظرة عامة (Overview)",
        "objectives": "الأهداف (Objectives)",
        "process": "مسار العمل التجاري (Business Process)",
        "navigation": "مسار التنقل بالقوائم (Menu Navigation)",
        "configuration": "الإعداد (Configuration)",
        "master_data": "البيانات الرئيسية (Master Data)",
        "transaction_flow": "مسار المعاملة (Transaction Flow)",
        "reports": "التقارير (Reports)",
        "dashboards": "لوحات المتابعة (Dashboards)",
        "approvals": "الموافقات (Approvals)",
        "validation_rules": "قواعد التحقق (Validation Rules)",
        "accounting_entries": "القيود المحاسبية (Accounting Entries)",
        "security": "الأمان (Security)",
        "common_errors": "الأخطاء الشائعة (Common Errors)",
        "troubleshooting": "استكشاف الأخطاء وإصلاحها (Troubleshooting)",
        "best_practices": "أفضل الممارسات (Best Practices)",
        "related_screens": "شاشات ذات صلة (Related Screens)",
        "related_reports": "تقارير ذات صلة (Related Reports)",
        "customization": "التخصيص (Customization)",
        "ai_features": "ميزات الذكاء الاصطناعي (AI Features)",
        "integrations": "التكاملات ذات الصلة (Related Integrations)",
        "kpis": "مؤشرات الأداء الرئيسية (KPIs)",
        "faqs": "أسئلة شائعة (FAQs)",
        "exercises": "تمارين تطبيقية (Exercises)",
    }
    SECTION_ORDER = list(SECTION_LABELS.keys())

    def topic_doc(self, title, sections, screenshot_desc=None):
        """Render a full standard functional-topic section (Chapters 4/5/8/9).

        `sections` is a dict keyed by the short names in SECTION_LABELS; each
        value is either a string (rendered as a paragraph), a list (rendered
        as bullets), or a list-of-lists tuple ("table", headers, rows, caption).
        """
        self.h2(title)
        if screenshot_desc:
            self.screenshot(screenshot_desc)
        for key in self.SECTION_ORDER:
            if key not in sections:
                continue
            value = sections[key]
            self.h3(self.SECTION_LABELS[key])
            if isinstance(value, tuple) and value and value[0] == "table":
                _, headers, rows, caption = value
                self.table(headers, rows, caption=caption)
            elif isinstance(value, list):
                self.bullets(value)
            else:
                self.para(value)


# --------------------------------------------------------------------------
# Document scaffolding: styles, page setup, header/footer, cover, TOC
# --------------------------------------------------------------------------

def new_document():
    doc = Document()
    _configure_styles(doc)
    _configure_page(doc)
    set_update_fields_on_open(doc)
    return doc


def _configure_styles(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = LATIN_FONT
    normal.font.size = Pt(12)
    rpr = normal.element.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), LATIN_FONT)
    rFonts.set(qn('w:hAnsi'), LATIN_FONT)
    rFonts.set(qn('w:cs'), ARABIC_FONT)
    rpr.append(rFonts)

    for lvl, size in ((1, 20), (2, 16), (3, 13.5), (4, 12)):
        st = styles[f"Heading {lvl}"]
        st.font.name = LATIN_FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(*NAVY)

    try:
        cap = styles["Caption"]
    except KeyError:
        cap = styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    cap.font.name = LATIN_FONT
    cap.font.size = Pt(11)
    cap.font.italic = True
    cap.font.color.rgb = RGBColor(*GREY)


def _configure_page(doc):
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    sectPr = section._sectPr
    bidi = OxmlElement('w:bidi')
    insert_ordered(sectPr, bidi, 'w:bidi', SECTPR_ORDER)


def add_header_footer(doc, doc_title="دليل النظام — الديوان العام لمحافظة بورسعيد على أوديو",
                        classification="سري — للاستخدام الداخلي الرسمي فقط"):
    section = doc.sections[0]
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)

    header = section.header
    hp = header.paragraphs[0]
    set_para_rtl(hp)
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = hp.add_run(doc_title)
    style_run(r, size=9, bold=True, color=(0x66, 0x66, 0x66))

    footer = section.footer
    fp = footer.paragraphs[0]
    set_para_rtl(fp)
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = fp.add_run(f"{classification}   |   صفحة ")
    style_run(r1, size=9, color=(0x66, 0x66, 0x66))
    add_field(fp, "PAGE", "1")
    r2 = fp.add_run(" من ")
    style_run(r2, size=9, color=(0x66, 0x66, 0x66))
    add_field(fp, "NUMPAGES", "1")


def add_cover_page(doc, meta):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(40)
    set_para_rtl(p)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"[{meta.get('vendor_logo_placeholder', 'شعار Paradise AI Solutions')}]")
    style_run(r, size=11, italic=True, color=(0x99, 0x99, 0x99))

    p2 = doc.add_paragraph()
    set_para_rtl(p2)
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(f"[{meta.get('customer_logo_placeholder', 'شعار العميل')}]")
    style_run(r2, size=11, italic=True, color=(0x99, 0x99, 0x99))

    for _ in range(3):
        doc.add_paragraph()

    title = doc.add_paragraph()
    set_para_rtl(title)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run(meta["system_name"])
    style_run(r, size=30, bold=True, color=NAVY)

    sub = doc.add_paragraph()
    set_para_rtl(sub)
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run(meta["system_subtitle"])
    style_run(r, size=16, color=GREY)

    doc.add_paragraph()
    sub2 = doc.add_paragraph()
    set_para_rtl(sub2)
    sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub2.add_run("دليل النظام الشامل — Comprehensive System Manual")
    style_run(r, size=14, bold=True, color=GOLD)

    for _ in range(4):
        doc.add_paragraph()

    info_rows = [
        ("اسم النظام", meta["system_name"]),
        ("الإصدار (Version)", meta["version"]),
        ("رقم المستند (Document No.)", meta["doc_number"]),
        ("رقم المراجعة (Revision No.)", meta["revision_no"]),
        ("تاريخ الإصدار", meta["issue_date"]),
        ("إعداد (Prepared By)", meta["prepared_by"]),
        ("مراجعة (Reviewed By)", meta["reviewed_by"]),
        ("اعتماد (Approved By)", meta["approved_by"]),
        ("الجهة المطوّرة (Vendor)", meta["vendor"]),
        ("الجهة المستفيدة (Client)", meta["client"]),
        ("تصنيف السرية", meta["classification"]),
    ]
    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_rtl_table(t)
    for label, value in info_rows:
        cells = t.add_row().cells
        cells[0].text = ""
        p0 = cells[0].paragraphs[0]
        set_para_rtl(p0)
        p0.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rr = p0.add_run(label)
        style_run(rr, size=10, bold=True, color=(0xFF, 0xFF, 0xFF))
        shade_cell(cells[0], "0B2E4E")
        set_cell_margins(cells[0])
        cells[1].text = ""
        p1 = cells[1].paragraphs[0]
        set_para_rtl(p1)
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rr2 = p1.add_run(str(value))
        style_run(rr2, size=10)
        set_cell_margins(cells[1])
        cells[0].width = Cm(6)
        cells[1].width = Cm(9)

    doc.add_paragraph()
    conf = doc.add_paragraph()
    set_para_rtl(conf)
    conf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = conf.add_run(meta["confidentiality_statement"])
    style_run(r, size=10.5, italic=True, color=(0x8B, 0x00, 0x00))
    doc.add_page_break()


def add_document_control(doc, mb: ManualBuilder, revisions, approvals, distribution):
    mb.heading(1, "ضبط المستند (Document Control)")
    mb.doc.add_paragraph()
    hp = mb.para("سجل المراجعات (Revision History)", bold=True, size=14, color=NAVY)
    mb.table(
        ["رقم المراجعة", "التاريخ", "الوصف", "المُعد", "الحالة"],
        revisions,
        caption="سجل مراجعات المستند",
        col_widths=[2, 2.5, 6.5, 3, 2],
    )

    mb.para("الاعتمادات (Approvals)", bold=True, size=14, color=NAVY)
    mb.table(
        ["الدور", "الاسم", "التوقيع", "التاريخ"],
        approvals,
        caption="جدول الاعتمادات",
        col_widths=[4, 5, 3, 3],
    )

    mb.para("قائمة التوزيع (Distribution List)", bold=True, size=14, color=NAVY)
    mb.bullets(distribution)
    mb.doc.add_page_break()


def add_toc_section(doc, mb: ManualBuilder):
    mb.heading(1, "فهرس المحتويات (Table of Contents)")
    p = doc.add_paragraph()
    set_para_rtl(p)
    add_field(p, 'TOC \\o "1-4" \\h \\z \\u', "اضغط F9 أو ⌘/Ctrl لتحديث الفهرس بعد فتح المستند في Word")
    doc.add_page_break()

    mb.heading(1, "فهرس الأشكال (List of Figures)")
    p2 = doc.add_paragraph()
    set_para_rtl(p2)
    add_field(p2, 'TOC \\h \\z \\c "Figure"', "قائمة الأشكال — تُحدَّث تلقائياً")
    doc.add_page_break()

    mb.heading(1, "فهرس الجداول (List of Tables)")
    p3 = doc.add_paragraph()
    set_para_rtl(p3)
    add_field(p3, 'TOC \\h \\z \\c "Table"', "قائمة الجداول — تُحدَّث تلقائياً")
    doc.add_page_break()
