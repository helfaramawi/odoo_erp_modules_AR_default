# -*- coding: utf-8 -*-
"""
ربط دفاتر اليومية (account.journal) بحسابات من الشجرة الحكومية الجديدة
بدل الحسابات القديمة المؤرشفة "[قديم] ..." — يُشغَّل يدويًا عبر odoo shell.

المرحلة دي بترتبط بحسابين بس فيهم مطابقة واضحة وغير خلافية في الشجرة
الحكومية المعتمدة:
  - دفاتر النقدية/البنوك (type in cash, bank): بتتربط بالحساب
    31110300 "النقدية" — أقرب حساب تفصيلي (leaf) لمفهوم النقدية
    بالخزينة/البنك في الشجرة المعتمدة.

دفاتر المبيعات والمشتريات (type sale/purchase) **مش بتتلمس** — تحديد
الحساب الافتراضي ليها قرار محاسبي/سياسة (تحت أي باب من أبواب الإيرادات
أو المصروفات الحكومية تُقيَّد عمليات البيع/الشراء الفعلية) مش حاجة
أقدر أخمّنها؛ السكريبت بيطبعها في تقرير منفصل "يحتاج قرارك" بدل ما
يغيّر فيها.

السكريبت بيطبع أولاً **كل** دفاتر اليومية الموجودة فعليًا (نوعها،
كودها، والحساب الافتراضي الحالي) قبل أي تعديل، عشان تشوفي الصورة
الكاملة، وبعدين يطبّق الربط على دفاتر النقدية/البنوك بس.

طريقة التشغيل:
    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "/entrypoint.sh odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/link_journal_accounts.py
"""

CASH_ACCOUNT_CODE = '31110300'  # النقدية — الأصول / الاصول المالية / لاصول النقدية / النقدية بالبنوك و الخزينة و البريد و الوحدةالحسابية / النقدية


def run(env):
    Journal = env['account.journal']
    Account = env['account.account']
    company = env.company

    journals = Journal.search([('company_id', '=', company.id)])

    print('=' * 70)
    print('كل دفاتر اليومية الحالية (%d):' % len(journals))
    for j in journals:
        acc = j.default_account_id
        print('  [%s] %s (%s) — الحساب الافتراضي الحالي: %s'
              % (j.code, j.name, j.type,
                 ('%s %s' % (acc.code, acc.name)) if acc else '(غير محدد)'))
    print('=' * 70)

    cash_account = Account.search([
        ('company_id', '=', company.id), ('code', '=', CASH_ACCOUNT_CODE)], limit=1)
    if not cash_account:
        print('تعذّر إيجاد حساب النقدية %s — لم يتم ربط أي دفتر.' % CASH_ACCOUNT_CODE)
        return

    linked = []
    skipped_no_field = []
    for j in journals.filtered(lambda x: x.type in ('cash', 'bank')):
        old = j.default_account_id
        try:
            j.write({'default_account_id': cash_account.id})
            linked.append((j.code, j.name, j.type,
                            old.code if old else '(غير محدد)', cash_account.code))
        except Exception as exc:
            skipped_no_field.append((j.code, j.name, str(exc)))

    needs_policy = journals.filtered(lambda x: x.type in ('sale', 'purchase'))

    env.cr.commit()

    print('تم ربط %d دفتر نقدية/بنك بحساب "النقدية" (%s):' % (len(linked), cash_account.code))
    for code, name, jtype, old_code, new_code in linked:
        print('  [%s] %s (%s): %s -> %s' % (code, name, jtype, old_code, new_code))
    if skipped_no_field:
        print('-' * 70)
        print('تعذّر ربط %d دفتر:' % len(skipped_no_field))
        for code, name, err in skipped_no_field:
            print('  [%s] %s — %s' % (code, name, err))
    print('=' * 70)

    if needs_policy:
        print('دفاتر تحتاج قرارك (المبيعات/المشتريات) — لم تُلمس:')
        for j in needs_policy:
            print('  [%s] %s (%s)' % (j.code, j.name, j.type))
        print("""
الشجرة الحكومية المعتمدة منظَّمة كأبواب إيرادات/مصروفات حكومية، مش
كحسابات "مبيعات منتج" أو "تكلفة بضاعة مباعة" تجارية — فمحتاجة تحددي
بنفسك تحت أي باب إيراد/مصروف فعلي هتُقيَّد عمليات المبيعات والمشتريات
عندك. قوليلي الأنشطة الفعلية (مثلاً: بيع خدمات، تحصيل رسوم، توريد
مستلزمات...) وهقترح لك الحساب المناسب من الشجرة.
""")


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
