# -*- coding: utf-8 -*-
"""
تصحيح بادئات تصنيف الحسابات (demo_gov.subsidiary.account.classification)
بعد استبدال شجرة الحسابات — يُشغَّل يدويًا عبر odoo shell.

اكتُشفت هذه المشكلة بالتدقيق الاستباقي على باقي الموديولات بعد استبدال
شجرة الحسابات: حقل coa_code_prefix في demo_gov_subsidiary_books
(المستخدَم في "إسناد تلقائي بالبادئة" — account.account التي يبدأ كودها
بهذه البادئة تُسنَد تلقائياً لهذا التصنيف) كان لسه بالبادئات القديمة
(12/13/21) اللي كانت صحيحة على شجرة الحسابات الإنجليزية القديمة، لكن
نفس البادئات دلوقتي في الشجرة الحكومية المعتمدة (8 خانات) بتعني حاجة
مختلفة تمامًا — مثلاً بادئة "21" بقت تعني باب "المصروفات" بالكامل، مش
"ذمم دائنة/موردين". لو حد ضغط "إسناد تلقائي بالبادئة" من غير ما ننتبه،
كان هيُصنَّف حسابات مصروفات غلط كحسابات جارية دائنة.

تم تصحيح الملف المصدري data/account_classification_data.xml (للتثبيتات
الجديدة)، لكن noupdate="1" يمنع أي تحديث لاحق من التأثير على السجلات
المُنشأة بالفعل — فالسكريبت ده بيحدّث السجلات الموجودة فعليًا في قاعدة
البيانات الحالية، ثم يشغّل الإسناد التلقائي الصحيح على الشجرة الجديدة.

البادئات الصحيحة على الشجرة المعتمدة:
  CUR_DR   (حسابات جارية مدينة) : 3113 (الحسابات المدينة المتنوعة)
  CUR_CR   (حسابات جارية دائنة) : 4111 (الحسابات الجارية الدائنة)
  MEMO_DR  (حسابات نظامية مدينة): 91   (بدون تغيير — كانت صحيحة بالفعل)
  MEMO_CR  (حسابات نظامية دائنة): 92   (بدون تغيير — كانت صحيحة بالفعل)
  PERSONAL (حسابات شخصية)       : بلا بادئة — الشجرة المعتمدة مفيهاش
                                   باب منفصل بالكود للحسابات الشخصية
                                   بالاسم؛ تُسنَد يدويًا.

طريقة التشغيل:
    docker compose -f docker-compose.demo.yml exec -T odoo sh -c \
        "/entrypoint.sh odoo shell -d $DEMO_DB_NAME --no-http" \
        < ../addons/demo_gov_coa_fix/scripts/fix_subsidiary_classification_prefixes.py
"""

CORRECT_PREFIXES = {
    'CUR_DR':   '3113',
    'CUR_CR':   '4111',
    'MEMO_DR':  '91',
    'MEMO_CR':  '92',
    'PERSONAL': False,
}


def run(env):
    Classification = env['demo_gov.subsidiary.account.classification']

    print('=' * 70)
    print('تصحيح بادئات التصنيف:')
    updated = []
    for code, prefix in CORRECT_PREFIXES.items():
        rec = Classification.search([('code', '=', code)], limit=1)
        if not rec:
            print('   [%s] السجل غير موجود — تخطّي.' % code)
            continue
        old_prefix = rec.coa_code_prefix
        if old_prefix == prefix:
            print('   [%s] البادئة صحيحة بالفعل (%s) — بدون تغيير.' % (code, prefix or '-'))
            continue
        rec.write({'coa_code_prefix': prefix})
        updated.append((code, old_prefix, prefix))
        print('   [%s] %s -> %s' % (code, old_prefix or '-', prefix or '-'))
    env.cr.commit()
    print('-' * 70)

    print('تشغيل الإسناد التلقائي بالبادئة الصحيحة على الشجرة الجديدة:')
    assignable = Classification.search([('coa_code_prefix', '!=', False)])
    for rec in assignable:
        before = env['account.account'].search_count(
            [('x_subsidiary_classification_id', '=', rec.id)])
        rec.action_auto_assign_by_prefix()
        after = env['account.account'].search_count(
            [('x_subsidiary_classification_id', '=', rec.id)])
        print('   [%s] %s: %d -> %d حساب مُصنَّف' % (rec.code, rec.name, before, after))
    env.cr.commit()
    print('=' * 70)


run(env)  # noqa: F821  -- ``env`` is injected by ``odoo shell``
