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
بتتوسم (deprecated=True + بادئة "[قديم] " في الاسم) مش بتتمسح ولا بتتأرشف
فعليًا — account.account في هذا الإصدار من أودو معندوش حقل active أصلاً —
فالقيود المرحّلة عليها والحالة الحالية تفضل موجودة وسليمة بالكامل ومتاحة
للمراجعة والتقارير التاريخية. ملحوظة: الحسابات القديمة هتفضل تظهر في
قوائم الاختيار (deprecated مجرد علامة معلوماتية، مش فلترة تلقائية زي
active)، والبادئة في الاسم هي اللي هتفرّقها بصريًا عن الشجرة الجديدة.

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

    # 1) وسم الحسابات الحالية كـ "متروكة" — بدون حذف، حفاظاً على القيود
    # المرحّلة. account.account في هذا الإصدار من أودو معندوش حقل active
    # (اتأكد من كده بالتشغيل الفعلي)، فالحقل الصحيح لإخفاء/وسم حساب قديم
    # هو deprecated — نفس الحقل اللي تقارير demo_gov_gl_reports/demo_gov_reports
    # بتستخدمه فعلاً لتمييز الحسابات المتروكة. لاحظي إن deprecated مجرد
    # علامة معلوماتية ومش بيمنع ظهور الحساب في قوائم الاختيار زي ما كان
    # هيحصل مع active=False، فبنضيف كمان بادئة للاسم عشان يبقى واضح بصريًا.
    existing = Account.search([('company_id', '=', company.id)])
    archived_info = [(a.code, a.name) for a in existing]
    marking_failed = []
    for acc in existing:
        if acc.name.startswith('[قديم] '):
            continue
        vals = {'deprecated': True, 'name': '[قديم] ' + acc.name}
        # أودو مايسمحش بأكتر من حساب واحد من نوع equity_unaffected لكل
        # شركة — الحساب الحكومي الجديد المناسب للدور ده (نتيجة العام
        # الجاري) هياخد النوع ده بدل الحساب القديم.
        if acc.account_type == 'equity_unaffected':
            vals['account_type'] = 'equity'
        try:
            acc.write(vals)
        except Exception as exc:
            marking_failed.append((acc.code, acc.name, str(exc)))

    # 2) تحميل الشجرة الحكومية المعتمدة وبناء سجلات جديدة
    with open(REFERENCE_CSV, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    # تصحيح عيب بيانات في الملف المعتمد نفسه: 3 صفوف بس (من 1369) طالعين
    # بأسماء إنجليزية مبتورة الحرف الأول ومتعلّمين كلهم equity_unaffected —
    # أودو بيسمح بحساب واحد بس من النوع ده لكل شركة. نسيب الحساب اللي
    # معناه فعلاً "نتيجة العام الجاري" بالنوع الخاص، والباقي بيتحول
    # لحقوق ملكية عادية، مع تصحيح الاسم المبتور.
    NAME_FIXES = {
        '51000101': 'Surplus_Deficit',
        '52000101': 'Reserve for Encumbrances',
        '52000201': 'Miscellaneous Clearing Account',
    }
    DOWNGRADE_TO_EQUITY = {'52000101', '52000201'}

    codes_seen = set()
    to_create = []
    skipped_dupes = []
    for row in rows:
        code = row['code'].strip()
        if code in codes_seen:
            skipped_dupes.append(code)
            continue
        codes_seen.add(code)
        name = NAME_FIXES.get(code, row['name'].strip())
        account_type = row['account_type'].strip()
        if code in DOWNGRADE_TO_EQUITY:
            account_type = 'equity'
        to_create.append({
            'code': code,
            'name': name,
            'account_type': account_type,
            'company_id': company.id,
        })

    created = Account.create(to_create)
    env.cr.commit()

    print('=' * 70)
    print('تم وسم %d حساب قديم كمتروك (محفوظ بالكامل مع كل القيود المرحّلة):'
          % (len(archived_info) - len(marking_failed)))
    for code, name in archived_info:
        print('  [%s] %s' % (code, name))
    if marking_failed:
        print('-' * 70)
        print('تعذّر وسم %d حساب (السبب موضّح لكل واحد):' % len(marking_failed))
        for code, name, err in marking_failed:
            print('  [%s] %s — %s' % (code, name, err))
    print('-' * 70)
    print('تم إنشاء %d حساب من الشجرة الحكومية المعتمدة (8 خانات).' % len(created))
    print('-' * 70)
    print('تصحيح تلقائي لعيب بيانات في الملف المعتمد (أسماء مبتورة الحرف '
          'الأول + تعارض 3 حسابات equity_unaffected):')
    print('  51000101 Surplus_Deficit -> بقي equity_unaffected (نتيجة العام الجاري)')
    print('  52000101 Reserve for Encumbrances -> equity عادي')
    print('  52000201 Miscellaneous Clearing Account -> equity عادي')
    if skipped_dupes:
        print('-' * 70)
        print('تحذير — أكواد مكررة في الملف المرجعي اتجُوهل تكرارها: %s'
              % ', '.join(sorted(set(skipped_dupes))))
    print('=' * 70)
    print("""
تنبيه مهم — إجراء يدوي مطلوب منك:
الحسابات القديمة اتوسمت [قديم] ومتروكة (مش اتمسحت)، لكن أي إعداد كان
بيشاور عليها (الحساب الافتراضي لدفاتر اليومية، حسابات العملاء/الموردين
الافتراضية، أو أي حقل حساب داخل موديولاتنا المخصصة زي دفتر 55/السلف/
التأمينات) لسه بيشاور على الحساب القديم. راجعيها من الإعدادات واربطيها
بالحساب المناسب من الشجرة الجديدة قبل ما تسجّلي أي عملية جديدة — وبما
إن الحسابات القديمة هتفضل ظاهرة في قوائم الاختيار (اسمها بس هيتغيّر
لـ "[قديم] ...")، انتبهي متختاريش منها بالغلط بدل الحساب الجديد.
""")


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
