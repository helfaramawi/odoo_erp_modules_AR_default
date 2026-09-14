"""
تحويل التاريخ الميلادي إلى الهجري — نظام Kuwaiti/Algorithmic
"""
from datetime import date as _date


def gregorian_to_hijri(gdate):
    """Return (year, month, day) in Hijri given a Python date object."""
    if not gdate:
        return None, None, None
    d, m, y = gdate.day, gdate.month, gdate.year
    # Usamah Al-Rawi algorithm
    if m < 3:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    JD = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524
    # Hijri from JD
    L  = JD - 1948440 + 10632
    N  = int((L - 1) / 10631)
    L  = L - 10631 * N + 354
    J  = int((10985 - L) / 5316) * int(50 * L / 17719) + int(L / 5670) * int(43 * L / 15238)
    L  = L - int((30 - J) / 15) * int(17719 * J / 50) - int(J / 16) * int(15238 * J / 43) + 29
    Hm = int(24 * L / 709)
    Hd = L - int(709 * Hm / 24)
    Hy = 30 * N + J - 30
    return Hy, Hm, Hd


HIJRI_MONTHS_AR = [
    '', 'محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر',
    'جمادى الأولى', 'جمادى الآخرة', 'رجب', 'شعبان',
    'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة',
]


def hijri_display(gdate):
    """Return Arabic formatted Hijri date string, e.g. '15 رمضان 1446 هـ'"""
    if not gdate:
        return ''
    hy, hm, hd = gregorian_to_hijri(gdate)
    if hy is None:
        return ''
    month_name = HIJRI_MONTHS_AR[hm] if 1 <= hm <= 12 else ''
    return f'{hd} {month_name} {hy} هـ'
