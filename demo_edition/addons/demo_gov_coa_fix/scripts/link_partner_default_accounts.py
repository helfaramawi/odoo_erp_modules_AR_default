# -*- coding: utf-8 -*-
"""
ربط الحسابات الافتراضية للعملاء/الموردين (property_account_receivable_id /
property_account_payable_id) بحسابات من الشجرة الحكومية الجديدة — يُشغَّل
يدويًا عبر odoo shell.

الاختيار مبني على بحث في الشجرة المعتمدة نفسها، مش تخمين: بدل حساب
عام "أخرى"، لقيت مقابل دقيق لمفهوم "طرف خارجي غير حكومي" (بالظبط
المفهوم اللي بيمثّله عميل/مورد تجاري من منظور محاسبة حكومية):

  - العملاء (property_account_receivable_id):
    31130112 "مدينة تحت التسوية جهات غير حكومية" — حساب تفصيلي (leaf)
    تحت "الحسابات المدينة المتنوعة"، تحديدًا لمديونيات جهات غير حكومية.

  - الموردون (property_account_payable_id):
    41110831 "دائنة-جهات غير حكومية" — حساب تفصيلي (leaf) تحت
    "الحسابات الجارية الدائنة"، تحديدًا لمديونية الجهة لأطراف غير حكومية.

بيربط:
  1) الإعداد الافتراضي على مستوى الشركة كلها (ir.property، بيطبّق على
     أي شريك مالوش قيمة صريحة).
  2) أي شريك (عميل/مورد) عنده قيمة صريحة محفوظة بتشاور فعليًا على حساب
     "[قديم]" مؤرشف — بيتغيّر له بنفس الحساب الجديد.

طريقة التشغيل:
    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "/entrypoint.sh odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/link_partner_default_accounts.py
"""

RECEIVABLE_CODE = '31130112'  # مدينة تحت التسوية جهات غير حكومية
PAYABLE_CODE = '41110831'     # دائنة-جهات غير حكومية


def run(env):
    Account = env['account.account']
    Partner = env['res.partner']
    company = env.company

    receivable_account = Account.search(
        [('company_id', '=', company.id), ('code', '=', RECEIVABLE_CODE)], limit=1)
    payable_account = Account.search(
        [('company_id', '=', company.id), ('code', '=', PAYABLE_CODE)], limit=1)

    if not receivable_account or not payable_account:
        print('تعذّر إيجاد أحد الحسابين المرجعيين (%s / %s) — لم يتم أي تغيير.'
              % (RECEIVABLE_CODE, PAYABLE_CODE))
        return

    # 1) الإعداد الافتراضي على مستوى الشركة
    env['ir.property']._set_default(
        'property_account_receivable_id', 'res.partner',
        receivable_account, company=company)
    env['ir.property']._set_default(
        'property_account_payable_id', 'res.partner',
        payable_account, company=company)

    # 2) أي شريك عنده قيمة صريحة على حساب قديم مؤرشف
    old_receivable_partners = Partner.search([
        ('company_id', 'in', [company.id, False]),
        ('property_account_receivable_id.name', 'like', '[قديم] '),
    ])
    old_payable_partners = Partner.search([
        ('company_id', 'in', [company.id, False]),
        ('property_account_payable_id.name', 'like', '[قديم] '),
    ])

    for p in old_receivable_partners:
        p.property_account_receivable_id = receivable_account
    for p in old_payable_partners:
        p.property_account_payable_id = payable_account

    env.cr.commit()

    print('=' * 70)
    print('تم تعيين الحساب الافتراضي للعملاء (على مستوى الشركة): %s %s'
          % (receivable_account.code, receivable_account.name))
    print('تم تعيين الحساب الافتراضي للموردين (على مستوى الشركة): %s %s'
          % (payable_account.code, payable_account.name))
    print('-' * 70)
    print('شركاء اتحدّث لهم حساب العميل الصريح (%d):' % len(old_receivable_partners))
    for p in old_receivable_partners:
        print('  %s' % p.name)
    print('شركاء اتحدّث لهم حساب المورد الصريح (%d):' % len(old_payable_partners))
    for p in old_payable_partners:
        print('  %s' % p.name)
    print('=' * 70)


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
