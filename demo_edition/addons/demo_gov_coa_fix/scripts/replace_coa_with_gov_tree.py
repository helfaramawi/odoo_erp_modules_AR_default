# -*- coding: utf-8 -*-
"""
استبدال كامل لشجرة الحسابات الإنجليزية العامة (الافتراضية من أودو) بالشجرة
الحكومية المعتمدة (1369 حساب، أكواد 8 خانات) — يُشغَّل مرة واحدة يدويًا
عبر odoo shell.

استُخدم هذا السكريبت بدل fix_account_codes.py لأن الحسابات الفعلية في
قاعدة بيانات الديمو طلعت "Bank / Cash / Account Receivable..." (شجرة
أودو الإنجليزية العامة الافتراضية) وليست شجرة حكومية بأسماء عربية بأكواد
6 خانات — فمفيش أي تطابق ممكن بالاسم، والحل الوحيد المنطقي هو الاستبدال
الكامل، مش إعادة الترقيم.

**الحفاظ على الوضع الحالي والقيود المرحّلة**: الحسابات القديمة الـ 47
بتتأرشف (active=False) مش بتتمسح، فالقيود المرحّلة عليها والحالة الحالية
تفضل موجودة وسليمة بالكامل ومتاحة للمراجعة والتقارير التاريخية.

**تنبيه بعد التشغيل — يحتاج إجراء يدوي منك:** الحسابات المؤرشفة كانت هي
المُعرَّفة كحسابات افتراضية لدفاتر اليومية (بنك/خزينة/مبيعات/مشتريات)
ولإعدادات العملاء/الموردين بالشركة ولبعض موديولاتنا المخصصة. الشجرة
الحكومية المعتمدة نفسها ما فيهاش حسابات من نوع asset_cash/asset_receivable/
liability_payable (الأنواع اللي أودو يحتاجها فنيًا لتسوية البنك وربط
الفواتير)، فلازم تختاري بنفسك بعد التشغيل الحسابات المناسبة من الشجرة
الجديدة وتربطيها يدويًا في:
  - Settings → Accounting → دفاتر اليومية (Journals) → الحساب الافتراضي
  - Settings → Accounting → حسابات العملاء/الموردين الافتراضية
  - أي موديول مخصص عنده حقل Many2one لحساب محدد (دفتر 55، السلف، التأمينات...)

طريقة التشغيل (بعد docker compose up -d --build عشان الملف يبقى موجود
جوه الكونتينر):

    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "/entrypoint.sh odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/replace_coa_with_gov_tree.py
"""
import csv

REFERENCE_CSV = '/mnt/demo-addons/demo_gov_coa_fix/data/gov_chart_of_accounts_reference.csv'


def run(env):
    Account = env['account.account']
    company = env.company

    # 1) أرشفة الحسابات الحالية — بدون حذف، حفاظاً على القيود المرحّلة
    existing = Account.search([('company_id', '=', company.id)])
    archived_info = [(a.code, a.name) for a in existing]
    if existing:
        existing.write({'active': False})

    # 2) تحميل الشجرة الحكومية المعتمدة وبناء سجلات جديدة
    with open(REFERENCE_CSV, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    codes_seen = set()
    to_create = []
    skipped_dupes = []
    for row in rows:
        code = row['code'].strip()
        if code in codes_seen:
            skipped_dupes.append(code)
            continue
        codes_seen.add(code)
        to_create.append({
            'code': code,
            'name': row['name'].strip(),
            'account_type': row['account_type'].strip(),
            'company_id': company.id,
        })

    created = Account.create(to_create)
    env.cr.commit()

    print('=' * 70)
    print('تم أرشفة %d حساب قديم (محفوظ بالكامل مع كل القيود المرحّلة):'
          % len(archived_info))
    for code, name in archived_info:
        print('  [%s] %s' % (code, name))
    print('-' * 70)
    print('تم إنشاء %d حساب من الشجرة الحكومية المعتمدة (8 خانات).' % len(created))
    if skipped_dupes:
        print('-' * 70)
        print('تحذير — أكواد مكررة في الملف المرجعي اتجُوهل تكرارها: %s'
              % ', '.join(sorted(set(skipped_dupes))))
    print('=' * 70)
    print("""
تنبيه مهم — إجراء يدوي مطلوب منك:
الحسابات القديمة اتأرشفت (مش اتمسحت)، لكن أي إعداد كان بيشاور عليها
(الحساب الافتراضي لدفاتر اليومية، حسابات العملاء/الموردين الافتراضية،
أو أي حقل حساب داخل موديولاتنا المخصصة زي دفتر 55/السلف/التأمينات)
لسه بيشاور على الحساب القديم المؤرشف. راجعيها من الإعدادات واربطيها
بالحساب المناسب من الشجرة الجديدة قبل ما تسجّلي أي عملية جديدة.
""")


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
