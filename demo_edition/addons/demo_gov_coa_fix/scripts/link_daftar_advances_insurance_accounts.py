# -*- coding: utf-8 -*-
"""
ربط حسابات دفتر 55/224، السلف، والتأمينات بالشجرة الحكومية الجديدة —
يُشغَّل يدويًا عبر odoo shell.

بحث في الكود (زي ما طُلب) قبل أي تغيير، لكل موديول على حدة:

  - demo_gov_daftar55 (دفتر 55): مفيش أي حقل account.account في الموديول
    دي أصلاً — الترحيل المحاسبي الفعلي بيحصل عبر demo_gov_daftar224.

  - demo_gov_daftar224 (السجل اليومي المزدوج لدفتر 55): 3 حقول
    (account_debit_id / account_credit1_id / account_credit2_id) لكن
    create_dual_entry_from_daftar55() ما بيحطش فيها قيمة خالص — حقول
    مُدخَلة يدويًا لكل معاملة (تختلف حسب بند الموازنة)، مش إعداد شركة
    ثابت زي الدفاتر/الشركاء. السكريبت بيتأكد إنها فاضية زي المتوقع
    وبيرجّع أي حساب (لو حصل ووُجد) بيشاور على "[قديم]" فقط.

  - demo_gov_advances (السلف: استمارة 62 ع.ح): مفيش أي حقل account.account
    في advance.py ولا bank_guarantee.py — القيد المحاسبي (account_move_id)
    بيتسجل كمرجع بس، من غير حساب افتراضي مُعدّ مسبقًا. مفيش حاجة تُربط.

  - demo_gov_hr_payroll_insurance_eg (التأمينات الاجتماعية الرسمية):
    4 حقول على demo_gov.hr.payroll.insurance.bracket. الشجرة المعتمدة
    فيها تصنيف دقيق ورسمي لمزايا التأمينات (حصة الحكومة/حصة الموظف)،
    فاخترت:
      - حصة الموظف (مدين): 31130106 "ح / مدينة - تأمينات لدى الغير" —
        أصل، وضع مؤقت لحصة الموظف المحتجزة تمهيدًا لتوريدها.
      - حصة الموظف (دائن): 41110201 "ح / دائنة - تأمين ومعاشات" —
        التزام تجاه هيئة التأمينات.
      - حصة الجهة (مدين): 21120101 "التأمين ضد الشيخوخة والعجز والوفاة" —
        مصروف فعلي على موازنة الجهة (تحت "حصة الحكومة فى صندوق التأمين
        الاجتماعى للحكومة").
      - حصة الجهة (دائن): 41110203 "ح / دائنة - تأمينات اجتماعية/أعمال
        مقاولات" — التزام تجاه هيئة التأمينات عن حصة الجهة.

  - demo_gov_hr_takaful (صندوق التكافل) و demo_gov_insurance_subsidiary
    (تأمينات نقدية/خطابات ضمان): **مفيش تطابق رسمي في الشجرة المعتمدة**.
    الشجرة الحكومية منظَّمة بأبواب الموازنة العامة فقط، وصندوق التكافل
    (صندوق تكافل داخلي بمساهمات الموظفين، خارج الموازنة العامة تمامًا)
    وتأمينات الموردين النقدية (عُهد مؤقتة تحت تصرف الجهة، مش مصروف ولا
    إيراد حكومي) مفهومين إداريين داخليين، مش بنود موازنة. demo_gov_
    insurance_subsidiary نفسه موثّق فعلاً في data/accounting_config_data.xml
    إن الإعداد يدوي بالكامل (بعد ما كان السبب المذكور "يعتمد على دليل
    الحسابات المستخدم" — دلوقتي الدليل معروف ومعتمد، لكن المفهوم نفسه
    برضه مش له بند رسمي مطابق في الشجرة). السكريبت بيبلّغ بس عن حالتها
    الحالية (فاضية / بتشاور على "[قديم]") من غير ما يخمّن لها حساب.

طريقة التشغيل:
    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "/entrypoint.sh odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/link_daftar_advances_insurance_accounts.py
"""

INSURANCE_BRACKET_ACCOUNTS = {
    'employee_debit_account_id':  '31130106',  # ح / مدينة - تأمينات لدى الغير
    'employee_credit_account_id': '41110201',  # ح / دائنة - تأمين ومعاشات
    'employer_debit_account_id':  '21120101',  # التأمين ضد الشيخوخة والعجز والوفاة
    'employer_credit_account_id': '41110203',  # ح / دائنة - تأمينات اجتماعية/أعمال مقاولات
}

# لا يوجد لها تطابق رسمي في الشجرة المعتمدة — تُترك، وتُبلَّغ فقط إن كانت
# تشاور على حساب "[قديم]" مؤرشف.
NO_OFFICIAL_MATCH = {
    'demo_gov.hr.takaful.parameters': ['fund_account_id', 'income_account_id', 'expense_account_id'],
    'res.company': [
        'insurance_cash_asset_account_id', 'insurance_cash_liability_account_id',
        'guarantee_memo_dr_account_id', 'guarantee_memo_cr_account_id',
        'insurance_forfeiture_revenue_account_id',
    ],
}


def _is_deprecated(account):
    return bool(account) and account.name.startswith('[قديم] ')


def run(env):
    Account = env['account.account']
    company = env.company

    print('=' * 70)
    print('1) دفتر 224 (دفتر 55) — فحص الحقول الثلاثة على كل السجلات:')
    daftar224_recs = env['demo_gov.daftar224'].search([])
    stale_224 = daftar224_recs.filtered(
        lambda r: _is_deprecated(r.account_debit_id)
        or _is_deprecated(r.account_credit1_id)
        or _is_deprecated(r.account_credit2_id))
    print('   إجمالي سجلات دفتر 224: %d — سجلات بتشاور على حساب [قديم]: %d'
          % (len(daftar224_recs), len(stale_224)))
    if stale_224:
        for r in stale_224:
            print('   [%s] مدين=%s دائن1=%s دائن2=%s' % (
                r.display_name,
                r.account_debit_id.name if r.account_debit_id else '-',
                r.account_credit1_id.name if r.account_credit1_id else '-',
                r.account_credit2_id.name if r.account_credit2_id else '-'))
        print('   -> حقول لكل معاملة على حدة (بند موازنة مختلف كل مرة)، '
              'محتاجة تحديد يدوي لكل سجل، مش إعداد افتراضي واحد.')
    print('-' * 70)

    print('2) السلف (demo_gov.advance / demo_gov.bank.guarantee) — لا '
          'يوجد أي حقل account.account في الموديول، فلا يوجد ما يُربط.')
    print('-' * 70)

    print('3) التأمينات الاجتماعية الرسمية (demo_gov.hr.payroll.insurance.bracket):')
    accounts_by_code = {}
    missing = []
    for field_name, code in INSURANCE_BRACKET_ACCOUNTS.items():
        acc = Account.search([('company_id', '=', company.id), ('code', '=', code)], limit=1)
        if not acc:
            missing.append((field_name, code))
        accounts_by_code[field_name] = acc

    if missing:
        print('   تعذّر إيجاد الحسابات التالية — لم يتم أي تغيير على هذا الجزء:')
        for field_name, code in missing:
            print('     %s -> كود %s غير موجود' % (field_name, code))
    else:
        brackets = env['demo_gov.hr.payroll.insurance.bracket'].search([])
        updated = []
        for rec in brackets:
            vals = {}
            for field_name, acc in accounts_by_code.items():
                current = rec[field_name]
                if not current or _is_deprecated(current):
                    vals[field_name] = acc.id
            if vals:
                rec.write(vals)
                updated.append(rec.year)
        env.cr.commit()
        print('   تم تحديث %d إعداد سنوي (%s):' % (len(updated), ', '.join(updated) or '-'))
        for field_name, acc in accounts_by_code.items():
            print('     %s -> %s %s' % (field_name, acc.code, acc.name))
    print('-' * 70)

    print('4) بلا تطابق رسمي في الشجرة المعتمدة (تُترك، بلاغ فقط):')
    for model_name, field_names in NO_OFFICIAL_MATCH.items():
        if model_name == 'res.company':
            records = company
        else:
            records = env[model_name].search([])
        if not records:
            print('   [%s] لا توجد سجلات بعد.' % model_name)
            continue
        for rec in records:
            for field_name in field_names:
                val = rec[field_name]
                status = ('يشاور على حساب [قديم] — محتاج قرارك' if _is_deprecated(val)
                          else ('%s %s' % (val.code, val.name) if val else 'فاضي (بالتصميم)'))
                print('   [%s:%s] %s -> %s' % (model_name, rec.id, field_name, status))
    print('=' * 70)


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
