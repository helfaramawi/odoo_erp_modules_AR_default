#!/usr/bin/env python3
"""
Convert RFP markdown files to RTL Word documents.
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy
import re
import sys

# ── helpers ──────────────────────────────────────────────────────────────────

def set_rtl(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement('w:bidi')
    pPr.append(bidi)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT

def set_ltr(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

def set_cell_rtl(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    bidi = OxmlElement('w:textDirection')
    bidi.set(qn('w:val'), 'btLr')
    # set paragraph RTL
    for para in cell.paragraphs:
        set_rtl(para)

def set_run_rtl(run):
    rPr = run._r.get_or_add_rPr()
    rtl = OxmlElement('w:rtl')
    rPr.append(rtl)

def set_doc_rtl(doc):
    """Set document default to RTL."""
    settings = doc.settings.element
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    bidi = OxmlElement('w:bidi')
    settings.append(bidi)

def set_table_rtl(table):
    tbl = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    bidi = OxmlElement('w:bidiVisual')
    tblPr.append(bidi)
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                set_rtl(para)
                for run in para.runs:
                    set_run_rtl(run)

def shade_cell(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def add_heading(doc, text, level=1, rtl=True):
    style_map = {1: 'Heading 1', 2: 'Heading 2', 3: 'Heading 3'}
    p = doc.add_paragraph(style=style_map.get(level, 'Heading 1'))
    run = p.add_run(text)
    if level == 1:
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
    elif level == 2:
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)
    else:
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
    if rtl:
        set_rtl(p)
        set_run_rtl(run)
    else:
        set_ltr(p)
    return p

def add_para(doc, text, bold=False, rtl=True, size=10):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    if rtl:
        set_rtl(p)
        set_run_rtl(run)
    else:
        set_ltr(p)
    return p

def add_table(doc, headers, rows, rtl=True, header_color='1F497D'):
    col_count = len(headers)
    table = doc.add_table(rows=1 + len(rows), cols=col_count)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # header row
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.text = ''
        shade_cell(cell, header_color)
        para = cell.paragraphs[0]
        run = para.add_run(h)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(9)
        if rtl:
            set_rtl(para)
            set_run_rtl(run)
        else:
            set_ltr(para)

    # data rows
    for ri, row_data in enumerate(rows):
        row = table.rows[ri + 1]
        bg = 'F2F2F2' if ri % 2 == 0 else 'FFFFFF'
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            cell.text = ''
            shade_cell(cell, bg)
            para = cell.paragraphs[0]
            run = para.add_run(str(val))
            run.font.size = Pt(9)
            if rtl:
                set_rtl(para)
                set_run_rtl(run)
            else:
                set_ltr(para)

    if rtl:
        set_table_rtl(table)
    return table

def page_break(doc):
    doc.add_page_break()

def horizontal_rule(doc, rtl=True):
    p = doc.add_paragraph('─' * 60)
    p.runs[0].font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    p.runs[0].font.size = Pt(7)
    if rtl:
        set_rtl(p)
    else:
        set_ltr(p)

# ── ARABIC RFP ────────────────────────────────────────────────────────────────

def build_arabic(path):
    doc = Document()
    set_doc_rtl(doc)

    # margins
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    # title block
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run('طلب تقديم العروض (RFP)\nنظام تخطيط موارد المؤسسة (ERP)\nالمالية وسلسلة التوريد الحكومية')
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)

    doc.add_paragraph()
    add_table(doc, ['البند', 'التفاصيل'], [
        ['جهة الطرح',       'الديوان العام لمحافظة ............'],
        ['رقم الوثيقة',     'RFP-ERP-2026-001'],
        ['تاريخ الإصدار',   'مايو 2026'],
        ['آخر موعد للتقديم','............/............/2026'],
    ], rtl=True)

    doc.add_paragraph()
    add_para(doc, 'ملاحظة: هذه الوثيقة سرية وموجهة للجهات المتأهلة فقط.', bold=True, rtl=True)
    horizontal_rule(doc)

    # ── القسم الأول
    add_heading(doc, 'القسم الأول: نظرة عامة ومعلومات المشروع', 1)
    add_heading(doc, '1.1 خلفية الجهة', 2)
    add_para(doc, 'الديوان العام لمحافظة ............ هو الجهاز التنفيذي للمحافظة المسؤول عن إدارة الشؤون المالية والإدارية وسلاسل التوريد والمشتريات الحكومية وفق اللوائح والقوانين المصرية المعمول بها، بما في ذلك تعليمات الجهاز المركزي للمحاسبات ولوائح وزارة المالية.', rtl=True)

    add_heading(doc, '1.2 الهدف من طلب العروض', 2)
    add_para(doc, 'يهدف هذا الطلب إلى الحصول على عروض فنية ومالية من شركات متخصصة لتوريد وتركيب وتخصيص وصيانة نظام متكامل لتخطيط موارد المؤسسة (ERP) مبني على منصة Odoo 17، يغطي الوظائف المالية وسلسلة التوريد والمشتريات الحكومية وإدارة المستودعات.', rtl=True)

    add_heading(doc, '1.3 نطاق المشروع', 2)
    add_table(doc, ['البند', 'القيمة'], [
        ['عدد المستخدمين', '40 مستخدماً'],
        ['المستخدمون المتزامنون', '20–25'],
        ['نموذج التشغيل', 'On-Premise (مفضل) / Cloud خاص'],
        ['اللغة الأساسية', 'العربية (RTL)'],
        ['موعد الإطلاق المستهدف', 'خلال 5 أشهر من توقيع العقد'],
    ], rtl=True)

    # ── القسم الثاني
    page_break(doc)
    add_heading(doc, 'القسم الثاني: المتطلبات الوظيفية', 1)

    add_heading(doc, '2.1 وحدة الحسابات العامة', 2)
    add_table(doc, ['#', 'المتطلب', 'الأولوية'], [
        ['1','دليل حسابات حكومي متعدد المستويات (4 مستويات)','إلزامي'],
        ['2','دفتر 55 ع.ح — نموذج وزارة المالية','إلزامي'],
        ['3','يومية 224 — سجل الصرف العام','إلزامي'],
        ['4','إقفال السنة المالية (1 يوليو — 30 يونيو)','إلزامي'],
        ['5','الأبعاد المالية (مراكز التكلفة)','إلزامي'],
        ['6','ترحيل دفعي للقيود (Batch Posting)','إلزامي'],
    ], rtl=True)

    add_heading(doc, '2.2 الدفاتر المساعدة الحكومية (29 دفتراً)', 2)
    add_table(doc, ['#', 'الدفتر', 'الأولوية'], [
        ['1','مفردات الحسابات الجارية المدينة (39 ع.ح)','إلزامي'],
        ['2','مفردات الحسابات الجارية الدائنة (39 ع.ح)','إلزامي'],
        ['3','إجمالي الحسابات الجارية المدينة (71 مكرر)','إلزامي'],
        ['4','إجمالي الحسابات الجارية الدائنة (71 ع.ح)','إلزامي'],
        ['5','مفردات الحسابات النظامية المدينة (39 مكرر)','إلزامي'],
        ['6','مفردات الحسابات النظامية الدائنة (39 مكرر)','إلزامي'],
        ['7','إجمالي الحسابات النظامية المدينة (78 مكرر)','إلزامي'],
        ['8','إجمالي الحسابات النظامية الدائنة (78 ع.ح)','إلزامي'],
        ['9','دفتر اليومية العامة (يومية 224)','إلزامي'],
        ['10','دفتر 55 ع.ح — اليومية المحاسبية','إلزامي'],
        ['11','دفتر الصندوق العام المدين','إلزامي'],
        ['12','دفتر الصندوق العام الدائن','إلزامي'],
        ['13','دفتر الإيرادات','إلزامي'],
        ['14','دفتر المصروفات','إلزامي'],
        ['15','دفتر الشيكات الواردة','إلزامي'],
        ['16','دفتر الشيكات الصادرة','إلزامي'],
        ['17','دفتر التأمينات والودائع','إلزامي'],
        ['18','دفتر السلف والعهد','إلزامي'],
        ['19','دفتر التحويلات الخزينية','إلزامي'],
        ['20','دفتر الالتزامات','إلزامي'],
        ['21','دفتر أوامر الصرف (استمارة 50)','إلزامي'],
        ['22','دفتر المستودع — الوارد','إلزامي'],
        ['23','دفتر المستودع — الصادر','إلزامي'],
        ['24','دفتر الأصول الثابتة','إلزامي'],
        ['25','دفتر الإهلاك السنوي','إلزامي'],
        ['26','دفتر الجزاءات والمخالفات','إلزامي'],
        ['27','دفتر العقوبات والاستقطاعات','إلزامي'],
        ['28','دفتر المزادات والممتلكات الحكومية','إلزامي'],
        ['29','دفتر المخصصات والاحتياطيات','إلزامي'],
        ['—','ترقيم تسلسلي قانوني لكل دفتر-سنة-فولية','إلزامي'],
        ['—','ترحيل شهري (نقل بعده / من قبله)','إلزامي'],
        ['—','توقيع موظف الشطب ورئيس الحسابات','إلزامي'],
    ], rtl=True)

    add_heading(doc, '2.3 وحدة الموازنة والالتزامات', 2)
    add_table(doc, ['#', 'المتطلب', 'الأولوية'], [
        ['1','إعداد الموازنة التفصيلية (باب/فصل/بند)','إلزامي'],
        ['2','تسجيل الالتزامات قبل الصرف','إلزامي'],
        ['3','مراقبة الاعتماد المالي في الوقت الفعلي','إلزامي'],
        ['4','تنبيهات تجاوز الموازنة','إلزامي'],
        ['5','تصنيف الموازنة (رأسمالية/جارية)','إلزامي'],
        ['6','نقل الاعتمادات بين البنود','مرغوب'],
    ], rtl=True)

    add_heading(doc, '2.4 وحدة أمر الصرف (استمارة 50 ع.ح)', 2)
    add_table(doc, ['#', 'المتطلب', 'الأولوية'], [
        ['1','إنشاء أمر صرف إلكتروني كامل','إلزامي'],
        ['2','طباعة استمارة 50 على الخلفية الرسمية المطبوعة مسبقاً','إلزامي'],
        ['3','تحديد مواضع الحقول بدقة على النموذج المادي','إلزامي'],
        ['4','جدول الفواتير المتعددة في الأمر الواحد','إلزامي'],
        ['5','حساب الاستقطاعات تلقائياً (ضريبة/دمغة)','إلزامي'],
        ['6','التفقيط بالعربية','إلزامي'],
        ['7','دورة الموافقة متعددة المستويات','إلزامي'],
        ['8','طباعة استمارة 69 و75','مرغوب'],
    ], rtl=True)

    add_heading(doc, '2.5 المشتريات الحكومية', 2)
    add_table(doc, ['#', 'المتطلب', 'الأولوية'], [
        ['1','طلبات الشراء ومصفوفة الموافقات','إلزامي'],
        ['2','لجنة المشتريات (تشكيل/محاضر/قرارات)','إلزامي'],
        ['3','جلسات العطاءات والترسية','إلزامي'],
        ['4','أوامر الشراء مرتبطة بالموازنة','إلزامي'],
        ['5','الفاتورة الإلكترونية ETA (B2B/B2G)','إلزامي'],
    ], rtl=True)

    add_heading(doc, '2.6 المستودعات والمخزون', 2)
    add_table(doc, ['#', 'المتطلب', 'الأولوية'], [
        ['1','إدارة مستودعات متعددة','إلزامي'],
        ['2','أذونات الإضافة والصرف والإرجاع والتحويل','إلزامي'],
        ['3','الجرد الدوري والسنوي','إلزامي'],
        ['4','إعادة تقييم المخزون','إلزامي'],
        ['5','ربط المخزون بالمحاسبة المالية','إلزامي'],
    ], rtl=True)

    add_heading(doc, '2.7 الأصول الثابتة', 2)
    add_table(doc, ['#', 'المتطلب', 'الأولوية'], [
        ['1','سجل الأصول الثابتة كامل','إلزامي'],
        ['2','الإهلاك التلقائي (خطي/متناقص)','إلزامي'],
        ['3','التخلص من الأصول','إلزامي'],
        ['4','ربط قيود الإهلاك بالموازنة','إلزامي'],
    ], rtl=True)

    add_heading(doc, '2.8 التقارير ولوحة القيادة التنفيذية', 2)
    add_table(doc, ['#', 'المتطلب', 'الأولوية'], [
        ['1','لوحة القيادة التنفيذية (KPIs) — الوقت الفعلي','إلزامي'],
        ['2','تقرير الأستاذ العام بالعربية','إلزامي'],
        ['3','تقرير شيخوخة الذمم (Aging)','إلزامي'],
        ['4','تقارير تنفيذ الموازنة','إلزامي'],
        ['5','تصدير XML للضرائب','إلزامي'],
        ['6','إدارة العهد والأمانات','إلزامي'],
    ], rtl=True)

    # ── القسم الثالث
    page_break(doc)
    add_heading(doc, 'القسم الثالث: المتطلبات التقنية', 1)

    add_heading(doc, '3.1 الخادم الرئيسي (Production)', 2)
    add_table(doc, ['المواصفة', 'الحد الأدنى'], [
        ['المعالج','Intel Xeon / AMD EPYC — 16 Core / 32 Thread'],
        ['الذاكرة العشوائية','64 GB DDR4 ECC'],
        ['تخزين النظام','2 × 480 GB SSD (RAID 1)'],
        ['تخزين البيانات','4 × 2 TB NVMe SSD (RAID 10)'],
        ['الشبكة','2 × 10 Gbps (Bonding)'],
        ['مزود الطاقة','Redundant PSU (2 × 800W)'],
        ['نظام التشغيل','Ubuntu Server 22.04 LTS'],
    ], rtl=True)

    add_heading(doc, '3.2 خادم الاحتياطي والاختبار', 2)
    add_table(doc, ['الخادم', 'المعالج', 'RAM', 'التخزين'], [
        ['Backup/DR','8 Core','32 GB','8 TB NAS RAID 6'],
        ['Staging/Test','8 Core','32 GB','1 TB SSD'],
    ], rtl=True)

    add_heading(doc, '3.3 البرمجيات المطلوبة', 2)
    add_table(doc, ['البرنامج', 'الإصدار'], [
        ['Odoo','17.0 (Community أو Enterprise)'],
        ['PostgreSQL','15 أو أحدث'],
        ['Python','3.10+'],
        ['Nginx','أحدث إصدار مستقر'],
        ['wkhtmltopdf','0.12.6'],
        ['Redis','7.x'],
    ], rtl=True)

    add_heading(doc, '3.4 محطات المستخدمين (40 محطة)', 2)
    add_table(doc, ['المواصفة', 'الحد الأدنى'], [
        ['المعالج','Intel Core i5 (الجيل الثامن+)'],
        ['الذاكرة','8 GB RAM'],
        ['التخزين','256 GB SSD'],
        ['الشاشة','21 بوصة — Full HD'],
        ['المتصفح','Chrome 120+ / Firefox 120+'],
        ['الطابعة','Laser A4'],
    ], rtl=True)

    # ── القسم الرابع
    page_break(doc)
    add_heading(doc, 'القسم الرابع: الأداء والأمن', 1)

    add_heading(doc, '4.1 معايير الأداء', 2)
    add_table(doc, ['المعيار', 'المتطلب'], [
        ['وقت استجابة الصفحة','أقل من 3 ثوانٍ'],
        ['التوافرية (Uptime)','≥ 99.5%'],
        ['المستخدمون المتزامنون','25 كحد أدنى'],
        ['RTO (وقت التعافي)','أقل من 4 ساعات'],
        ['RPO (نقطة الاسترداد)','أقل من 24 ساعة'],
    ], rtl=True)

    add_heading(doc, '4.2 الأمن والصلاحيات', 2)
    add_table(doc, ['المتطلب', 'التفاصيل'], [
        ['المصادقة','اسم مستخدم + كلمة مرور + 2FA اختياري'],
        ['نموذج الصلاحيات','RBAC — Role-Based Access Control'],
        ['سجل التدقيق','Audit Trail لكل عملية'],
        ['تشفير البيانات','AES-256 (تخزين) + TLS 1.3 (نقل)'],
        ['حماية الاختراق','WAF + IDS/IPS'],
    ], rtl=True)

    # ── القسم الخامس
    page_break(doc)
    add_heading(doc, 'القسم الخامس: التنفيذ والتدريب', 1)

    add_heading(doc, '5.1 مراحل التنفيذ', 2)
    add_table(doc, ['المرحلة', 'المدة', 'المخرجات'], [
        ['التركيب والإعداد','الأسابيع 1–4','الخوادم جاهزة، Odoo مثبت'],
        ['التخصيص والبرمجة','الأسابيع 5–10','كل الموديولات مبرمجة ومختبرة'],
        ['نقل البيانات وUAT','الأسابيع 11–14','البيانات محولة، اختبار القبول مكتمل'],
        ['التدريب','الأسابيع 15–16','جميع المستخدمين مدربون'],
        ['الإطلاق التجريبي','الأسبوع 17','تشغيل موازٍ'],
        ['الإطلاق الرسمي','الأسبوع 18','التحويل الكامل للإنتاج'],
    ], rtl=True)

    add_heading(doc, '5.2 متطلبات التدريب', 2)
    add_table(doc, ['الفئة', 'الساعات', 'الأسلوب'], [
        ['المستخدمون النهائيون (مالية)','16 ساعة/وحدة','حضوري + فيديو'],
        ['المستخدمون (مشتريات)','16 ساعة/وحدة','حضوري + فيديو'],
        ['المشرفون التقنيون','40 ساعة','حضوري'],
        ['مسؤولو النظام (IT)','24 ساعة','حضوري + تطبيق عملي'],
        ['الإدارة العليا','4 ساعات','عرض تقديمي'],
    ], rtl=True)

    # ── القسم السادس
    page_break(doc)
    add_heading(doc, 'القسم السادس: الدعم والصيانة', 1)

    add_heading(doc, '6.1 مستويات الخدمة (SLA)', 2)
    add_table(doc, ['الأولوية', 'التعريف', 'وقت الاستجابة', 'وقت الحل'], [
        ['P1 — حرجة','النظام متوقف كلياً','1 ساعة','4 ساعات'],
        ['P2 — عالية','وظيفة رئيسية متوقفة','4 ساعات','24 ساعة'],
        ['P3 — متوسطة','مشكلة جزئية','8 ساعات','72 ساعة'],
        ['P4 — منخفضة','استفسارات/تحسينات','24 ساعة','أسبوع'],
    ], rtl=True)

    add_heading(doc, '6.2 خدمات الصيانة (3 سنوات)', 2)
    for item in [
        'تحديثات الأمان الدورية وترقيات Odoo 17.x',
        'مراقبة الأداء والسعة',
        'نسخ احتياطي مُراقب مع اختبار ربع سنوي',
        'تقارير صحة النظام شهرية',
        'خط دعم هاتفي وإلكتروني خلال ساعات العمل',
        'زيارات ميدانية: حدٍّها الأدنى مرتان سنوياً',
    ]:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(item)
        run.font.size = Pt(10)
        set_rtl(p)
        set_run_rtl(run)

    # ── القسم السابع
    page_break(doc)
    add_heading(doc, 'القسم السابع: متطلبات العرض والتقييم', 1)

    add_heading(doc, '7.1 الوثائق المطلوبة', 2)
    add_table(doc, ['#', 'الوثيقة', 'الصيغة'], [
        ['1','العرض الفني التفصيلي','PDF'],
        ['2','خطة المشروع مع Gantt Chart','PDF / MS Project'],
        ['3','السيرة الذاتية للفريق والشهادات','PDF'],
        ['4','مرجعيات 3 مشاريع حكومية منجزة','PDF'],
        ['5','العرض المالي (مظروف مغلق منفصل)','PDF'],
        ['6','سجل تجاري وبطاقة ضريبية','PDF'],
        ['7','شهادة Odoo Partner (إن وجدت)','PDF'],
        ['8','خطاب ضمان بنكي','أصل'],
    ], rtl=True)

    add_heading(doc, '7.2 معايير التقييم', 2)
    add_table(doc, ['المعيار', 'الوزن'], [
        ['الملاءة الفنية للحل وشموليته','35%'],
        ['خبرة الفريق ومرجعيات المشاريع','25%'],
        ['خطة التنفيذ وجودة التدريب','15%'],
        ['خطة الدعم والالتزام بالـ SLA','15%'],
        ['التكلفة الإجمالية (5 سنوات)','10%'],
    ], rtl=True)

    # ── القسم الثامن
    page_break(doc)
    add_heading(doc, 'القسم الثامن: الجدول الزمني والتواصل', 1)

    add_heading(doc, '8.1 الجدول الزمني', 2)
    add_table(doc, ['الحدث', 'التاريخ'], [
        ['إصدار طلب العروض','............'],
        ['آخر موعد لأسئلة الموردين','............'],
        ['الرد على الأسئلة','............'],
        ['آخر موعد لتقديم العروض','............'],
        ['فتح المظاريف الفنية','............'],
        ['فتح المظاريف المالية','............'],
        ['الإعلان عن الفائز','............'],
        ['توقيع العقد','............'],
        ['بدء التنفيذ','............'],
    ], rtl=True)

    add_heading(doc, '8.2 معلومات التواصل', 2)
    add_table(doc, ['البند', 'التفاصيل'], [
        ['الجهة المختصة','إدارة تقنية المعلومات'],
        ['الجهة','الديوان العام لمحافظة ............'],
        ['العنوان','............................................'],
        ['هاتف','............................................'],
        ['بريد إلكتروني','............................................'],
        ['ساعات العمل','الأحد–الخميس، 09:00–15:00'],
    ], rtl=True)

    doc.add_paragraph()
    add_para(doc, 'الإصدار 1.0 — مايو 2026 | الديوان العام لمحافظة ............', rtl=True, size=9)

    doc.save(path)
    print(f'✓ Arabic RFP saved: {path}')


# ── ENGLISH RFP ───────────────────────────────────────────────────────────────

def build_english(path):
    doc = Document()

    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    def H(text, level=1):
        add_heading(doc, text, level, rtl=False)

    def P(text, bold=False):
        add_para(doc, text, bold=bold, rtl=False)

    def T(headers, rows, hcolor='1F497D'):
        add_table(doc, headers, rows, rtl=False, header_color=hcolor)

    # title
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run('REQUEST FOR PROPOSAL (RFP)\nEnterprise Resource Planning (ERP) System\nFinance & Supply Chain — Egyptian Government')
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)

    doc.add_paragraph()
    T(['Field', 'Details'], [
        ['Issuing Authority','General Diwan — ............ Governorate'],
        ['Document Reference','RFP-ERP-2026-001'],
        ['Issue Date','May 2026'],
        ['Submission Deadline','............/............/2026'],
    ])
    doc.add_paragraph()
    P('CONFIDENTIAL — For pre-qualified vendors only.', bold=True)
    horizontal_rule(doc, rtl=False)

    # Section 1
    H('SECTION 1 — INTRODUCTION', 1)
    H('1.1 Background', 2)
    P('The General Diwan of ............ Governorate is the executive body responsible for managing financial affairs, government procurement, supply chain, and treasury functions in compliance with Egyptian Ministry of Finance regulations and Central Auditing Organization (CAO) standards.')
    H('1.2 Purpose', 2)
    P('This RFP invites qualified vendors to submit technical and financial proposals for the supply, installation, customization, training, and support of a fully integrated ERP system based on Odoo 17, covering Government Financial Management, Procurement, Warehouse, and Executive Reporting.')
    H('1.3 Project Scale', 2)
    T(['Parameter', 'Value'], [
        ['Named Users','40 Users'],
        ['Concurrent Users','20–25 (estimated)'],
        ['Deployment Model','On-Premise (preferred) / Private Cloud'],
        ['Primary Language','Arabic (RTL)'],
        ['Go-Live Target','Within 5 months from contract signing'],
    ])

    # Section 2
    page_break(doc)
    H('SECTION 2 — FUNCTIONAL REQUIREMENTS', 1)

    H('2.1 Financial Management', 2)
    T(['Module', 'Description', 'Priority'], [
        ['General Ledger','Multi-level chart of accounts; Arabic journals; July–June fiscal year','Mandatory'],
        ['Daftar 55 (دفتر 55 ع.ح)','Government daily accounting register — MoF format','Mandatory'],
        ['Journal 224 (يومية 224)','Government payment journal — MoF format','Mandatory'],
        ['Subsidiary Books (29 books)','Forms 29/39/71/78 — legal sequential numbering, monthly carry-forward','Mandatory'],
        ['Budget Planning','Chapter/Section/Line-item budget; real-time commitment tracking','Mandatory'],
        ['Commitments','Pre-expenditure registration linked to budget','Mandatory'],
        ['Treasury & Cash Books','Multi-fund cash management; government cash book formats','Mandatory'],
        ['Cheque Management','Issue, receive, collect, bounce tracking','Mandatory'],
        ['Advances','Staff and vendor advances with settlement tracking','Mandatory'],
        ['Insurance & Deposits','Receipt/release/forfeiture linked to vendor contracts','Mandatory'],
        ['Penalties','Violation register and appeals workflow','Mandatory'],
        ['Custody Management','Government custody tracking','Mandatory'],
    ])

    H('2.2 Payment Order — Form 50 (استمارة 50 ع.ح)', 2)
    T(['Feature', 'Requirement', 'Priority'], [
        ['Electronic payment order creation','Full workflow','Mandatory'],
        ['Print Form 50 on pre-printed official background','Pixel-accurate overlay','Mandatory'],
        ['Multi-invoice table per payment order','Unlimited rows','Mandatory'],
        ['Auto-calculation of deductions (tax, stamps)','Formula-driven','Mandatory'],
        ['Net amount + Arabic text amount (تفقيط)','Arabic words','Mandatory'],
        ['Budget classification (Chapter/Section/Line)','Linked to budget','Mandatory'],
        ['Multi-level approval workflow','Configurable levels','Mandatory'],
        ['Form 69 & Form 75 printing','','Optional'],
    ])

    H('2.3 Government Procurement', 2)
    T(['Module', 'Description', 'Priority'], [
        ['Purchase Requisitions','Multi-level with approval matrix','Mandatory'],
        ['Procurement Committee','Formation, minutes, decisions','Mandatory'],
        ['Bidding & Tendering','Tender sessions, bid evaluation','Mandatory'],
        ['Adjudication','Award decisions, vendor notifications','Mandatory'],
        ['Purchase Orders','Linked to budget; receiving workflow','Mandatory'],
        ['ETA Electronic Invoice','B2B/B2G integration with Egyptian Tax Authority','Mandatory'],
    ])

    H('2.4 Warehouse & Inventory', 2)
    T(['Module', 'Description', 'Priority'], [
        ['Multi-Warehouse Management','Multiple stores/locations','Mandatory'],
        ['Addition / Issue / Return / Transfer Permits','Controlled movements','Mandatory'],
        ['Annual Stocktaking','Physical count with variance report','Mandatory'],
        ['Inventory Revaluation','FIFO/Average costing','Mandatory'],
        ['Stock-Finance Bridge','Auto journal entries for stock movements','Mandatory'],
    ])

    H('2.5 Fixed Assets', 2)
    T(['Feature', 'Requirement', 'Priority'], [
        ['Asset Register','Full record with government categories','Mandatory'],
        ['Depreciation','Automatic — Straight-Line / Declining Balance','Mandatory'],
        ['Asset Disposal','Write-off / sale workflows','Mandatory'],
        ['Budget Integration','Depreciation entries linked to budget','Mandatory'],
    ])

    H('2.6 Reporting & Executive Dashboard', 2)
    T(['Report', 'Description', 'Priority'], [
        ['Executive Dashboard','Real-time KPIs — Finance, Procurement, Inventory','Mandatory'],
        ['Budget Execution Report','Planned vs. actual by classification','Mandatory'],
        ['General Ledger Report','Full Arabic ledger per account','Mandatory'],
        ['Aging Report','Receivables & payables aging','Mandatory'],
        ['Tax XML Export','Export for Egyptian Tax Authority','Mandatory'],
        ['Auctions & Government Property','','Optional'],
    ])

    # Section 3
    page_break(doc)
    H('SECTION 3 — TECHNICAL REQUIREMENTS', 1)

    H('3.1 Production Server', 2)
    T(['Specification', 'Minimum Requirement'], [
        ['CPU','Intel Xeon / AMD EPYC — 16 Cores / 32 Threads'],
        ['RAM','64 GB DDR4 ECC'],
        ['OS Storage','2 × 480 GB SSD (RAID 1)'],
        ['Data Storage','4 × 2 TB NVMe SSD (RAID 10)'],
        ['Network','2 × 10 Gbps Ethernet (Bonding/LACP)'],
        ['Power Supply','Redundant PSU (2 × 800W)'],
        ['Operating System','Ubuntu Server 22.04 LTS'],
    ])

    H('3.2 Backup & Staging Servers', 2)
    T(['Server', 'CPU', 'RAM', 'Storage'], [
        ['Backup / DR','8 Cores','32 GB','8 TB NAS RAID 6'],
        ['Staging / Test','8 Cores','32 GB','1 TB SSD'],
    ])

    H('3.3 Network & Security Infrastructure', 2)
    T(['Component', 'Requirement'], [
        ['Firewall','Enterprise-grade (Fortinet / Palo Alto / pfSense)'],
        ['Load Balancer','HAProxy or Nginx'],
        ['SSL Certificate','Valid TLS (Let\'s Encrypt or CA-signed)'],
        ['VPN','Remote admin access (WireGuard / OpenVPN)'],
        ['Redundant ISP','Secondary 4G/Fiber failover'],
        ['WAF + IDS/IPS','Web Application Firewall + Intrusion Detection'],
    ])

    H('3.4 Software Stack', 2)
    T(['Component', 'Required Version'], [
        ['Odoo','17.0 (Community or Enterprise)'],
        ['PostgreSQL','15 or later'],
        ['Python','3.10+'],
        ['Nginx','Latest stable'],
        ['wkhtmltopdf','0.12.6 (PDF printing)'],
        ['Redis','7.x (session/cache)'],
    ])

    H('3.5 Client Workstations (40 Stations)', 2)
    T(['Specification', 'Minimum'], [
        ['CPU','Intel Core i5 (8th Gen+)'],
        ['RAM','8 GB'],
        ['Storage','256 GB SSD'],
        ['Display','21" Full HD'],
        ['Browser','Chrome 120+ / Firefox 120+ / Edge 120+'],
        ['Printer','Laser A4 (for government forms)'],
    ])

    H('3.6 UPS & Power', 2)
    T(['Component', 'Requirement'], [
        ['Server UPS','APC / Eaton — 10 KVA minimum'],
        ['Runtime','30 minutes under full load'],
        ['Generator','Required for large facilities (Bidder to confirm)'],
    ])

    # Section 4
    page_break(doc)
    H('SECTION 4 — NON-FUNCTIONAL REQUIREMENTS', 1)

    H('4.1 Performance & Availability', 2)
    T(['Metric', 'Requirement'], [
        ['Page response time','< 3 seconds (90th percentile)'],
        ['System availability (Uptime)','≥ 99.5%'],
        ['Simultaneous users','40 named / 25 concurrent'],
        ['Recovery Time Objective (RTO)','< 4 hours'],
        ['Recovery Point Objective (RPO)','< 24 hours'],
    ])

    H('4.2 Security & Access Control', 2)
    T(['Requirement', 'Detail'], [
        ['Authentication','Username + Password + optional 2FA'],
        ['Authorization','Role-Based Access Control (RBAC)'],
        ['Audit Trail','Full action log for every transaction'],
        ['Data Encryption','AES-256 at rest; TLS 1.3 in transit'],
        ['WAF + IDS/IPS','Mandatory'],
        ['Session Timeout','Auto-timeout after inactivity'],
    ])

    H('4.3 Backup Policy', 2)
    T(['Parameter', 'Requirement'], [
        ['Daily backup','Full DB + filestore + custom addons'],
        ['Weekly / Monthly','Full backup with offsite copy'],
        ['Retention','90 days (daily) / 12 months (monthly)'],
        ['Restore testing','Quarterly documented restore test'],
        ['Format','pg_dump -Fc (restorable via pg_restore)'],
    ])

    H('4.4 Arabic & Localization', 2)
    T(['Requirement', 'Detail'], [
        ['Text direction','Full RTL (Right-to-Left)'],
        ['Arabic fonts','Amiri / Cairo embedded in PDF reports'],
        ['Numeral support','Arabic-Indic (٠١٢٣٤٥٦٧٨٩) where required'],
        ['Government forms','Pixel-accurate match to MoF official forms'],
        ['Fiscal calendar','July 1 – June 30 (Egyptian government year)'],
    ])

    # Section 5
    page_break(doc)
    H('SECTION 5 — IMPLEMENTATION PLAN', 1)

    H('5.1 Project Phases', 2)
    T(['Phase', 'Duration', 'Deliverables'], [
        ['Infrastructure & Base Install','Weeks 1–4','Servers configured, Odoo installed'],
        ['Customization & Development','Weeks 5–10','All modules coded and tested'],
        ['Data Migration & UAT','Weeks 11–14','Data imported, UAT completed'],
        ['Training','Weeks 15–16','All 40 users trained'],
        ['Pilot Go-Live','Week 17','Parallel run with existing system'],
        ['Full Go-Live','Week 18','Production cutover'],
    ])

    H('5.2 Data Migration', 2)
    T(['Data Type', 'Source', 'Requirement'], [
        ['Chart of Accounts','Existing system / Excel','Full import'],
        ['Opening Balances','As of go-live date','All accounts'],
        ['Vendor / Supplier Master','Existing records','Complete'],
        ['Fixed Assets Register','Existing records','With accumulated depreciation'],
        ['Inventory Opening Stock','Physical count','Quantities + values'],
    ])

    H('5.3 Training Plan', 2)
    T(['Group', 'Hours', 'Format'], [
        ['Finance End Users','16 hrs/module','Classroom + recorded video'],
        ['Procurement End Users','16 hrs/module','Classroom + recorded video'],
        ['System Supervisors','40 hours','Classroom'],
        ['IT Administrators','24 hours','Classroom + hands-on'],
        ['Senior Management','4 hours','Executive presentation'],
    ])

    # Section 6
    page_break(doc)
    H('SECTION 6 — SUPPORT & MAINTENANCE', 1)

    H('6.1 Service Level Agreement (SLA)', 2)
    T(['Priority', 'Definition', 'Response', 'Resolution'], [
        ['P1 — Critical','System completely down','1 hour','4 hours'],
        ['P2 — High','Core function unavailable','4 hours','24 hours'],
        ['P3 — Medium','Partial functionality issue','8 hours','72 hours'],
        ['P4 — Low','Minor issue / enhancement','24 hours','1 week'],
    ])

    H('6.2 Maintenance Services (3-Year Contract)', 2)
    for item in [
        'Monthly security patches and Odoo 17.x updates',
        'Performance monitoring and capacity reporting',
        'Supervised automated backup with quarterly restore testing',
        'Monthly system health reports',
        'Phone + email support during official working hours',
        'Minimum 2 on-site visits per year',
    ]:
        p = doc.add_paragraph(style='List Bullet')
        run = p.add_run(item)
        run.font.size = Pt(10)
        set_ltr(p)

    # Section 7
    page_break(doc)
    H('SECTION 7 — PROPOSAL REQUIREMENTS', 1)

    H('7.1 Required Documents', 2)
    T(['#', 'Document', 'Format'], [
        ['1','Technical Proposal','PDF'],
        ['2','Project Plan with Gantt Chart','PDF / MS Project'],
        ['3','Team CVs and Certifications','PDF'],
        ['4','References: 3 government ERP projects','PDF'],
        ['5','Financial Proposal (sealed envelope)','PDF'],
        ['6','Company registration and tax card','PDF'],
        ['7','Odoo Partnership certificate (if applicable)','PDF'],
        ['8','Bank guarantee / bid bond','Original'],
    ])

    H('7.2 Pre-Qualification Criteria', 2)
    T(['Criterion', 'Minimum'], [
        ['Years of Odoo experience','3 years'],
        ['Completed government ERP projects','3 projects'],
        ['Technical staff','10 FTEs minimum'],
        ['Odoo Partner status','Preferred'],
        ['Valid commercial registration','Mandatory'],
        ['Valid tax registration','Mandatory'],
    ])

    H('7.3 Evaluation Criteria', 2)
    T(['Criterion', 'Weight'], [
        ['Technical solution adequacy & completeness','35%'],
        ['Team experience & project references','25%'],
        ['Implementation plan & training quality','15%'],
        ['Support plan & SLA commitment','15%'],
        ['Total cost of ownership (5 years)','10%'],
    ])

    # Section 8
    page_break(doc)
    H('SECTION 8 — FINANCIAL PROPOSAL STRUCTURE', 1)
    P('Vendors must provide a detailed cost breakdown (in Egyptian Pounds EGP, inclusive of all taxes):')
    T(['Item', 'Required'], [
        ['Odoo license (if Enterprise)','Per-user annual cost'],
        ['Implementation & customization','Fixed price per module'],
        ['Infrastructure (servers, network, UPS)','Itemized'],
        ['Data migration','Fixed price'],
        ['Training','Per session / total'],
        ['Year 1 support & maintenance','Annual'],
        ['Year 2 support & maintenance','Annual'],
        ['Year 3 support & maintenance','Annual'],
        ['TOTAL 3-YEAR COST OF OWNERSHIP','Summary line'],
    ])

    H('SECTION 9 — GENERAL TERMS', 1)
    T(['Term', 'Detail'], [
        ['IP & Data Ownership','All data and custom code owned by the Governorate Diwan'],
        ['Source code delivery','Full custom code delivered at project completion'],
        ['Delivery delay penalty','1% of contract value per week (max 10%)'],
        ['SLA breach penalty','Pro-rata deduction from monthly maintenance fee'],
        ['Warranty period','12 months from official go-live date'],
        ['Governing law','Laws of the Arab Republic of Egypt'],
    ])

    H('SECTION 10 — SUBMISSION & CONTACT', 1)
    T(['Field', 'Details'], [
        ['Department','Information Technology Department'],
        ['Organization','General Diwan — ............ Governorate'],
        ['Address','............................................'],
        ['Phone','............................................'],
        ['Email','............................................'],
        ['Working Hours','Sunday–Thursday, 09:00–15:00'],
    ])

    doc.add_paragraph()
    P('Document Version: 1.0 — May 2026 | General Diwan — ............ Governorate')

    doc.save(path)
    print(f'✓ English RFP saved: {path}')


# ── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    base = '/home/user/odoo_erp_modules_AR_default'
    build_arabic(f'{base}/RFP_ERP_SYSTEM_AR.docx')
    build_english(f'{base}/RFP_ERP_SYSTEM_EN.docx')
    print('Done.')
