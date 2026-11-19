# -*- coding: utf-8 -*-
"""
ربط دفتري المبيعات (INV) والمشتريات (BILL) بحسابات من الشجرة الحكومية
الجديدة — يُشغَّل يدويًا عبر odoo shell.

الاختيار مبني على الاستخدام الفعلي في كودنا، مش تخمين:

  - BILL (Vendor Bills / in_invoice): بحثت في demo_gov_uat_tools
    (سيناريوهات الاختبار الفعلية: توريد حاسب آلي، أعمال صيانة طريق،
    مستلزمات نظافة، توريد أثاث مكتبي — كلها مشتريات سلع/خدمات
    حكومية عامة)، وفي demo_gov_duplicate_claim_ai_agent (بيراقب
    in_invoice/in_refund لاكتشاف مطالبات موردين مكرَّرة) — يعني
    BILL فعليًا بيمثّل مدفوعات توريد/تعاقدات للموردين. الحساب
    المناسب: 21210806 "مستلزمات سلعية متنوعة" — الحساب التفصيلي
    الأعم تحت باب "شراء السلع والخدمات" (نفس الباب اللي غطّى كل
    سيناريوهات الاختبار الأربعة).

  - INV (Customer Invoices / out_invoice): مفيش أي استخدام فعلي
    لـ out_invoice في أي موديول مخصص عندنا (بحثت ولقيت صفر نتائج) —
    يعني مفيش نشاط "فواتير عملاء" حقيقي موثّق في الكود حاليًا. اخترت
    أعم حساب إيراد عام ممكن: 11320130 "أخـــرى" تحت "إيرادات الخدمات"
    — نفس نمط "الحساب العام/أخرى" المستخدم لباقي الدفاتر، ومتاح
    للمراجعة/التغيير بسهولة لو ظهر نشاط فعلي محدد لاحقًا.

كلاهما حسابات تفصيلية (leaf) قابلة للترحيل مباشرة، مش حسابات تجميعية.

طريقة التشغيل:
    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "/entrypoint.sh odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/link_sale_purchase_journals.py
"""

JOURNAL_TYPE_TO_ACCOUNT_CODE = {
    'sale': '11320130',      # أخـــرى — إيرادات الخدمات (عام، لحين تحديد نشاط فعلي)
    'purchase': '21210806',  # مستلزمات سلعية متنوعة — شراء السلع والخدمات
}


def run(env):
    Journal = env['account.journal']
    Account = env['account.account']
    company = env.company

    linked = []
    missing_account = []
    write_failed = []

    for jtype, code in JOURNAL_TYPE_TO_ACCOUNT_CODE.items():
        account = Account.search(
            [('company_id', '=', company.id), ('code', '=', code)], limit=1)
        if not account:
            missing_account.append((jtype, code))
            continue
        journals = Journal.search([('company_id', '=', company.id), ('type', '=', jtype)])
        for j in journals:
            old = j.default_account_id
            try:
                j.write({'default_account_id': account.id})
                linked.append((j.code, j.name, jtype,
                                old.code if old else '(غير محدد)', account.code, account.name))
            except Exception as exc:
                write_failed.append((j.code, j.name, str(exc)))

    env.cr.commit()

    print('=' * 70)
    print('تم ربط %d دفتر:' % len(linked))
    for jcode, jname, jtype, old_code, new_code, new_name in linked:
        print('  [%s] %s (%s): %s -> %s (%s)'
              % (jcode, jname, jtype, old_code, new_code, new_name))
    if missing_account:
        print('-' * 70)
        print('تعذّر إيجاد الحساب المرجعي لنوع الدفتر:')
        for jtype, code in missing_account:
            print('  %s -> كود %s غير موجود' % (jtype, code))
    if write_failed:
        print('-' * 70)
        print('تعذّر ربط بعض الدفاتر:')
        for jcode, jname, err in write_failed:
            print('  [%s] %s — %s' % (jcode, jname, err))
    print('=' * 70)
    print("""
ملحوظة: ربط دفتر INV بحساب "أخـــرى" العام اختيار مؤقت آمن لحد ما
يتحدد نشاط فعلي لفواتير العملاء عندكم — لو عرفنا بعد كده إن في نشاط
محدد (تحصيل رسوم معينة مثلاً)، سهل نغيّره لحساب أدق من نفس الشجرة.
""")


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
