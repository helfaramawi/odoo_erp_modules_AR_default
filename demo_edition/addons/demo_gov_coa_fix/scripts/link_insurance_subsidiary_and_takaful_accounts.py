# -*- coding: utf-8 -*-
"""
1) ربط حسابات تأمينات الموردين (demo_gov_insurance_subsidiary) بحسابات
   رسمية من الشجرة الحكومية المعتمدة — تطابق دقيق كان فايتنا في المراجعة
   الأولى (كنا شايفين إنه مفيش تطابق، لحد ما دقّقنا في قسم "الحسابات
   النظامية" وقسم "تأمينات للغير").

2) إنشاء 3 حسابات مخصصة (خارج الشجرة الرسمية، بأكواد بادئة 99 غير
   مستخدَمة إطلاقاً في الملف المرجعي المعتمد) لصندوق التكافل
   (demo_gov_hr_takaful) — صندوق داخلي بمساهمات الموظفين، خارج أبواب
   الموازنة العامة تمامًا، فمفيش له بند رسمي في الشجرة المعتمدة أصلاً
   (تأكدنا بالبحث في الملف كامل: لا "تكافل" ولا أي مرادف قريب).
   الحسابات دي واضح من كودها واسمها إنها مخصصة ("[مخصص]")، مش جزء من
   الشجرة المعتمدة، عشان متتلخبطش بيها في أي تقرير رسمي.

يُشغَّل يدويًا عبر odoo shell:
    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "/entrypoint.sh odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/link_insurance_subsidiary_and_takaful_accounts.py
"""

# ── 1) تأمينات الموردين — حسابات رسمية من الشجرة المعتمدة ──────────────────
INSURANCE_SUBSIDIARY_ACCOUNTS = {
    # مدين عند استلام تأمين نقدي من مورد — نفس حساب النقدية المستخدم لدفاتر
    # البنك/الخزينة، لأنه فعليًا نقدية حقيقية تدخل خزينة الجهة.
    'insurance_cash_asset_account_id': '31110300',      # النقدية
    # دائن — الالتزام برد التأمين للمورد (الفئة العامة/متنوعة، قابلة
    # للتخصيص لاحقًا حسب نوع التأمين: ابتدائي/نهائي/استثماري/ضمان أعمال).
    'insurance_cash_liability_account_id': '41110499',  # ح / دائنة - تأمينات للغير - متنوعة أخرى
    # حسابات نظامية (خارج الميزانية) لإثبات خطابات الضمان المستلمة —
    # الفئة "نهائية" كإعداد افتراضي عام (الأكثر شيوعًا لضمانات حسن التنفيذ).
    'guarantee_memo_dr_account_id': '91130501',          # ح/ كفالات عن تأمينات للغير نهائية
    'guarantee_memo_cr_account_id': '92130501',          # ح/ تأمينات عن كفالات نهائية
    # إيرادات مصادرة التأمين — تطابق حرفي دقيق.
    'insurance_forfeiture_revenue_account_id': '11330101',  # ايرادات النقد المصادر
}

# ── 2) صندوق التكافل — حسابات مخصصة جديدة (لا يوجد تطابق رسمي) ─────────────
TAKAFUL_CUSTOM_ACCOUNTS = [
    {
        'code': '99000001',
        'name': '[مخصص] رصيد صندوق التكافل',
        'account_type': 'liability_non_current',
        'field': 'fund_account_id',
    },
    {
        'code': '99000002',
        'name': '[مخصص] إيرادات اشتراكات صندوق التكافل',
        'account_type': 'income',
        'field': 'income_account_id',
    },
    {
        'code': '99000003',
        'name': '[مخصص] مصروفات صرف استحقاقات صندوق التكافل',
        'account_type': 'expense',
        'field': 'expense_account_id',
    },
]


def run(env):
    Account = env['account.account']
    company = env.company

    print('=' * 70)
    print('1) تأمينات الموردين (demo_gov_insurance_subsidiary) — ربط بحسابات رسمية:')
    missing = []
    resolved = {}
    for field_name, code in INSURANCE_SUBSIDIARY_ACCOUNTS.items():
        acc = Account.search([('company_id', '=', company.id), ('code', '=', code)], limit=1)
        if not acc:
            missing.append((field_name, code))
        else:
            resolved[field_name] = acc

    if missing:
        print('   تعذّر إيجاد الحسابات التالية — لم يتم أي تغيير على هذا الجزء:')
        for field_name, code in missing:
            print('     %s -> كود %s غير موجود' % (field_name, code))
    else:
        company.write({k: v.id for k, v in resolved.items()})
        env.cr.commit()
        for field_name, acc in resolved.items():
            print('   %s -> %s %s' % (field_name, acc.code, acc.name))
    print('-' * 70)

    print('2) صندوق التكافل (demo_gov_hr_takaful) — إنشاء حسابات مخصصة:')
    created = []
    already = []
    for spec in TAKAFUL_CUSTOM_ACCOUNTS:
        existing = Account.search(
            [('company_id', '=', company.id), ('code', '=', spec['code'])], limit=1)
        if existing:
            already.append(existing)
            continue
        acc = Account.create({
            'code': spec['code'],
            'name': spec['name'],
            'account_type': spec['account_type'],
            'company_id': company.id,
        })
        created.append((spec['field'], acc))
    env.cr.commit()

    if already:
        print('   موجودة بالفعل (لم تُعَد إنشاؤها):')
        for acc in already:
            print('     [%s] %s' % (acc.code, acc.name))

    if created:
        params = env['demo_gov.hr.takaful.parameters'].get_parameters()
        params.write({field_name: acc.id for field_name, acc in created})
        env.cr.commit()
        print('   تم إنشاء %d حساب مخصص وربطها بإعدادات صندوق التكافل:' % len(created))
        for field_name, acc in created:
            print('     %s -> [%s] %s' % (field_name, acc.code, acc.name))
    print('=' * 70)
    print("""
ملحوظة: حسابات صندوق التكافل (بادئة 99) مخصصة وخارج الشجرة الحكومية
المعتمدة عمدًا — ميظهروش في أي تقرير حكومي رسمي قائم على أبواب الموازنة،
وده متعمَّد لأن الصندوق نفسه خارج الموازنة العامة. لو حبيتي التقارير
الداخلية تفرزها بوضوح أكتر، ممكن نضيف علم/تصنيف مخصص لها لاحقًا.
""")


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
