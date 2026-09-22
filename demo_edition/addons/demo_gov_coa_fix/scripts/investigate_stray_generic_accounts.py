# -*- coding: utf-8 -*-
"""
تشخيص الحسابات الغريبة اللي ظهرت في شجرة الحسابات بأكواد 6 خانات (زي
101000/101300/101401...) بدون بادئة "[قديم] " — مش جزء من الشجرة
الحكومية المعتمدة (8 خانات) ولا من الـ47 حساب الأصلي اللي اتوسم.

الاحتمال الأرجح: أودو بيُنشئ تلقائيًا شجرة حسابات عامة مصغّرة (Generic
Chart of Accounts) لما تفتح تطبيق المحاسبة/الفوترة لأول مرة على شركة
مفيهاش "قالب دليل حسابات" مُثبَّت رسميًا عبر المعالج (wizard) — واستبدال
الشجرة عندنا تم عن طريق account.account.create() مباشرة، مش عبر معالج
تثبيت القالب الرسمي، فأودو لسه شايف إن الشركة "من غير دليل حسابات
مُثبَّت" ويعرض/يُنشئ شجرة افتراضية بديلة عند أول استخدام.

السكريبت ده **للتشخيص فقط أولاً** — بيطبع:
  1) كل حساب كوده مش بادئ بـ"[قديم] " واسمه ومش من الشجرة الحكومية
     (أي حساب كوده مش موجود في ملف gov_chart_of_accounts_reference.csv)
  2) لكل واحد فيهم: هل عليه أي قيد محاسبي (account.move.line) — لو
     فاضي (مفيش قيود) يبقى آمن حذفه لاحقًا. لو عليه قيود، لازم نتعامل
     معاه بحذر (تسوية/نقل بدل حذف).
  3) حالة إعداد الشركة (chart_template / account_setup_bank_data_done...)
     اللي ممكن تفسّر السبب.

طريقة التشغيل:
    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "/entrypoint.sh odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/investigate_stray_generic_accounts.py
"""
import csv

REFERENCE_CSV = '/mnt/demo-addons/demo_gov_coa_fix/data/gov_chart_of_accounts_reference.csv'


def run(env):
    Account = env['account.account']
    company = env.company

    with open(REFERENCE_CSV, encoding='utf-8') as f:
        gov_codes = {row['code'].strip() for row in csv.DictReader(f)}

    all_accounts = Account.search([('company_id', '=', company.id)])
    stray = all_accounts.filtered(
        lambda a: not a.name.startswith('[قديم] ')
        and a.code not in gov_codes
        and a.code not in ('99000001', '99000002', '99000003'))  # حسابات صندوق التكافل المخصصة — مش غريبة

    print('=' * 70)
    print('إجمالي حسابات الشركة: %d' % len(all_accounts))
    print('حسابات غريبة (مش من الشجرة الحكومية ولا [قديم] ولا مخصصة معروفة): %d' % len(stray))
    print('-' * 70)

    if not stray:
        print('مفيش أي حساب غريب — القائمة اللي شفتيها في الصورة على الأغلب '
              'اختفت بالفعل أو كانت في نسخة سابقة.')
    else:
        for acc in stray:
            move_line_count = env['account.move.line'].search_count([('account_id', '=', acc.id)])
            posted_count = env['account.move.line'].search_count([
                ('account_id', '=', acc.id), ('parent_state', '=', 'posted')])
            safe = 'آمن حذفه (مفيش أي قيد عليه)' if move_line_count == 0 else \
                   'فيه %d قيد (%d منها مرحّل) — لا تُحذف، تحتاج نقل/تسوية أولاً' % (
                       move_line_count, posted_count)
            print('  [%s] %s (%s) — %s' % (acc.code, acc.name, acc.account_type, safe))

    print('-' * 70)
    print('حالة إعداد دليل الحسابات على الشركة:')
    for field_name in ('chart_template_id', 'account_setup_coa_state',
                        'account_setup_bank_data_state', 'account_setup_fy_data_state'):
        if field_name in company._fields:
            print('   %s = %r' % (field_name, company[field_name]))
        else:
            print('   %s -> غير موجود في هذا الإصدار' % field_name)
    print('=' * 70)


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
