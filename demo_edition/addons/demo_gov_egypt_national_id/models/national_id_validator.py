# -*- coding: utf-8 -*-
"""
مكتبة تحقق مشتركة من صحة تركيب الرقم القومي المصري (14 رقماً)، حسب
التعريف الرسمي المعلن من مصلحة الأحوال المدنية:

  الخانة  1      : قرن الميلاد — 2 = مواليد 1900-1999، 3 = مواليد 2000-2099
  الخانتان 2-3   : سنة الميلاد (آخر رقمين)
  الخانتان 4-5   : شهر الميلاد (01-12)
  الخانتان 6-7   : يوم الميلاد (01-31، حسب الشهر والسنة الفعليين)
  الخانتان 8-9   : كود محافظة الميلاد (جدول رسمي، انظر GOVERNORATE_CODES)
  الخانات 10-13  : مسلسل الميلاد بنفس المحافظة في نفس اليوم — الخانة 13
                   (آخر رقم في هذا المسلسل) تحدد النوع: فردي = ذكر، زوجي = أنثى
  الخانة  14     : رقم تحقق (checksum) — لا يوجد نشر رسمي موثّق لصيغة
                   حسابه، فيُكتفى بالتأكد من وجوده كرقم واحد صحيح.

التحقق هنا تركيبي (structural): يتأكد إن الرقم منطقي شكلاً ومضمونًا
(تاريخ ميلاد حقيقي، كود محافظة معروف) — مش تحقق من وجوده فعليًا في
قاعدة بيانات مصلحة الأحوال المدنية (تكامل خارجي غير متاح في بيئة الديمو).
"""
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tools.translate import _

GOVERNORATE_CODES = {
    '01': 'القاهرة', '02': 'الإسكندرية', '03': 'بورسعيد', '04': 'السويس',
    '11': 'دمياط', '12': 'الدقهلية', '13': 'الشرقية', '14': 'القليوبية',
    '15': 'كفر الشيخ', '16': 'الغربية', '17': 'المنوفية', '18': 'البحيرة',
    '19': 'الإسماعيلية', '21': 'الجيزة', '22': 'بني سويف', '23': 'الفيوم',
    '24': 'المنيا', '25': 'أسيوط', '26': 'سوهاج', '27': 'قنا',
    '28': 'أسوان', '29': 'الأقصر', '31': 'البحر الأحمر', '32': 'الوادي الجديد',
    '33': 'مطروح', '34': 'شمال سيناء', '35': 'جنوب سيناء',
    '88': 'مواليد خارج جمهورية مصر العربية',
}

CENTURY_BY_DIGIT = {'2': 1900, '3': 2000}


def parse_egyptian_national_id(value, field_label=None):
    """يتحقق من رقم قومي مصري (14 رقماً) ويرجع dict بالبيانات المستخرجة
    {'birth_date', 'governorate_code', 'governorate_name', 'is_male'}
    لو الرقم سليم تركيبياً، أو يرفع ValidationError برسالة عربية دقيقة
    توضح أي جزء بالظبط غير صحيح."""
    label = field_label or 'الرقم القومي'
    digits = (value or '').strip()

    if not digits.isdigit() or len(digits) != 14:
        raise ValidationError(_(
            '%(label)s غير صحيح: "%(value)s".\n'
            'الرقم القومي المصري يجب أن يتكون من 14 رقماً بالضبط، أرقام فقط.'
        ) % {'label': label, 'value': value})

    century_digit = digits[0]
    if century_digit not in CENTURY_BY_DIGIT:
        raise ValidationError(_(
            '%(label)s غير صحيح: "%(value)s".\n'
            'الخانة الأولى (قرن الميلاد) يجب أن تكون 2 (مواليد 1900-1999) '
            'أو 3 (مواليد 2000-2099) — القيمة المُدخلة: %(digit)s.'
        ) % {'label': label, 'value': value, 'digit': century_digit})

    year = CENTURY_BY_DIGIT[century_digit] + int(digits[1:3])
    month = int(digits[3:5])
    day = int(digits[5:7])
    try:
        birth_date = date(year, month, day)
    except ValueError:
        raise ValidationError(_(
            '%(label)s غير صحيح: "%(value)s".\n'
            'تاريخ الميلاد المستخرج من الرقم (يوم %(day)s / شهر %(month)s / '
            'سنة %(year)s) غير موجود فعليًا في التقويم.'
        ) % {'label': label, 'value': value, 'day': digits[5:7],
             'month': digits[3:5], 'year': year})

    if birth_date > date.today():
        raise ValidationError(_(
            '%(label)s غير صحيح: "%(value)s".\n'
            'تاريخ الميلاد المستخرج من الرقم (%(bdate)s) في المستقبل.'
        ) % {'label': label, 'value': value, 'bdate': birth_date})

    gov_code = digits[7:9]
    if gov_code not in GOVERNORATE_CODES:
        raise ValidationError(_(
            '%(label)s غير صحيح: "%(value)s".\n'
            'كود المحافظة (الخانتان 8-9 = %(code)s) غير موجود في جدول '
            'أكواد المحافظات الرسمي.'
        ) % {'label': label, 'value': value, 'code': gov_code})

    is_male = int(digits[12]) % 2 == 1

    return {
        'birth_date': birth_date,
        'governorate_code': gov_code,
        'governorate_name': GOVERNORATE_CODES[gov_code],
        'is_male': is_male,
    }
