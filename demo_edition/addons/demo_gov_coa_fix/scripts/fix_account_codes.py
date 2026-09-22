# -*- coding: utf-8 -*-
"""
تصحيح أكواد شجرة الحسابات من 6 خانات إلى الترقيم الحكومي الموحّد
الرسمي (8 خانات) — يُشغَّل مرة واحدة يدويًا عبر odoo shell.

آمن تمامًا على القيود المرحّلة والحالة الحالية: بيغيّر قيمة حقل code
بس على حسابات موجودة بالفعل (بالمطابقة بالاسم + نوع الحساب مع الملف
المرجعي المعتمد ../data/gov_chart_of_accounts_reference.csv) — من غير
ما يمسح أو يعيد إنشاء أي account.account، فالمعرّف الداخلي للحساب
(اللي بترتبط بيه قيود اليومية فعليًا، مش الكود) مايتغيّرش خالص.

أي حساب:
- اسمه مش موجود في الملف المرجعي، أو
- اسمه متكرر في الملف المرجعي بأكواد مختلفة (حالة غامضة تحتاج تحديد بشري)
مش بيتلمس خالص، وبيتسجَّل في تقرير "يحتاج مراجعة يدوية" آخر التشغيل
بدل ما يتخمَّن له كود.

طريقة التشغيل (بعد docker compose up -d --build عشان الملف يبقى
موجود جوه الكونتينر على /mnt/demo-addons):

    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/fix_account_codes.py
"""
import csv
import os

REFERENCE_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'gov_chart_of_accounts_reference.csv')


def _normalize(text):
    text = (text or '').strip()
    text = ' '.join(text.split())
    for hamza_alef in ('أ', 'إ', 'آ'):
        text = text.replace(hamza_alef, 'ا')
    text = text.replace('ى', 'ي')
    return text


def run(env):
    if not os.path.exists(REFERENCE_CSV):
        print('تعذّر إيجاد الملف المرجعي: %s' % REFERENCE_CSV)
        return

    by_key = {}
    ambiguous_keys = set()
    with open(REFERENCE_CSV, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            key = (_normalize(row['name']), row['account_type'])
            if key in by_key and by_key[key][0] != row['code']:
                ambiguous_keys.add(key)
            by_key[key] = (row['code'], row['full_path'])

    accounts = env['account.account'].search([])

    renamed = []
    already_correct = []
    unresolved = []

    for acc in accounts:
        key = (_normalize(acc.name), acc.account_type)
        if key in ambiguous_keys:
            unresolved.append((
                acc.code, acc.name, acc.account_type,
                'اسم متكرر في الملف المرجعي بأكثر من كود — يحتاج تحديد يدوي'))
            continue
        match = by_key.get(key)
        if not match:
            unresolved.append((
                acc.code, acc.name, acc.account_type,
                'لا يوجد تطابق باسم الحساب في الملف المرجعي'))
            continue
        correct_code, full_path = match
        if acc.code == correct_code:
            already_correct.append((acc.code, acc.name))
            continue
        old_code = acc.code
        try:
            acc.write({'code': correct_code})
            renamed.append((old_code, correct_code, acc.name, full_path))
        except Exception as exc:
            unresolved.append((
                acc.code, acc.name, acc.account_type,
                'فشل تغيير الكود: %s' % exc))

    env.cr.commit()

    print('=' * 70)
    print('تم تصحيح كود %d حساب:' % len(renamed))
    for old, new, name, path in renamed:
        print('  %s -> %s   %s   (%s)' % (old, new, name, path))
    print('-' * 70)
    print('أكواد صحيحة بالفعل: %d حساب' % len(already_correct))
    print('-' * 70)
    print('يحتاج مراجعة يدوية: %d حساب' % len(unresolved))
    for code, name, atype, reason in unresolved:
        print('  [%s] %s (%s) — %s' % (code, name, atype, reason))
    print('=' * 70)


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
